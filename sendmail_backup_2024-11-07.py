# 最近配息的股票以及 RSI < 25 的股票
import yfinance as yf
import pandas as pd
import numpy as np
from new_stock_functions import *
import math

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

#headers = ['代碼', '收盤價', '配息日', '配息', '殖利率', '1M達標率', '2M達標率', '3M達標率', 'RSI', '1M最大跌幅', '一年最低價', '一年最高價']
headers = ['代碼', '收盤價', '配息日', '配息', '殖利率', 'RSI', '1M最大跌幅', '一年最低價', '一年最高價']

df_res = pd.DataFrame(columns = headers)
# 有興趣的股票
Other_stocks = ['CL', 'HAS', 'IP', 'AAP', 'LEG', 'WU', 'XRX', 'KSS', 'JWN', 
		'DOW', 'CVX', 'SHEL', 'XOM', 'ENPH', 'ENBP', 'BP', 'EQNR', 'ET', 'KMI', 'TTE', 'O', 'FUTU', 'MO', 'T', 'VTRS']

aristocrats = getAristocrats()
SNP500 = sp500_tickers() 

tmp = 0

stocks = SNP500 + Other_stocks

'''
try:
	stocks.remove('SW')
except Exception as e:
	tmp=1
'''

stocks = list(set(stocks))  # remove duplicates
stocks = list(map(lambda x: x.replace('.', '-'), stocks)) # e.g. BRK.B, BF.B，要改為 BRK-B, BF-B 才讀得到交易資料
stocks.sort()
#stocks = stocks[:50]

