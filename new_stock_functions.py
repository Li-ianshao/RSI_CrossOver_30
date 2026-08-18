import yfinance as yf
import pandas as pd
import math
from datetime import date
from datetime import datetime
import time

import json
import bs4 as bs
import requests
import talib as ta
from talib import MA_Type

def sp500_tickers():
	resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
	soup = bs.BeautifulSoup(resp.text, 'lxml')
	table = soup.find('table', {'class': 'wikitable sortable sticky-header'})
	tickers = []
	#print(table)


	for row in table.findAll('tr')[2:]:
		#print(row)
		ticker = row.findAll('td')[0].text
		tickers.append(ticker.rstrip())

	tickers = list(map(lambda x: x.replace('.', '-'), tickers)) # e.g. BRK.B, BF.B

	return tickers

def getAristocrats():
	resp = requests.get('https://en.wikipedia.org/wiki/S%26P_500_Dividend_Aristocrats')
	soup = bs.BeautifulSoup(resp.text, 'lxml')

	table = soup.find('table', {'class': 'wikitable sortable'})

	tickers = []

	for row in table.findAll('tr')[1:]:
		ticker = row.findAll('td')[1].text.rstrip()
		tickers.append(ticker)

	return tickers

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

def getEarnings(ticker):
	df = ticker.earnings_dates

	df = df.dropna()

	df['Surprise(%)'] = round(df['Surprise(%)'] * 100,1)

	estimates = str(df['EPS Estimate'][0]) + '/' + str(df['EPS Estimate'][1]) + '/' + str(df['EPS Estimate'][2]) + '/' + str(df['EPS Estimate'][3])
	actuals = str(df['Reported EPS'][0]) + '/' + str(df['Reported EPS'][1]) + '/' + str(df['Reported EPS'][2]) + '/' + str(df['Reported EPS'][3])
	surprises = str(df['Surprise(%)'][0]) + '/' + str(df['Surprise(%)'][1]) + '/' + str(df['Surprise(%)'][2]) + '/' + str(df['Surprise(%)'][3])

	return estimates, actuals, surprises

def getTickerInfo(stock, SNP500, aristocrats):
	ticker = yf.Ticker(stock)
	df = ticker.history(period="3mo")
	Close = round(df.tail(1)['Close'][0],2)                                         # 最新收盤價/現價
	max_close = df['Close'].max()                                                   # 最近三個月內最高價
	min_close = df['Close'].min()                                                   # 最近三個月內最低價

	decreased = round((max_close - Close) / (max_close) * 100, 2) # 三個月內最大跌幅 %
	increased = - round((min_close - Close) / (min_close) * 100, 2) # 三個月內最大漲幅 %

	if stock in aristocrats:
		category = 'AR'
	elif stock in SNP500:
		category = 'S&P'
	else:
		category = 'None'
	
	industry = ticker.info['industry']

	if not math.isnan(df.tail(2)['Close'][0]):
		prev_close = round(df.tail(2)['Close'][0],2)                                    # 前一日收盤價
		change = round((Close - prev_close) / prev_close * 100,2)                       # 當日漲跌幅
	else:
		print(stock)

	try:
		PERatio = round(ticker.info['trailingPE'],2)
	except Exception as e:
		PERatio = 0

	EPS = round(ticker.info['trailingEps'],2)

	volume = int(ticker.info['volume'])
	#volume = f"{volume:,d}"
			
	avg_Volume = int(ticker.info['averageVolume'])
	#avg_Volume = f"{avg_Volume:,d}"

	try:
		yld = round(ticker.info['dividendYield'] * 100,2)
	except Exception as e:
		yld = 0

	try:
		div = ticker.info['dividendRate']
	except Exception as e:
		div = 0

	try:
		div_date = ticker.info['exDividendDate']
		#div_date = datetime.datetime.fromtimestamp(div_date)
		div_date = datetime.utcfromtimestamp(div_date).strftime('%Y-%m-%d')

	except Exception as e:
		div_date = ''

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


	data = {'Ticker':stock, 'Category':category, 'Industry': industry, 'Price':Close, 'Decreased': decreased,
		'Change': change, 'PE': PERatio, 'EPS':EPS, 'Volume': volume, 'AVG_Vol': avg_Volume,
		'Yield':yld, 'Dividend':div, 'Div_Date': div_date, 'RSI': RSI, 'BBAND':BBAND, 'MACD': MACD}

	return data


