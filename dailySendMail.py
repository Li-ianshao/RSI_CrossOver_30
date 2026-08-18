import yfinance as yf
import pandas as pd
from new_stock_functions import *
import math
from datetime import date
from datetime import datetime

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

threshold = 30.0  # 過濾門檻值
recp = ['scshao@berkeley.edu']
recp_1 = ['kelvintsai@infodoc.com.tw', 'scshao@berkeley.edu', 'kathytsu@gmail.com', 'crystalchientw@gmail.com', 'msung520@gmail.com']
#recp = ['kathytsu@gmail.com', 'scshao@berkeley.edu', 'chuchu0917@gmail.com', 'wimmylin@gmail.com', 'kelvintsai@infodoc.com.tw', 'm.wang8851@gmail.com', 'fulltimesandy@gmail.com', 'kao4jade@aol.com', 'jh.suen@gmail.com', 'bardodo@gmail.com', 'st2376@gmail.com', 'bswei@gatech.edu', 't_t1010m@yahoo.com', 'luhliang2106@gmail.com', 'joehuangus@yahoo.com', 'alice.wen88@gmail.com', 'christina.fong.lee@gmail.com', 'grace_chi@yahoo.com', 'dullmoow@gmail.com,' 'DorisChou@yahoo.com', 'gyu1623@yahoo.com', 'gloriachao1208@gmail.com', '2903ROG@gmail.com', 'Debbieltx077@gmail.com', 'tina_1688@yahoo.com', 'family.dwan@gmail.com', 'Imao9992@gmail.com', 'jduann@gmail.com','imiaochen@yahoo.com']

Other_stocks = ['CL', 'HAS', 'IP', 'AAP', 'GPS', 'LEG', 'WU', 'XRX', 'KSS', 'JWN', 
		'DOW', 'CVX', 'SHEL', 'XOM', 'ENPH', 'ENBP', 'BP', 'EQNR', 'ET', 'KMI', 'TTE', 'O', 'FUTU', 'MO', 'T', 'VTRS']

aristocrats = getAristocrats()
SNP500 = sp500_tickers()

stocks = SNP500 + Other_stocks
print(stocks)
stocks.remove("SW")
stocks = list(set(stocks))  # remove duplicates
stocks = list(map(lambda x: x.replace('.', '-'), stocks)) # e.g. BRK.B, BF.B，要改為 BRK-B, BF-B 才讀得到交易資料

print(stocks)
# testing only
#stocks = ['XOM', 'ENPH', 'FUTU', 'GL', 'CHTR', 'GE', 'MU']
stocks.sort()

# stocks, threshold, SNP500, aristocrats, threshold_day
no_dec_stocks, dec_output, no_inc_stocks, inc_output, no_dayDec_stocks, dayDec_output = getOutputs(stocks, threshold, SNP500, aristocrats)

df = pd.DataFrame(dec_output)

df.rename({'Ticker': '股票代碼', 'Category':'分類', 'Industry': '產業別', 'Price':'收盤價', 'Change':'漲跌幅%', 'Decreased':'最大跌幅%', 'PE':'本益比', 'EPS':'每股盈餘', 'Volume':'交易量', 'AVG_Vol':'平均交易量', 'Yield':'殖利率%', 'Dividend':'配息$', 'Div_Date':'最近配息日', 'Estimates':'估計季每股收益', 'Actuals':'實際季每股收益', 'Surprises':'訝異比'}, axis=1, inplace=True)

print(df)

with open('comments.txt', 'r', encoding="utf-8") as f:
	lines = f.read()

try:
    msg = df.to_html() + lines
    sendMail(str(date.today()) + " 美股 S&P500 跌深股列表", msg, recp_1)
except Exception as e:
    print(e)

#x = input('press enter to end')


