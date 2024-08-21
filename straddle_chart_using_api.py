import pdb
import pandas as pd
import xlwings as xw
import time
import sqlite3
import datetime
import sys
import os
import pdb
from SmartApi import SmartConnect #or from SmartApi.smartConnect import SmartConnect
import pyotp
import requests
import random

# def get_instruments():
#     global instrument_df
#     url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
#     request = requests.get(url=url, verify=False)
#     data = request.json()
#     instrument_df = pd.DataFrame(data)
#     instrument_df.to_csv("instruments.csv")
#     instrument_df.set_index("symbol", inplace=True)
#     return instrument_df

# instrument_df = get_instruments()

# # login in angel
# def angelbrok_login():
#     try:
#         global feed_token, client_code, angel, password

#         angel = SmartConnect(api_key="F78V76K0")

#         client_code = "N303894"
#         password = "5004"
#         token = 'ADVGBRQACAVTVMNFT4N357PJ3A'
#         # totp = input(f"Enter TOTP for {client_code}: ")
#         # print(f"TOTP received : {totp}")
#         data = angel.generateSession(client_code, password, pyotp.TOTP(token).now())
#         refreshToken = data['data']['refreshToken']
#         feed_token = angel.getfeedToken()
#         print("Login successful")
#     except Exception as e:
#         print("Error in login", e)


# angelbrok_login()


# def get_ltp(name, exchange):
#     symboltoken = instrument_df.loc[name]['token']
#     ltp_data = angel.ltpData(exchange, name, symboltoken)
#     ltp = ltp_data['data']['ltp']
#     return ltp


# def make_straddle(name, exipry, gap):
#     ltp = get_ltp(name, "NSE")
#     atm_strike = round(ltp/gap)*gap
#     call_name = name + exipry + str(atm_strike) + 'CE'
#     put_name = name + exipry + str(atm_strike) + 'PE'
#     call_ltp = get_ltp(call_name,'NFO')
#     put_ltp = get_ltp(put_name,'NFO')
    
#     avg_price = atm_strike + (call_ltp - put_ltp)
#     avg_price_round = round(avg_price,-2)
#     call_name2 = name + exipry + str(atm_strike) + 'CE'
#     put_name2 = name + exipry + str(atm_strike) + 'PE'
#     call_ltp2 = get_ltp(call_name,'NFO')
#     put_ltp2 = get_ltp(put_name,'NFO')
#     factor_price = call_ltp2 + put_ltp2

#     return [avg_price,factor_price]

# IV CHART SHEET OBJECT 

wb1 = xw.Book("iv_chart.xlsm")
chart_sheet = wb1.sheets['Sheet1']

chart_sheet.range("A1:F500").value = "" # erase old data from excel

wb2 = xw.Book("FACTOR.xlsx")
factor_sheet = wb2.sheets['Sheet1']

# CREATE DATABASE 
current_date = str(datetime.datetime.now().date())
try:
    for item in os.listdir():
        path = os.path.join(item)
        if (item.startswith('dataset_')) and (current_date not in item.split("_")[1]):
            if os.path.isfile(path):
                os.remove(path)
    today_db_table =  "dataset_" + current_date
    conn = sqlite3.connect(today_db_table + '.db')
except Exception as e:
    print(e)
    # pdb.set_trace()

cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS DATA( TIMESTAMP_  TIMESTAMP, LTP REAL)''')
data = []

# namee = input('index_name :  ' )
# expiryy = input('expiry : ')
# gap = int(input('gap : '))


while True:
    time.sleep(1)

    # APPEND DATA INTO OHLC FORMAT 
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")# call time

    # factor = make_straddle(namee,expiryy,gap)[-1]  # call factor
    factor = factor_sheet.range('I7').value
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
    resampled_df = resampled_df[['datetime','open','high','low','close']]

    # pdb.set_trace()
    time_slot = float(resampled_df.iloc[0]['datetime'].strftime('%H.%M'))
    # pdb.set_trace()
    # SEND DATA INTO ANOTHER EXCEL SHEET WHERE WE WILL PLOT CHART
    chart_sheet.range('G3').value = time_slot
    chart_sheet.range('A2').value = resampled_df[-120:] # dump data into excel

    print(datetime.datetime.now().time())


