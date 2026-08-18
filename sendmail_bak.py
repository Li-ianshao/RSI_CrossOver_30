# 如果執行發生錯誤，很可能是 yfinance 改版，執行下列程式 upgrate
# pip install yfinance --upgrade --no-cache-dir

# 最近配息的股票以及 RSI < 25 的股票
import yfinance as yf
import pandas as pd
import numpy as np
import math
#import talib as ta
#from talib import MA_Type
import finnhub

# Setup client
finnhub_client = finnhub.Client(api_key="d0noj91r01qn5ghl2c3gd0noj91r01qn5ghl2c40")


import json
import bs4 as bs
import requests

from datetime import timedelta, date
from datetime import datetime
from tabulate import tabulate
import email, smtplib, ssl
from os.path import exists
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


import warnings
warnings.filterwarnings("ignore")

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

def sendMail(subject, msg_text, recp):
    me = "scshaoifd@email.com"
    you = "scshao@berkeley.edu"

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject  #郵件標題
    msg['From'] = me
    msg['To'] = you

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(msg_text, 'plain', 'utf-8')
    part2 = MIMEText(msg_text, 'html', 'utf-8')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)
    text = msg.as_string()

    # Send the message via local SMTP server.
    mail = smtplib.SMTP('smtp.gmail.com', 587)
    mail.ehlo()
    mail.starttls()

    mail.login('scshaoifd@gmail.com', 'cfcq dnpq hfox awfv')
    
    mail.sendmail(me, recp, text)
    mail.quit()

def getRSI(data, window=14, adjust=False):
    delta = data['Close'].diff(1).dropna()
    loss = delta.copy()
    gains = delta.copy()

    gains[gains < 0] = 0
    loss[loss > 0] = 0

    gain_ewm = gains.ewm(com=window - 1, adjust=adjust).mean()
    loss_ewm = abs(loss.ewm(com=window - 1, adjust=adjust).mean())

    RS = gain_ewm / loss_ewm
    RSI = 100 - 100 / (1 + RS)

    return RSI

##################################################################################################
#                                                                                                #
#                                          Main                                                  #
#                                                                                                #
##################################################################################################

# 周末不執行
dt = datetime.now()
x = dt.strftime('%A')
h = dt.strftime("%I%p")

if x == 'Saturday' or x == 'Sunday':
	print("Exit")
	sys.exit(x)

headers = ['代碼', '收盤價', '配息日', '配息', '此次配息率', '殖利率', '當日漲跌幅', '一年最低價', '一年最高價', 'RSI', 'volume_Delta', 'Surprise%']

df_res = pd.DataFrame(columns = headers)
# 有興趣的股票
Other_stocks = ['CL', 'HAS', 'IP', 'AAP', 'LEG', 'WU', 'XRX', 'KSS', 'JWN', 'MO', 'EPD',
		'DOW', 'CVX', 'SHEL', 'XOM', 'BP', 'ET', 'KMI', 'TTE', 'O', 'MO', 'T', 'VTRS']

aristocrats = getAristocrats()
SNP500 = sp500_tickers() 

stocks = SNP500 + Other_stocks

stocks = list(set(stocks))  # remove duplicates
stocks = list(map(lambda x: x.replace('.', '-'), stocks)) # e.g. BRK.B, BF.B，要改為 BRK-B, BF-B 才讀得到交易資料

#stocks = Other_stocks
stocks.sort()

#print(stocks)

print('---------------------------------------------\n\n')

