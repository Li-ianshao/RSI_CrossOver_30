# 找出所有 SAP500 即將配息且殖利率超過 4% 的股票

# dividendDate (付息日) 幾乎每次都讀得到，所以先讀取他，如果讀不到就離開

import yfinance as yf
import pandas as pd
from datetime import timedelta, date
from datetime import datetime
import time
from tabulate import tabulate
import json
import bs4 as bs
import requests

import email, smtplib, ssl
from os.path import exists
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import finnhub
# Setup client
finnhub_client = finnhub.Client(api_key="d0noj91r01qn5ghl2c3gd0noj91r01qn5ghl2c40")

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

###########################################################################################
# 周末不執行
dt = datetime.now()
x = dt.strftime('%A')
h = dt.strftime("%I%p")

if x == 'Saturday' or x == 'Sunday':
	print("Exit")
	sys.exit(x)

Other_stocks = ['CL', 'HAS', 'IP', 'AAP', 'LEG', 'WU', 'XRX', 'KSS', 'JWN', 'MO', 'EPD',
		'DOW', 'CVX', 'SHEL', 'XOM', 'BP', 'ET', 'KMI', 'TTE', 'O', 'MO', 'T', 'VTRS']

aristocrats = getAristocrats()
SNP500 = sp500_tickers()

tickers = SNP500 + Other_stocks

tickers = list(set(tickers))  # remove duplicates

tickers.sort()

results = []

for s in tickers:
	print(s)
	ticker = yf.Ticker(s)
	df = ticker.history(period='1y')

	if s in aristocrats:
		s_ = s + '/AR'
	elif s in SNP500:
		s_ = s + '/SNP'
	else:
		s_ = s

	info = ticker.info

	div_pay_date = info.get('dividendDate','')

	if div_pay_date != '':  # 只處理有付息日期的股票
		# 過去一年殖利率不到 4% 的離開
		div_pay_date = datetime.utcfromtimestamp(div_pay_date).strftime('%Y-%m-%d')
		yields = df['Dividends'].sum() / df['Close'][-1] * 100

		if yields >= 4.0:
			# 強制讀取 exDividendDate 
			# 設定最多重試次數
			max_retries = 10

			attempt = 0
			success = False
    		
			while attempt < max_retries and not success:
				try:
					print(f"📥 Downloading: Attempt {attempt+1}")
					ticker = yf.Ticker(s)
					info = ticker.info
					exDividendDate = info.get('exDividendDate','')
					
					if exDividendDate != '':
					    success = True
					    exDividendDate = datetime.utcfromtimestamp(exDividendDate).strftime('%Y-%m-%d')
					else:
					    print(f"⚠️ Failed")
					    attempt += 1
					    time.sleep(1)
				except Exception as e:
					print(f"❌ Failed: {e}")
					attempt += 1
					time.sleep(1)

			if exDividendDate != '' and exDividendDate > date.today().strftime("%Y-%m-%d"):
				yields = round(info['dividendYield'],2)

				if yields < 4.0:
					print('low yields')
					continue
				
				dividends = info['dividendRate']			# 最近一年配息總額
				#div2 = float(ticker.info['lastDividendValue']) # 本次配息金額
				div2 = info.get('lastDividendValue', 'NA')
				RSI = getRSI(df)

				earnings = finnhub_client.company_earnings(s, limit=5) # get earnings

				all_surprises = [d["surprisePercent"] for d in earnings] # Extract specific elements from list of dictionaries
				all_surprises1 = [ '%.2f' % elem for elem in all_surprises ] # round float to two deciamals

				all_surprises2 = [str(number) for number in all_surprises1] # convert numbers to strings

				separator = "/" # join elements of a list and add separators
				result_string = separator.join(all_surprises2)
				Surprise = result_string

				results.append({
					'Ticker': s_,
					'CLose': '$' + str(round(df['Close'][-1],2)),
					'Div_Date': exDividendDate,
					'Pay_Date': div_pay_date,
					'Pay_Amount': '$' + str(round(dividends, 4)),
					'Yields': str(round(yields, 2)) + '%',
					'Pay_This_Time': 'NA' if div2 == 'NA' else "$" + str(div2) + '/Share',
					'52WksMax': '$' + str(round(df['Close'].min(),2)),
					'52WksMin': '$' + str(round(df['Close'].max(),2)),
					'RSI': round(RSI[-1],2),
					'Surprises':Surprise
				})
			time.sleep(1.0)

df = pd.DataFrame(results)
df = df.sort_values(by=['Div_Date'], ascending=True)
df = df.reset_index(drop=True)

print(tabulate(df, df.columns, tablefmt="grid"))

recp_0 = ['scshao@berkeley.edu', 'poi7415778@gmail.com']
#recp_0 = ['scshao@berkeley.edu', 'crystalchientw@gmail.com', 'poi7415778@gmail.com']

with open('mail2.html', 'r', encoding="utf-8") as f:
    lines = f.read()

if len(df) >0:
	msg_1 = df.to_html() + lines
	today = date.today().strftime('%Y-%m-%d')
	sendMail(today + " 美股近期配息列表", msg_1, recp_0)

#print(tabulate(df_res, headers, tablefmt="grid"))



