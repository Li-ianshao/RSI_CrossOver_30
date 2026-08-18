# 如果執行發生錯誤，很可能是 yfinance 改版，執行下列程式 upgrate
# pip install yfinance --upgrade --no-cache-dir

# 最近配息的股票以及 RSI < 25 的股票
import yfinance as yf
import pandas as pd
import numpy as np
import math

import json
import bs4 as bs
import requests

from datetime import timedelta, date
from datetime import datetime, UTC
from tabulate import tabulate
import email, smtplib, ssl
from os.path import exists
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time

# Setup client
import finnhub
finnhub_client = finnhub.Client(api_key="d0noj91r01qn5ghl2c3gd0noj91r01qn5ghl2c40")


#import warnings
#warnings.filterwarnings("ignore")

def sp500_tickers():
    table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    tickers = table[0]['Symbol'].tolist()
    return [ticker.replace('.', '-') for ticker in tickers]

def getAristocrats():
	resp = requests.get('https://en.wikipedia.org/wiki/S%26P_500_Dividend_Aristocrats')
	soup = bs.BeautifulSoup(resp.text, 'lxml')

	table = soup.find('table', {'class': 'wikitable sortable'})

	tickers = []

	for row in table.find_all('tr')[1:]:
		ticker = row.find_all('td')[1].text.rstrip()
		tickers.append(ticker)

	return tickers

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
tickers = list(map(lambda x: x.replace('.', '-'), stocks)) # e.g. BRK.B, BF.B，要改為 BRK-B, BF-B 才讀得到交易資料

tickers = tickers[:100]
#stocks = Other_stocks
tickers = ['ARE', 'APA', 'BBY', 'BEN']
tickers.sort()


#************************************************************************************************

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


def fetch_stock_data(tickers, period='1y', interval='1d', max_retries=3):
	records = []  # 最終存放所有股票資料（list of dict）

	for symbol in tickers:
		attempt = 0
		success = False

		while attempt < max_retries and not success:
			try:
				print(f"\n📥 Fetching {symbol} (Attempt {attempt + 1})")

				# 取得歷史交易資料
				ticker_obj = yf.Ticker(symbol)

				# 取得 info
				info = ticker_obj.info

				# 過濾掉沒有配息，配息過少，配息日已過的股票
				try:
					div_date = info.get('exDividendDate')		# ex 配息日
					div_date = datetime.fromtimestamp(div_date, UTC).strftime("%Y-%m-%d")
					yields = round(info.get('dividendYield'),2)
					print(div_date, yields)
					
				except Exception as e:
					print(e)
					print('No Dividend')
					break

				#print(f'div_date={div_date}, yileds={yields}')

				if div_date <= date.today().strftime("%Y-%m-%d") or yields < 4.0:
					print('配息日已過，無意義')
					break

				print(f'div_date={div_date}, yileds={yields}')

				success = True
				time.sleep(0.5)  # 避免太快被限速

			except Exception as e:
				print(f"❌ Error on {symbol}: {e}")
				attempt += 1
				time.sleep(1)
				'''
				if div_date <= date.today().strftime("%Y-%m-%d") or yields < 4.0:
					print('配息日已過，無意義')
					break

				# 有配息才有繼續下去的意義

				print(f"Div_Date:{div_date}, yield={yield}")
				# 從歷史資料中取出最新一天

				hist = ticker_obj.history(period=period, interval=interval)

				if hist.empty:
				    raise ValueError(f"{symbol} has no historical data.")
				    break
				latest = hist.iloc[-1]

				# 建立紀錄（可根據需要調整欄位）

				Close = latest['Close']
				prev_close = round(hist.tail(2)['Close'][-2],2)
				print('previous close', prev_close)
				#prev_close = round(stock_df.tail(2)['Close'],2)
				fiftyTwoWeeksLow = round(hist['Close'].min(),2)
				fiftyTwoWeeksHigh = round(hist['Close'].max(),2)
				RSI = getRSI(hist)

				try:
					volume = latest['Volume']
					avg_Volume = int(info.get('averageVolume'))
					print('Volume', volume, avg_Volume)
					volume_Delta =  round((volume/avg_Volume)*100,2)
				except Exception as e:
					volume = latest['Volume']
					avg_Volume = ''
					volume_Delta = ''

				
					div2 = info.get('lastDividendValue')

					print("Div/Close", div2, Close)
					div_thisTime = str(round((div2 / Close) * 100,3)) + '%'
					earnings = finnhub_client.company_earnings(symbol, limit=5) # get earnings

					all_surprises = [d["surprisePercent"] for d in earnings] # Extract specific elements from list of dictionaries
					all_surprises1 = [ '%.2f' % elem for elem in all_surprises ] # round float to two deciamals

					all_surprises2 = [str(number) for number in all_surprises1] # convert numbers to strings

					separator = "/" # join elements of a list and add separators
					result_string = separator.join(all_surprises2)
					Surprise = result_string

					print("Prev-Close", Close, prev_close)

					record = {
						'Ticker': symbol,
						'Date': latest.name.date(),
						'Close': '$' + str(Close),
						'change': '$' + str(round((Close - prev_close) / prev_close * 100,2)),
						'Volume': volume,
						'DividendDate': div_date,
						'div2': div2,
						'div_thisTime': div_thisTime,
						'yields': yields,
						'RSI': round(RSI[-1],2),
						'volume_Delta': volume_Delta,
						'Surprise': Surprise,
						##'MarketCap': info.get('marketCap'),
						'Sector': info.get('sector'),
						##'LongName': info.get('longName'),
						'PE': info.get('trailingPE')
	                }
					records.append(record)
				else:
					div2 = ''
					Surprise = ''
					div_thisTime = ''
				success = True
				time.sleep(0.5)  # 避免太快被限速

			except Exception as e:
				print(f"❌ Error on {symbol}: {e}")
				attempt += 1
				time.sleep(1)

    # 整合為 DataFrame 回傳
	print('records=', records)
	df = pd.DataFrame(records)
	return df
	'''

df = fetch_stock_data(tickers)

'''
recp = ['scshao@berkeley.edu']
recp_0 = ['scshao@berkeley.edu', 'poi7415778@gmail.com']
#recp_0 = ['scshao@berkeley.edu', 'crystalchientw@gmail.com', 'poi7415778@gmail.com']
recp_1 = ['scshao@berkeley.edu', 'ldscontact@hotmail.com', ]
recp_2 = ['scshao@berkeley.edu', 'poi7415778@gmail.com', 'wimmylin@gmail.com', 'Andy0727@gmail.com','msung520@gmail.com', 'ldscontact@hotmail.com', 'crystalchientw@gmail.com']

with open('mail2.html', 'r', encoding="utf-8") as f:
    lines = f.read()

if len(df) >0:
	msg_1 = df.to_html() + lines
	today = date.today().strftime('%Y-%m-%d')
	#sendMail(today + " 美股近期配息列表", msg_1, recp_0)
'''
#df = df[['Ticker', 'Date', 'Close', 'change', 'Volume', 'DividendDate', 'div2', 'div_thisTime', 'yields', 'RSI',
#       'volume_Delta', 'Surprise', 'Sector', 'PE']]
#print(df.columns)
#print(tabulate(df.iloc[:, :8], df.columns, tablefmt="grid", showindex=False))



#print(df)
