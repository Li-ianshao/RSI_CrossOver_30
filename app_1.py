
from flask import Flask, render_template, request, jsonify
import requests
import yfinance as yf
import pandas as pd
import time
import bs4 as bs
import json
import yahoo_fin.stock_info as si       # very good module
import math
from functions import *
import pickle
from operator import itemgetter

import sys

app = Flask(__name__)

# defining stocks contents
stocks_1 = ['AAPL', 'GOOGL', 'MSFT', 'AMZN']
stocks_2 =  ['XOM', 'O', 'VTRS', 'BEN']

aristocrats = getAristocrats()

SNP500 = get_sp500()

Other_stocks = ['SHEL', 'BP', 'EQNR', 'TTE', 'ET', 'FUTU']

stocks = SNP500 + Other_stocks
stocks = list(set(stocks))  # remove duplicates
stocks = list(map(lambda x: x.replace('.', '-'), stocks)) # e.g. BRK.B, BF.B，要改為 BRK-B, BF-B 才讀得到交易資料
stocks.sort()

print(f'Number of stocks:{len(stocks)}')

watch_list = {'AAPL':150.0, 'AMD': 70.0,'BEN':22.0, 'ENPH': 95.0, 'ET':11.0, 'FUTU': 30.0,'IBM':125.0,
    'KMI':16.0, 'MSFT':240.0, 'MMM':85.0, 'MO':38.0, 'VTRS':8.95, 'XOM':70.0}


# parameters
threshold = 30.0  # 過濾門檻值

@app.route('/')
def index():
    #start = time.time()
    stock_data = []

    print('site was hitted')

    for s in watch_list:
        print(s)
        ticker = yf.Ticker(s)
        df = ticker.history(period='3mo')
        Close = round(df.tail(1)['Close'][0],2)                                         # 最新收盤價/現價
        max_close = df['Close'].max()                                                   # 最近三個月內最高價
        min_close = df['Close'].min()                                                   # 最近三個月內最低價

        decreased = round((max_close - Close) / (max_close) * 100, 2) # 三個月內最大漲跌幅 %

        increased = - round((min_close - Close) / (min_close) * 100, 2) # 三個月內最大漲幅 %

        # get market price, volume and change
        Close = round(df.tail(1)['Close'][0],2)

        target = watch_list[s]

        target_ratio = round((Close - target) / Close * 100,2)

        Volume =  round(df.tail(1)['Volume'][0],2)
        Volume = f"{Volume:,d}"

        prev_close = round(df.tail(2)['Close'][0],2)                                    # 前一日收盤價
        change = round((Close - prev_close) / prev_close * 100,2)                       # 當日漲跌幅


        if s in aristocrats:
            category = 'AR'
        elif s in SNP500:
            category = "S&P"
        else:
            category = 'None'

        try:
            earningsQuarterlyGrowth = round(ticker.info['earningsQuarterlyGrowth'],2)
            earningsGrowth = round(ticker.info['earningsGrowth'],2)
        except Exception as e:
            earningsQuarterlyGrowth = 10000 # 故意設這麼大
            earningsGrowth = 10000 # 故意設這麼大

        
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
        # 可能沒有 dividend 相關資料
        '''
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


        t = {'Symbol': s, 'category': category, 'Close': Close, 'Target': target, 'Target_ratio': target_ratio, 'Decrease': change, '3mDecrease':decreased,
        'earningsQuarterlyGrowth':earningsQuarterlyGrowth, 'earningsGrowth':earningsGrowth, 'PERatio':trailingPE, 'EPS':trailingEps,
        'Volume': Volume, 'AVG_Volume':averageVolume, 'Div':dividendRate, 'Yields': dividendYield, 'Div_Date':divDate}
        '''
        t = {'Symbol': s, 'category': category, 'Close': Close, 'Target': target, 'Target_ratio': target_ratio, 'Decrease': change, '3mDecrease':decreased,
        'earningsQuarterlyGrowth':earningsQuarterlyGrowth, 'earningsGrowth':earningsGrowth, 'Volume': Volume, 'AVG_Volume':averageVolume, 'Div':dividendRate, 'Yields': dividendYield, 'Div_Date':divDate}

        stock_data.append(t)

    #end = time.time()

    #print(f'更新網頁耗時：{round(end - start,2)} 秒')

    #print(stock_data)

    return render_template('watch-list.html', data=stock_data)
    #return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)