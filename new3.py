# !pip install --upgrade yfinance

import pandas as pd
import yfinance as yf
import ta
import json
import requests
import bs4 as bs
from datetime import timedelta, date
import datetime
import time

def get_sp500_tickers():
	url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
	df = pd.read_html(url)[0]
	tickers = df['Symbol'].tolist()
	tickers = [t.replace('.', '-') for t in tickers]
	return tickers

def getAristocrats():
	resp = requests.get('https://en.wikipedia.org/wiki/S%26P_500_Dividend_Aristocrats')
	soup = bs.BeautifulSoup(resp.text, 'lxml')

	table = soup.find('table', {'class': 'wikitable sortable'})

	tickers = []

	for row in table.find_all('tr')[1:]:
		ticker = row.find_all('td')[1].text.rstrip()
		tickers.append(ticker)

	return tickers

def getData(ticker_list):
	data = yf.download(
		tickers = ticker_list,
		period = '6mo',
		interval = '1d',
		group_by = 'ticker',
		auto_adjust = False,
		prepost = False,
		threads = True
	)
	data = data.T
	return data

sp500 = get_sp500_tickers()

#sp500 = sp500[:200] # testing only
aristocrats = getAristocrats()

data = getData(sp500)
data = data.sort_index()

rsi_crossover = []
div = []

for ticker in sp500:
	# 找出 RSI Crossover 30 的股票
	try:
		df = data.loc[(ticker,),].T

		if df.empty or len(df) < 20:
			continue

		df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi().squeeze()
		df = df.dropna()
	
		if len(df) >= 2:
			if (df['RSI'].iloc[-2] < 30) and (df['RSI'].iloc[-1] >= 30):
				rsi_crossover.append(ticker)
	except Exception as e:
		print(f"{ticker} error: {e}")

	# 找出 dividend dates and yields
	try:
		ticker2 = yf.Ticker(ticker)
		df_2 = ticker2.history(period='1y')

		if ticker in aristocrats:
			aris = True
		else:
			aris = False

		info = ticker2.info

		div_pay_date = info.get('dividendDate','')  # 過去的付息日期
		
		if div_pay_date != '':  # 只處理有付息日期的股票
			div_pay_date = datetime.datetime.fromtimestamp(div_pay_date, datetime.UTC).strftime('%Y-%m-%d')
			yields = round(info['dividendYield'],2)

			exDividendDate = info.get('exDividendDate','') # 最近配息日期
			exDividendDate = datetime.datetime.fromtimestamp(exDividendDate, datetime.UTC).strftime('%Y-%m-%d')

			if exDividendDate > date.today().strftime("%Y-%m-%d") and yields > 4.0:
				div.append({
					'Ticker': ticker,
					'Div_Date': exDividendDate,
					'Yields': round(yields, 2), #str(round(yields, 2)) + '%',
					'Aris':str(aris)
				})

	except Exception as e:
		print(f"{ticker} error: {e}")

my_dict = {"RSI": rsi_crossover}

div = sorted(div, key=lambda d: d['Div_Date']) # sort list of dictionaries
my_dict["dividends"] = div


json_str = json.dumps(my_dict, ensure_ascii=False, indent=2)

#print(json_str)

url = "https://stock-web-real-cfcydzdxg3c0hnck.centralus-01.azurewebsites.net/core/api/stockdata/"

response = requests.post(
    url,
    data=json_str,  # 轉換成 JSON String
    headers={"Content-Type": "application/json"}
)
