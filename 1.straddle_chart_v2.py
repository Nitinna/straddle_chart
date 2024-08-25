import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
import sqlite3
import datetime
import random
import time
import os
from threading import Thread
import matplotlib
from SmartApi import SmartConnect
import pyotp
import requests
import xlwings as xw
import sys
import pdb

# File paths
instruments_file = "instruments.csv"

def get_instruments():
    # Check if the instruments file already exists
    if not os.path.exists(instruments_file) or is_file_stale(instruments_file):
        try:
            url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
            data = requests.get(url=url, verify=False).json()
            df = pd.DataFrame(data)
            df.set_index("symbol", inplace=True)
            df.to_csv(instruments_file)
        except Exception as e:
            print(f"Error fetching or saving instruments data: {e}")
            return pd.DataFrame()  # Return an empty DataFrame on error
    else:
        # Load the existing instrument data
        try:
            df = pd.read_csv(instruments_file, index_col="symbol")
        except Exception as e:
            print(f"Error loading instruments data from file: {e}")
            return pd.DataFrame()  # Return an empty DataFrame on error
    return df

def is_file_stale(file_path):
    # Determine if the file is stale based on modification date
    last_mod_time = os.path.getmtime(file_path)
    last_mod_date = datetime.date.fromtimestamp(last_mod_time)
    return last_mod_date < datetime.date.today()

instrument_df = get_instruments()

# # login in angel
def angelbrok_login():
    try:
        global feed_token, client_code, angel, password

        angel = SmartConnect(api_key="F78V76K0")

        client_code = "N303894"
        password = "5004"
        token = 'ADVGBRQACAVTVMNFT4N357PJ3A'
        data = angel.generateSession(client_code, password, pyotp.TOTP(token).now())
        refreshToken = data['data']['refreshToken']
        feed_token = angel.getfeedToken()
        print("Login successful")
    except Exception as e:
        print(f"Error in login: {e}")

angelbrok_login()

def get_ltp(name, exchange):
    # time.sleep(1)
    try:
        # Fetch the symbol token from instrument_df based on the provided name
        symboltoken = instrument_df.loc[name]['token']
        # Fetch the Last Traded Price (LTP) data using the provided exchange, name, and symbol token
        ltp_data = angel.ltpData(exchange, name, symboltoken)
        # Extract and return the LTP value from the fetched data
        ltp = ltp_data['data']['ltp']
        return ltp
    except Exception as e:
        print(f"Error fetching LTP for {name} from {exchange}: {e}")
        return None

