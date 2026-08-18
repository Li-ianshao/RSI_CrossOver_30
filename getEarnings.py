import requests
import yfinance as yf
import pandas as pd
import bs4 as bs
import json

import math
from new_stock_functions import *
import talib as ta
from talib import MA_Type
import sys
import warnings
warnings.filterwarnings("ignore")

# All stocks considered
Other_stocks = ['CL', 'HAS', 'IP', 'AAP', 'GPS', 'LEG', 'WU', 'XRX', 'KSS', 'JWN', 'DOW', 'CVX', 'SHEL', 'XOM', 'ENPH', 'ENBP', 'BP', 'EQNR', 'ET', 'KMI', 'TTE', 'O', 'FUTU', 'MO', 'T', 'VTRS']

aristocrats = getAristocrats()
SNP500 = sp500_tickers()

stocks = SNP500 + Other_stocks
stocks = list(set(stocks))  # remove duplicates
stocks = list(map(lambda x: x.replace('.', '-'), stocks)) # e.g. BRK.B, BF.B，要改為 BRK-B, BF-B 才讀得到交易資料

# testing only
stocks = ['XOM', 'ENPH', 'FUTU', 'GL', 'CHTR']
stocks.sort()

#print(stocks)

# parameters 
threshold = 30.0  # 過濾門檻值

dec_stocks = pd.DataFrame(columns = ['Ticker', 'Category', 'Industry', 'Price', 'Decreased', 
	'PE', 'EPS', 
	'Volume', 'AVG_Vol', 
	'Yield', 'Dividend', 
	'Estimates', 'Actuals', 'Surprises',
	'RSI', 'BBAND', 'MACD'
	])

inc_stocks = pd.DataFrame()


# filter those stocks satisfy conditions, e.g., accumulated decrease exceeds threshold
data = getData(stocks)

for s in stocks:
	df = data.loc[(s,),].T

	ticker = yf.Ticker(s)
	Close = round(df.tail(1)['Close'][0],2)                                         # 最新收盤價/現價
	max_close = df['Close'].max()                                                   # 最近三個月內最高價
	min_close = df['Close'].min()                                                   # 最近三個月內最低價

	decreased = round((max_close - Close) / (max_close) * 100, 2) # 三個月內最大跌幅 %
	increased = - round((min_close - Close) / (min_close) * 100, 2) # 三個月內最大漲幅 %

	if decreased >= threshold:
		# fetch more relevant financial data for stock s
		if s in aristocrats:
			category = 'AR'
		elif s in SNP500:
			category = 'S&P'
		else:
			category = 'None'
		
		industry = ticker.info['industry']

		try:
			PERatio = round(ticker.info['trailingPE'],2)
		except Exception as e:
			PERatio = ''

		EPS = round(ticker.info['trailingEps'],2)

		if EPS < 0.0:
			EPS = '-$' + str(-EPS)
		else:
			EPS = '$' + str(EPS)

		volume = int(ticker.info['volume'])
		volume = f"{volume:,d}"
				
		avg_Volume = int(ticker.info['averageVolume'])
		avg_Volume = f"{avg_Volume:,d}"

		try:
			yld = str(ticker.info['dividendYield'] * 100) + '%'
		except Exception as e:
			yld = ''

		try:
			div = '$' + str(ticker.info['dividendRate'])
		except Exception as e:
			div = ''

		# Earnings, estimates, actuals, surprises
		try:
			 estimates, actuals, surprises = getEarnings(ticker)
		except Exception as e:
			estimates = ''
			actuals = ''
			surprises = ''

		# technical indicators
		# RSI
		df['RSI'] = ta.RSI(df['Close'], timeperiod=14)
		RSI = round(df.tail(1)['RSI'][0],1)

		# Bollinger Bands
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

		dec_stocks = dec_stocks.append({'Ticker' : s, 'Category': category, 'Industry' : industry, 
				'Price': '$' + str(Close), 'Decreased' : str(decreased) + '%',
				'PE':PERatio, 'EPS': EPS,
				'Volume': volume, 'AVG_Vol': avg_Volume,
				'Yield': yld, 'Dividend':div,
				'Estimates':estimates, 'Actuals': actuals, 'Surprises': surprises,
				'RSI':RSI, 'BBAND':BBAND, 'MACD': MACD
				}, ignore_index = True)


dec_stocks = dec_stocks.sort_values(by='Decreased', ascending=False)
print(dec_stocks[['Ticker','Decreased', 'Estimates','Actuals', 'Surprises']])

output = dec_stocks.T.to_dict().values()
print(output)

#print(dec_stocks)