# 找出最近配息的股票
for s in stocks:
	print(s, end='\t', flush=True)
	#print('\n\n' + s)
	ticker = yf.Ticker(s)

	# 上市不滿一年的股票不處理
	try:	
		df = ticker.history(period='1y')
		df['RSI'] = ta.RSI(df['Close'], timeperiod=14)
	except Exception as e:
		print(f"{s} 上市不滿一年")
		continue

	if s in aristocrats:
		s_ = s + '/AR'
	elif s in SNP500:
		s_ = s + '/SNP'
	else:
		s_ = s

	RSI = round(df.tail(1)['RSI'][0],2)					# RSI

	Close = round(df.tail(1)['Close'][0],2) 			# 最新收盤價
	fiftyTwoWeeksLow = round(df['Close'].min(),2)
	fiftyTwoWeeksHigh = round(df['Close'].max(),2)
	changed = round((df.tail(22)['Close'].max() - Close) / (df.tail(22)['Close'].max()) * 100, 2)  # 一個月內最大跌幅
	#diff = (Close - fiftyTwoWeeksLow) / (fiftyTwoWeeksHigh - fiftyTwoWeeksLow) * 100 	# 距離一年最低價的差距%

	try:
		div_date = ticker.info['exDividendDate']		# 配息日
		div_date = datetime.utcfromtimestamp(div_date).strftime('%Y-%m-%d')
		yields = round(ticker.info['dividendYield'] * 100,2)
		#div_date = fc.get_div_hist_per_stock(s).index[0]
	except Exception as e:
		div_date = ''


	if len(div_date) > 1 and div_date > date.today().strftime("%Y-%m-%d") and yields > 4.0:
		dividends = ticker.info['dividendRate']			# 最近一年配息總額

		div2 = ticker.info['lastDividendValue']
		div2 = float(div2)


		print(f'\n\n股票:{s}, 配息日:{div_date}, 殖利率:{yields}, 全年配息$:{dividends}, 最近配息$:{div2}\n')

		# 計算填息率，可能沒資料
		'''
		div_hist = fc.get_div_hist_per_stock(s)			# Dividend History
		div_hist['Date'] = div_hist.index.astype(str)
		div_hist['Year'] = div_hist['Date'].str[-4:]

		# 只要最近五年的配息資料 df_t2
		year = date.today().year
		dateFiveYearsAgo = year - 5

		df_t2 = div_hist[div_hist['Year'] >= str(dateFiveYearsAgo)]
		#payDate = datetime.strptime(div_hist.iloc[i,3], '%m/%d/%Y').strftime('%Y-%m-%d')

		#print(df_t2)
		df_t2['1MGoal'] = False
		df_t2['2MGoal'] = False
		df_t2['3MGoal'] = False

		# 計算是否於一個月，兩個月，三個月內填息
		# 計算填息率，[本次填息日]到[下次填息日]之間股價增值是否大於配息金額，最近一次的配息不必計算(因為還沒發生，只是宣布而已)

		for i in range(len(df_t2)-1):
			try:
				# 找出配息日後續三個月的交易資料
				start_date = datetime.strptime(df_t2.iloc[i+1,3], '%m/%d/%Y') #.strftime('%Y-%m-%d')
				end_date = start_date + timedelta(days = 60)
				#print(f"Start_date={start_date}, end_date={end_date}")
				df_t = yf.download(s, start=start_date, end=end_date, progress=False)

				#print(df_t)
				amount = float(df_t2['amount'][i+1][1:])	# 配息金額

				# 一個月(20個交易日)內填息
				increase = df_t['Adj Close'].head(20).max() - df_t['Adj Close'][0]

				if increase >= amount:
					df_t2['1MGoal'][i] = True

				# 兩個月(40個交易日)內填息
				increase = df_t['Adj Close'].head(40).max() - df_t['Adj Close'][0]

				if increase >= amount:
					df_t2['2MGoal'][i] = True

				# 三個月內填息
				increase = df_t['Adj Close'].max() - df_t['Adj Close'][0]

				if increase >= amount:
					df_t2['3MGoal'][i] = True
			except Exception as e:
					print(e)
					continue

		#print(df_t2)
		
		M1Times = len(df_t2[df_t2['1MGoal']==True])
		M1Ratio = round(M1Times / len(df_t2) * 100,2)

		M2Times = len(df_t2[df_t2['2MGoal']==True])
		M2Ratio = round(M2Times / len(df_t2) * 100,2)

		M3Times = len(df_t2[df_t2['3MGoal']==True])
		M3Ratio = round(M3Times / len(df_t2) * 100,2)
		#print(f"股票:{s}, 五年內配息次數：{len(df_t2)}, 一個月填息次數:{M1Times}, 達成率:{M1Ratio}%, 兩個月填息次數:{M2Times}, 達成率:{M2Ratio}%, 三個月填息次數:{M3Times}, 達成率:{M3Ratio}% ")
		#headers = ['代碼', '收盤價', '配息日', '配息', '殖利率', '1M達標率', '2M達標率', '3M達標率', 'RSI', 'Earnings', '一年最低價', '一年最高價']

		'''
		
		#df_res.loc[len(df_res.index)] = [s_, '$' + str(Close), div_date, '$' + str(amount), str(yields) + '%', str(M1Ratio) + '%', str(M2Ratio) + '%', str(M3Ratio) + '%', round(RSI,2), str(changed) + '%', fiftyTwoWeeksLow, fiftyTwoWeeksHigh] 

		df_res.loc[len(df_res.index)] = [s_, '$' + str(Close), div_date, '$' + str(div2), str(yields) + '%', round(RSI,2), str(changed) + '%', fiftyTwoWeeksLow, fiftyTwoWeeksHigh] 

print('\n\n\n')
df_res = df_res.sort_values(by=['配息日'], ascending=True)
df_res = df_res.reset_index(drop=True)

recp = ['scshao@berkeley.edu']
recp_0 = ['scshao@berkeley.edu', 'crystalchientw@gmail.com', 'poi7415778@gmail.com']
recp_1 = ['scshao@berkeley.edu', 'ldscontact@hotmail.com', ]
recp_2 = ['scshao@berkeley.edu', 'poi7415778@gmail.com', 'wimmylin@gmail.com', 'Andy0727@gmail.com','msung520@gmail.com', 'ldscontact@hotmail.com', 'crystalchientw@gmail.com']

with open('mail2.html', 'r', encoding="utf-8") as f:
    lines = f.read()

if len(df_res) >0:
	msg_1 = df_res.to_html() + lines
	today = date.today().strftime('%Y-%m-%d')
	sendMail(today + " 美股近期配息列表", msg_1, recp_0)

print(tabulate(df_res, headers, tablefmt="grid"))