def getOutputs(stocks, threshold, SNP500, aristocrats, threshold_day, targets):
	#headers_1 = ['代碼', 'industry', '收盤價', '漲跌幅%', '3mo跌幅', 'P/E', 'EPS_TTM', 'Vol./Avg. Vol.', 'Div&Yields', 'Ex. Div_date', 'Estimate', 'Actual', 'Surprise', 'RSI', 'UBBAND/Middle/LBBAND', 'MACDHist']
	#df_Outputs = pd.DataFrame(columns = headers_1)

	dec_stocks = pd.DataFrame(columns = ['Ticker', 'Category', 'Industry', 
		'Price', 'Change', 'Decreased', 
		'PE', 'EPS', 
		'Volume', 'AVG_Vol', 
		'Yield', 'Dividend', 'Div_Date',
		'RSI', 'BBAND', 'MACD'
		])

	dayDec_stocks = pd.DataFrame(columns = ['Ticker', 'Category', 'Industry', 
		'Price', 'Change', 'Decreased', 
		'PE', 'EPS', 
		'Volume', 'AVG_Vol', 
		'Yield', 'Dividend', 'Div_Date',
		'RSI', 'BBAND', 'MACD'
		])

	inc_stocks = pd.DataFrame(columns = ['Ticker', 'Category', 'Industry', 
		'Price', 'Change', 'Increased', 
		'PE', 'EPS', 
		'Volume', 'AVG_Vol', 
		'Yield', 'Dividend', 'Div_Date',
		'RSI', 'BBAND', 'MACD'
		])

	targets_reached = pd.DataFrame(columns = ['Ticker', 'Category', 'Industry', 
		'Price', 'Change', 'Decreased', 
		'PE', 'EPS', 
		'Volume', 'AVG_Vol', 
		'Yield', 'Dividend', 'Div_Date',
		'RSI', 'BBAND', 'MACD'
		])


	# filter those stocks satisfy conditions, e.g., accumulated decrease exceeds threshold

	data = getData(stocks)


	for s in stocks:
		targetReached = False
		df = data.loc[(s,),].T

		ticker = yf.Ticker(s)
		Close = round(df.tail(1)['Close'][0],2)                                         # 最新收盤價/現價
		max_close = df['Close'].max()                                                   # 最近三個月內最高價
		min_close = df['Close'].min()                                                   # 最近三個月內最低價

		# 如果 Close 小於 targets 則要顯示
		if s in targets and targets[s] >= Close:
			targetReached = True


		decreased = round((max_close - Close) / (max_close) * 100, 2) # 三個月內最大跌幅 %
		increased = - round((min_close - Close) / (min_close) * 100, 2) # 三個月內最大漲幅 %

		if not math.isnan(df.tail(2)['Close'][0]):                                          # 先計算出當日漲跌幅
			prev_close = round(df.tail(2)['Close'][0],2)                                    # 前一日收盤價
			change = round((Close - prev_close) / prev_close * 100,2)                       # 當日漲跌幅
		else:
			#print(s)
			change = 0.0

		if decreased >= threshold or increased > threshold or change*-1 >= threshold_day or targetReached:			
		# fetch more relevant financial data for stock s
			if s in aristocrats:
				category = 'AR'
			elif s in SNP500:
				category = 'S&P'
			else:
				category = 'None'
			
			industry = ticker.info['industry']

			df= df.dropna() 

			try:
				PERatio = round(ticker.info['trailingPE'],2)
			except Exception as e:
				PERatio = 0.0

			try:
				EPS = round(ticker.info['trailingEps'],2)
			except Exception as e:
				EPS = 0.0

			volume = int(ticker.info['volume'])
			#volume = f"{volume:,d}"
					
			avg_Volume = int(ticker.info['averageVolume'])
			#avg_Volume = f"{avg_Volume:,d}"

			try:
				yld = round(ticker.info['dividendYield'],2)
			except Exception as e:
				yld = 0

			try:
				div = ticker.info['dividendRate']
			except Exception as e:
				div = 0

			try:
				div_date = ticker.info['exDividendDate']
				#div_date = datetime.datetime.fromtimestamp(div_date)
				div_date = datetime.utcfromtimestamp(div_date).strftime('%Y-%m-%d')

			except Exception as e:
				div_date = ''

			# Earnings, estimates, actuals, surprises
			'''
			try:
				 estimates, actuals, surprises = getEarnings(ticker)
			except Exception as e:
				estimates = ''
				actuals = ''
				surprises = ''
			'''
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

			# WatchList 成員股低於買進目標價
			if targetReached:
				targets_reached.loc[len(targets_reached.index)] = [s, category, industry, Close, change, decreased, PERatio, EPS, volume, avg_Volume, yld, div, div_date, RSI, BBAND, MACD] 

			if(change*-1 >= threshold_day):							#因為有可能同時出現三個月內漲跌超過30%以及單日跌幅超過15%，所以要分開來做
				dayDec_stocks.loc[len(dayDec_stocks.index)] =  [s, category, industry, Close, change, decreased, PERatio, EPS, volume, avg_Volume, yld, div, div_date, RSI, BBAND, MACD]

			if (decreased >= threshold):
				dec_stocks.loc[len(dec_stocks.index)] = [s, category, industry, Close, change, decreased, PERatio, EPS, volume, avg_Volume, yld, div, div_date, RSI, BBAND, MACD] 
			#else:
			#	inc_stocks.loc[len(inc_stocks.index)] = [s, category, industry, Close, change, increased, PERatio, EPS, volume, avg_Volume, yld, div, div_date, estimates, actuals, surprises, RSI, BBAND, MACD] 

			if RSI <= 30:
				inc_stocks.loc[len(inc_stocks.index)] = [s, category, industry, Close, change, increased, PERatio, EPS, volume, avg_Volume, yld, div, div_date, RSI, BBAND, MACD] 
	dec_stocks = dec_stocks.sort_values(by='Decreased', ascending=False)
	inc_stocks = inc_stocks.sort_values(by='Increased', ascending=False)
	dayDec_stocks = dayDec_stocks.sort_values(by='Decreased', ascending=False)
	
	no_dec_stocks = len(dec_stocks)
	no_inc_stocks = len(inc_stocks)
	no_dayDec_stocks = len(dayDec_stocks)  # 

	dec_output = dec_stocks.to_dict('records')
	inc_output = inc_stocks.to_dict('records')
	dayDec_output = dayDec_stocks.to_dict('records') #

	targets_reached = targets_reached.to_dict('records')


	return no_dec_stocks, dec_output, no_inc_stocks, inc_output, no_dayDec_stocks, dayDec_output, targets_reached