def get_straddle_ltp(name, expiry, gap, range_around_atm=5):
    try:
        ltp = get_ltp(name, "BSE")
        if ltp is None:
            return pd.DataFrame()  # Return an empty DataFrame if LTP is not available
        
        atm_strike = round(ltp / gap) * gap
        
        # Create lists to store the results
        strikes = []
        call_ltps = []
        put_ltps = []
        total_ltps = []  # List to store the sum of call and put LTPs
        
        # Fetch LTP for strikes above and below the ATM strike
        for offset in range(-range_around_atm * 100, (range_around_atm + 1) * 100 + 1, 100):
            try:
                strike = atm_strike + offset
                call_name = f"{name}{expiry}{strike}CE"
                put_name = f"{name}{expiry}{strike}PE"
                
                # Fetch LTP for call and put options
                call_ltp = get_ltp(call_name, 'BFO')
                put_ltp = get_ltp(put_name, 'BFO')
                
                # Calculate the total LTP
                total_ltp = call_ltp + put_ltp if call_ltp is not None and put_ltp is not None else None
                
                # Append results to lists
                strikes.append(strike)
                call_ltps.append(call_ltp)
                put_ltps.append(put_ltp)
                total_ltps.append(total_ltp)
            except Exception as e:
                print(f"Error fetching LTP for strike {atm_strike + offset}: {e}")
                continue
        
        # Create a DataFrame from the results
        df = pd.DataFrame({
            'Call LTP': call_ltps,
            'Strike': strikes,
            'Put LTP': put_ltps,
            'Total LTP': total_ltps  # New column for the sum of call and put LTPs
        })
        
        return df
    except Exception as e:
        print(f"Error generating straddle LTP data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

# Example usage:
# Assuming 'instrument_df' and 'angel' are properly defined

# Use a GUI backend
matplotlib.use('TkAgg')

# Create the database and table if not exist
current_date = str(datetime.datetime.now().date())
try:
    for item in os.listdir():
        path = os.path.join(item)
        if (item.startswith('dataset_')) and (current_date not in item.split("_")[1]):
            if os.path.isfile(path):
                os.remove(path)
    today_db_table = "dataset_" + current_date
    conn = sqlite3.connect(today_db_table + '.db', check_same_thread=False)
except Exception as e:
    print(f"Error creating database: {e}")

cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS DATA( TIMESTAMP_ TIMESTAMP, LTP REAL)''')

# Function to generate and insert data into the database
def generate_data():
    local_conn = sqlite3.connect(today_db_table + '.db', check_same_thread=False)
    local_cursor = local_conn.cursor()
    
    while True:
        try:
            time.sleep(1)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df_straddle = get_straddle_ltp("BANKEX", "24AUG", 100)
            
            # factor = df_straddle['Total LTP'].min()
            
            factor = random.randint(100, 110)
            local_cursor.execute("INSERT INTO DATA (TIMESTAMP_, LTP) VALUES (?, ?)", (timestamp, factor))
            local_conn.commit()
        except Exception as e:
            print(f"Error generating or inserting data: {e}")
            continue

# Start the data generation in a separate thread
data_thread = Thread(target=generate_data)
data_thread.daemon = True
data_thread.start()

# Create figure and axis for plotting
fig, ax = plt.subplots()
plt.xticks()
plt.style.use('seaborn-v0_8-darkgrid')

# Function to plot the candlestick chart with last price annotation
def plot_candlestick(resampled_df, ax, last_price=None):
    try:
        ax.clear()
        
        for index, row in resampled_df.iterrows():
            color = 'green' if row['close'] >= row['open'] else 'red'
            ax.plot([row['datetime'], row['datetime']], [row['low'], row['high']], color='black')
            ax.plot([row['datetime'], row['datetime']], [row['open'], row['close']], color=color, linewidth=6)
            
        if last_price is not None:
            last_time = resampled_df['datetime'].iloc[-1]
            ax.text(last_time, last_price, f'{last_price:.2f}', color='blue', fontsize=12, verticalalignment='bottom')

        ax.set_xlabel('Time')
        ax.set_ylabel('Price')
        ax.set_title('Live Candlestick Chart')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
    except Exception as e:
        print(f"Error plotting candlestick chart: {e}")

# Animation function that updates the plot
def animate(i):
    try:
        # Fetch the latest data from the database
        cursor.execute('SELECT * FROM DATA')
        df = pd.DataFrame(data=cursor.fetchall())
        df[0] = pd.to_datetime(df[0], errors='coerce')
        df.dropna(subset=[0], inplace=True)
        df.set_index(0, inplace=True)
        df.columns = ['LTP']

        # Resample tick data into desired time periods (e.g., 1-minute candles)
        period = '1T'
        resampled_df = df.resample(period).agg({'LTP': 'ohlc'})
        resampled_df.columns = ['open', 'high', 'low', 'close']
        resampled_df.reset_index(inplace=True)
        resampled_df['datetime'] = resampled_df.index
        resampled_df = resampled_df[['datetime', 'open', 'high', 'low', 'close']]

        # Get the last price for annotation
        last_price = resampled_df['close'].iloc[-1] if not resampled_df.empty else None

        # Update the plot with the new candlestick data and last price
        plot_candlestick(resampled_df, ax, last_price=last_price)
    except Exception as e:
        print(f"Error in animation function: {e}")

# Create the animation once and keep updating the existing plot
ani = animation.FuncAnimation(fig, animate, interval=1000, cache_frame_data=False)

# Show the plot
plt.show()