# 找出最近配息的股票
for s in stocks:
	#print(s, end='\t', flush=True)
	print(s)
	ticker = yf.Ticker(s)

	# 上市不滿一年的股票不處理
	try:
		df = ticker.history(period='1y')
		#df['RSI'] = ta.RSI(df['Close'], timeperiod=14)
	except Exception as e:
		print(f"{s} 上市不滿一年, msg={e}")
		continue

	if s in aristocrats:
		s_ = s + '/AR'
	elif s in SNP500:
		s_ = s + '/SNP'
	else:
		s_ = s

	RSI = getRSI(df)  # A series

	#print(RSI[-1])

	'''
	RSI = round(df.tail(1)['RSI'][0],2)					# RSI

	# Bollinger Bands
	upper, middle, lower = ta.BBANDS(df['Close'], matype=MA_Type.T3)
	df['BBLower'] = lower
	df['BBUpper'] = upper
	df['BBMiddle'] = middle
	LBAND = round(df.tail(1)['BBLower'][0],2)
	UBAND = round(df.tail(1)['BBUpper'][0],2)
	MBAND = round(df.tail(1)['BBMiddle'][0],2)
	BV = round((round(df.tail(1)['Close'][0],2)-MBAND)/(UBAND-MBAND)*50,2)
	'''

	Close = round(df.tail(1)['Close'][0],2) 			# 最新收盤價
	fiftyTwoWeeksLow = round(df['Close'].min(),2)
	fiftyTwoWeeksHigh = round(df['Close'].max(),2)
	#volume = int(ticker.info['volume'])
	#avg_Volume = int(ticker.info['averageVolume'])
	#volume_Delta =  round((volume/avg_Volume)*100,2)
	volume_Delta = 0.0

	#percent_change = ((last_price - first_price) / first_price) * 100
	#max_P = df.tail(22)['Close'].max()
	#min_P = df.tail(22)['Close'].min()

	changed = round((df.tail(22)['Close'].max() - Close) / (df.tail(22)['Close'].max()) * 100, 2)  # 一個月內最大跌幅

	prev_close = round(df.tail(2)['Close'][0],2)                                    # 前一日收盤價
	change = round((Close - prev_close) / prev_close * 100,2)                       # 當日漲跌幅

	try:
		div_date = ticker.info['exDividendDate']		# 配息日
		div_date = datetime.utcfromtimestamp(div_date).strftime('%Y-%m-%d')


		yields = round(ticker.info['dividendYield'],2)
	except Exception as e:
		div_date = ''

	#print("yields", yields)

	if len(div_date) > 1 and div_date > date.today().strftime("%Y-%m-%d") and yields > 4.0:
		print(s, end='\t', flush=True)
		dividends = ticker.info['dividendRate']			# 最近一年配息總額
		div2 = ticker.info['lastDividendValue']
		div2 = float(div2)
		div_thisTime = str(round((div2 / Close) * 100,3)) + '%'

		earnings = finnhub_client.company_earnings(s, limit=5) # get earnings

		all_surprises = [d["surprisePercent"] for d in earnings] # Extract specific elements from list of dictionaries
		all_surprises1 = [ '%.2f' % elem for elem in all_surprises ] # round float to two deciamals

		all_surprises2 = [str(number) for number in all_surprises1] # convert numbers to strings

		separator = "/" # join elements of a list and add separators
		result_string = separator.join(all_surprises2)
		#print(result_string)
		Surprise = result_string

		# '此次配息率'
		# headers = ['代碼', '收盤價', '配息日', '配息', '此次配息率', '殖利率', '當日漲跌幅', '一年最低價', '一年最高價', 'RSI', 'volume_Delta', 'Surprise%']
		df_res.loc[len(df_res.index)] = [s_, '$' + str(Close), div_date, '$' + str(div2), div_thisTime, str(yields) + '%', str(change)+'%', fiftyTwoWeeksLow, fiftyTwoWeeksHigh,  round(RSI[-1],2), str(volume_Delta)+'%', Surprise] 

#print('\n\n\n')
df_res = df_res.sort_values(by=['配息日'], ascending=True)
df_res = df_res.reset_index(drop=True)

recp = ['scshao@berkeley.edu']
recp_0 = ['scshao@berkeley.edu', 'poi7415778@gmail.com']
#recp_0 = ['scshao@berkeley.edu', 'crystalchientw@gmail.com', 'poi7415778@gmail.com']
recp_1 = ['scshao@berkeley.edu', 'ldscontact@hotmail.com', ]
recp_2 = ['scshao@berkeley.edu', 'poi7415778@gmail.com', 'wimmylin@gmail.com', 'Andy0727@gmail.com','msung520@gmail.com', 'ldscontact@hotmail.com', 'crystalchientw@gmail.com']

with open('mail2.html', 'r', encoding="utf-8") as f:
    lines = f.read()

if len(df_res) >0:
	msg_1 = df_res.to_html() + lines
	today = date.today().strftime('%Y-%m-%d')
	sendMail(today + " 美股近期配息列表", msg_1, recp_0)

print(tabulate(df_res, headers, tablefmt="grid"))



