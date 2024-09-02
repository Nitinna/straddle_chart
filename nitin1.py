import pandas as pd
import time
import sqlite3
import datetime
import os
import pickle
import xlwings as xw

def run_program():
    # Initialize Excel and connect to the workbook
    wb = xw.Book('FACTOR.xlsx')
    sht = wb.sheets['Sheet1']

    # CREATE DATABASE
    current_date = str(datetime.datetime.now().date())
    try:
        for item in os.listdir():
            path = os.path.join(item)
            if item.startswith('dataset_') and current_date not in item.split("_")[1]:
                if os.path.isfile(path):
                    os.remove(path)
        today_db_table = "dataset_" + current_date
        conn = sqlite3.connect(today_db_table + '.db')
    except Exception as e:
        print(e)
        return  # Stop and restart the program if an error occurs during setup

    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS DATA(TIMESTAMP_ TIMESTAMP, LTP REAL)''')

    def get_dataframe():
        time.sleep(1)

        # APPEND DATA INTO OHLC FORMAT 
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # call time

        # factor = make_straddle(namee,expiryy,gap)[-1]  # call factor

        factor = sht.range('I7').value

        cursor.execute("INSERT INTO DATA (TIMESTAMP_, LTP) VALUES (?, ?)", (timestamp, factor))
        conn.commit()
        cursor.execute('SELECT * FROM DATA')
        df = pd.DataFrame(data=cursor.fetchall())
        df[0] = pd.to_datetime(df[0])
        df.set_index(0, inplace=True)
        df.columns = ['LTP']  # Rename the column for clarity

        # Resample tick data into desired time periods (e.g., 1-minute candles)
        period = '1T'  # 1 minute
        resampled_df = df.resample(period).agg({'LTP': 'ohlc'})

        resampled_df.columns = ['open', 'high', 'low', 'close']
        resampled_df.reset_index(inplace=True)
        resampled_df['datetime'] = resampled_df[0]
        resampled_df = resampled_df[['datetime', 'open', 'high', 'low', 'close']]

        # Save the resampled data
        with open('iv_chart', 'wb') as file_name:
            pickle.dump(resampled_df, file_name)

    while True:
        try:
            get_dataframe()
            print(datetime.datetime.now().time())
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Restarting the program...")
            time.sleep(.5)  # Wait for 1 seconds before restarting
            break  # Break out of the loop to restart the program

while True:
    run_program()
