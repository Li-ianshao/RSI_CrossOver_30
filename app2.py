from flask import Flask, render_template, request, jsonify
import requests
import yfinance as yf
import pandas as pd
import bs4 as bs
import json
import yahoo_fin.stock_info as si       # very good module
import math
from stock_functions import *
import pickle
from operator import itemgetter
import talib as ta
from talib import MA_Type
import sys
import warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)

# defining stocks contents
stocks_1 = ['AAPL', 'GOOGL', 'MSFT', 'AMZN']
stocks_2 =  ['XOM', 'O', 'VTRS', 'BEN']

aristocrats = getAristocrats()

SNP500 = get_sp500()

Other_stocks = ['SHEL', 'BP', 'EQNR','TTE', 'ET', 'FUTU']

stocks = SNP500 + Other_stocks
stocks = list(set(stocks))  # remove duplicates
stocks = list(map(lambda x: x.replace('.', '-'), stocks)) # e.g. BRK.B, BF.B，要改為 BRK-B, BF-B 才讀得到交易資料
stocks.sort()

print(f'Number of stocks:{len(stocks)}')

watch_list = {'AAPL':150.0, 'ABT':95.0, 'ALB': 110.0, 'AMD': 70.0,'BEN':22.0, 'CLX': 120.0, 'ENPH': 100.0, 'ET':11.0, 'FUTU': 38.0,'IBM':125.0, 
    'KMI':16.0, 'MSFT':240.0, 'MMM':85.0, 'MO':37.0, 'SHW':240.0, 'T':12.0, 'TSLA':120.0,'VTRS':8.95, 'XOM':70.0}


# parameters
threshold = 30.0  # 過濾門檻值

def getData(ticker_list):
    data = yf.download(
        tickers = ticker_list,
        period = '3mo',
        interval = '1d',
        group_by = 'ticker',
        auto_adjust = False,
        prepost = False,
        threads = True,
        proxy = None
    )

    data = data.T
    return data


@app.route('/')
def index():
    start = time.time()
    stock_data = []
    # print('OK')

    stocks = list(watch_list.keys())

    ticker_list = stocks

    data = getData(stocks)

    for s in ticker_list:
        #print(s)
        df = data.loc[(s,),].T

        ticker = yf.Ticker(s)
        #df = ticker.history(period='3mo')
        Close = round(df.tail(1)['Close'][0],2)                                         # 最新收盤價/現價
        max_close = df['Close'].max()                                                   # 最近三個月內最高價
        min_close = df['Close'].min()                                                   # 最近三個月內最低價

        # get market price, volume and change
        Close = round(df.tail(1)['Close'][0],2)

        target = watch_list[s]

        target_ratio = round((Close - target) / Close * 100,2)

        Volume =  round(df.tail(1)['Volume'][0],0)
        #Volume = Volume[:-2]
        Volume = f"{Volume:,}"

        prev_close = round(df.tail(2)['Close'][0],2)                                    # 前一日收盤價
        change = round((Close - prev_close) / prev_close * 100,2)                       # 當日漲跌幅


        if s in aristocrats:
            category = 'AR'
        elif s in SNP500:
            category = "S&P"
        else:
            category = 'None'

        industry = ticker.info['industry']

        try:
            earningsQuarterlyGrowth = round(ticker.info['earningsQuarterlyGrowth'],2)
            earningsGrowth = round(ticker.info['earningsGrowth'],2)
        except Exception as e:
            earningsQuarterlyGrowth = 10000 # 故意設這麼大
            earningsGrowth = 10000 # 故意設這麼大

        # 可能沒有 dividend 相關資料
        try:
            trailingPE = str(round(ticker.info['trailingPE'],2))
        except Exception as e:
            trailingPE = ''

        trailingEps = ticker.info['trailingEps']
        averageVolume =f"{ticker.info['averageVolume']:,d}"

        try:     
            dividendRate = ticker.info['dividendRate']      # dividend
            dividendYield = str(round(ticker.info['dividendYield'],4) * 100)[:4]    # yield
            exDividendDate = ticker.info['exDividendDate']  # ex-dividend date
            divDate = datetime.utcfromtimestamp(exDividendDate).strftime('%Y-%m-%d')
        except Exception as e:
            dividendRate = 0.0
            dividendYield = 0.0    # yield
            exDividendDate = ''
            divDate = ''

        # Technical indicators
        df['RSI'] = ta.RSI(df['Close'], timeperiod=14)
        RSI = round(df.tail(1)['RSI'][0],1)
            
        upper, middle, lower = ta.BBANDS(df['Close'], matype=MA_Type.T3)

        df['BBLower'] = lower
        df['BBUpper'] = upper
        df['BBMiddle'] = middle
        LBAND = round(df.tail(1)['BBLower'][0],2)
        UBAND = round(df.tail(1)['BBUpper'][0],2)
        MBAND = round(df.tail(1)['BBMiddle'][0],2)
        BBAND = str(UBAND) + '/' + str(MBAND) + '/' + str(LBAND)

        # MACD
        M = df['Close'].to_numpy()  # Convert dataframe column to array
        macd, signal, macdhist = ta.MACD(M, fastperiod=12, slowperiod=26, signalperiod=9)
        df['MACDHist'] = macdhist
        MACD = round(df.tail(1)['MACDHist'][0], 2)
       

        t = {'Symbol': s, 'category': category, 'Industry':industry, 'Close': Close, 'Target': target, 'Target_ratio': target_ratio, 'Decrease': change,
        'earningsQuarterlyGrowth':earningsQuarterlyGrowth, 'earningsGrowth':earningsGrowth, 'PERatio':trailingPE, 'EPS':trailingEps, 
        'Volume': Volume, 'AVG_Volume':averageVolume, 'Div':dividendRate, 'Yields': dividendYield, 'Div_Date':divDate, 
        'RSI': RSI, 'BBAND': BBAND, 'UBAND': UBAND, 'MBAND':MBAND, 'LBAND':LBAND, 'MACD': MACD}
        
        stock_data.append(t)

    end = time.time()

    print(f'更新網頁耗時：{round(end - start,2)} 秒')

    return render_template('watch-list.html', data=stock_data)


if __name__ == '__main__':
      app.run(host='0.0.0.0', port=8080)