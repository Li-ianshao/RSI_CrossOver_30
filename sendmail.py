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
import sys
from os.path import exists
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from requests.adapters import HTTPAdapter, Retry
from io import StringIO

import finnhub
# Setup client
finnhub_client = finnhub.Client(api_key="d0noj91r01qn5ghl2c3gd0noj91r01qn5ghl2c40")

import warnings
warnings.filterwarnings("ignore")
'''
def get_sp500_tickers():
	url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
	df = pd.read_html(url)[0]
	tickers = df['Symbol'].tolist()
	tickers = [t.replace('.', '-') for t in tickers]
	return tickers
'''
'''
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
'''

def get_sp500_tickers(as_yfinance: bool = True, timeout: int = 15) -> list[str]:
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

    sess = requests.Session()
    sess.mount("https://", HTTPAdapter(max_retries=Retry(
        total=5, backoff_factor=0.3,
        status_forcelist=[403, 429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )))
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
    }
    r = sess.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()

    # ✅ 用 StringIO 包住 resp.text，避免 FutureWarning
    tables = pd.read_html(StringIO(r.text), attrs={"id": "constituents"})  # 需要 lxml 解析器
    if not tables:
        raise RuntimeError("Constituents table not found.")
    df = tables[0]

    tickers = (
        df["Symbol"].astype(str).str.strip().tolist()
    )
    if as_yfinance:
        tickers = [t.replace(".", "-") for t in tickers]  # BRK.B -> BRK-B
    return tickers


def getAristocrats(as_yf=True):
    url = "https://en.wikipedia.org/wiki/S%26P_500_Dividend_Aristocrats"

    # 用帶 UA 的 session + 重試
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
    })
    sess.mount("https://", HTTPAdapter(max_retries=Retry(
        total=5, backoff_factor=0.3,
        status_forcelist=[403,429,500,502,503,504],
        allowed_methods=["GET"]
    )))

    r = sess.get(url, timeout=15)
    r.raise_for_status()

    # 用 StringIO 包裝字串給 read_html
    tables = pd.read_html(StringIO(r.text))   # 需要 pip install lxml
    # 找到含有 Symbol/Ticker 欄位且至少幾十列的表
    df = None
    for t in tables:
        cols = [str(c).lower() for c in t.columns]
        if any(("symbol" in c or "ticker" in c) for c in cols) and len(t) > 20:
            df = t; break
    if df is None:
        raise RuntimeError("Ticker table not found (page layout may have changed).")

    # 取出欄名
    col = next(c for c in df.columns if "Symbol" in str(c) or "Ticker" in str(c))
    tickers = (
        df[col].astype(str).str.strip().str.replace("\u200b","", regex=False).tolist()
    )
    if as_yf:
        tickers = [t.replace(".", "-") for t in tickers]  # BRK.B -> BRK-B
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

    mail.login('scshaoifd@gmail.com', 'qnug anok xwoa ofze')
    
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

def get_sp100_tickers(as_yfinance: bool = True, fallback_if_fail: bool = True) -> list[str]:
    """
    抓取 S&P 100 成分股，回傳 list。
    - as_yfinance=True：把 '.' 轉成 '-'（BRK.B -> BRK-B），方便 yfinance。
    - fallback_if_fail=True：抓取失敗時回傳內建備用清單（不一定剛好 100 檔）。
    """
    url = "https://en.wikipedia.org/wiki/S%26P_100"
    try:
        tables = pd.read_html(url)
        df = None
        # 找到包含 Symbol 欄位的表
        for t in tables:
            cols = [c.lower() for c in t.columns]
            if any("symbol" in c or "ticker" in c for c in cols):
                df = t
                break
        if df is None:
            raise RuntimeError("No SP100 table found.")
        # 抓欄位名
        col_name = None
        for c in df.columns:
            lc = str(c).lower()
            if "symbol" in lc or "ticker" in lc:
                col_name = c
                break
        if col_name is None:
            raise RuntimeError("Ticker column not found.")

        tickers = (
            df[col_name]
            .astype(str)
            .str.strip()
            .tolist()
        )
        # 去重、去空
        tickers = sorted({t for t in tickers if t and t.lower() != "nan"})

        if as_yfinance:
            tickers = [t.replace(".", "-") for t in tickers]

        return tickers

    except Exception as e:
        if not fallback_if_fail:
            raise
        # 簡易備用清單（節選，方便先跑；建議網路可用時改抓 Wikipedia）
        fallback = [
            "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","AVGO","LLY","TSLA",
            "BRK-B","JPM","V","UNH","XOM","MA","PG","HD","COST","JNJ",
            "MRK","ORCL","ADBE","PEP","BAC","KO","CRM","PFE","CSCO","ABT",
            "WMT","NFLX","TMO","ACN","DHR","MCD","WFC","TXN","LIN","PM",
            "INTU","IBM","AMD","CVX","CAT","GE","AMGN","LOW","HON","COP",
            "NKE","INTC","NEE","UPS","UNP","MS","RTX","SPGI","BKNG","QCOM",
            "BLK","SBUX","MDT","PLD","ADP","AMAT","ELV","GS","DE","LMT",
            "C","AXP","MDLZ","SYK","GILD","TJX","T","NOW","TGT","MMC"
        ]
        return fallback
###########################################################################################

recp_0 = ['scshao@berkeley.edu', 'poi7415778@gmail.com']


# 周末不執行
dt = datetime.now()
x = dt.strftime('%A')
h = dt.strftime("%I%p")


if x == 'Saturday' or x == 'Sunday':
	print("Exit")
	sys.exit(x)


Other_stocks = ['CL', 'HAS', 'IP', 'AAP', 'LEG', 'WU', 'XRX', 'KSS', 'JWN', 'MO', 'EPD',
		'DOW', 'CVX', 'SHEL', 'XOM', 'BP', 'ET', 'KMI', 'TTE', 'O', 'T', 'VTRS']

aristocrats = getAristocrats()
SNP500 = get_sp500_tickers()
sp100 = get_sp100_tickers(as_yfinance=True)

tickers = SNP500 + Other_stocks
#tickers = tickers[:100]

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
		# 過去一年殖利率不到 3.5% 的離開
		div_pay_date = datetime.utcfromtimestamp(div_pay_date).strftime('%Y-%m-%d')
		yields = df['Dividends'].sum() / df['Close'][-1] * 100
		change = (df['Close'][-1] - df['Close'][-2]) / df['Close'][-2] * 100

		if yields >= 3.5:
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
				try:
					yields = round(info['dividendYield'],2)

				except Exception as e:
					continue

				dividends = info['dividendRate']			# 最近一年配息總額
				#div2 = float(ticker.info['lastDividendValue']) # 本次配息金額
				div2 = info.get('lastDividendValue', 'NA')
				RSI = getRSI(df)

				T_EPS = info['trailingEps']     # 最近 12 個月 (TTM) EPS
				F_EPS = info['forwardEps']      # 預估 EPS
				EPS = str(T_EPS) + ':' + str(F_EPS)

				if ticker in sp100:
					snp100 = True
				else:
					snp100 = False

				results.append({
					'Ticker': s_,
					'SP100': str(snp100),
					'Close': '$' + str(round(df['Close'][-1],2)),
					'Change': str(round(change,2)) + '%',
					'Div_Date': exDividendDate,
					'Pay_Date': div_pay_date,
					'PayAmount': '$' + str(round(dividends, 4)),
					'Yields': round(yields, 2), #str(round(yields, 2)) + '%',
					'QuarterPay': 'NA' if div2 == 'NA' else "$" + str(div2) + '/Share',
					'52WksMin': '$' + str(round(df['Close'].min(),2)),
					'52WksMax': '$' + str(round(df['Close'].max(),2)),
					'RSI': round(RSI[-1],2),
					'trailing/Forward EPS':EPS
				})
			time.sleep(3.0)

df = pd.DataFrame(results)
df = df.sort_values(by=['Div_Date'], ascending=True)
df = df.reset_index(drop=False)

print(tabulate(df, df.columns, tablefmt="grid"))

#df.to_csv('out.csv')

def df_to_html_with_inline_style(df):
    html = '<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">\n'
    html += '<tr>' + ''.join(f'<th>{col}</th>' for col in df.columns) + '</tr>\n'

    for _, row in df.iterrows():
        html += '<tr>'
        for col in df.columns:
            val = row[col]
            style = ''

            # 根據你的條件判斷
            if col == 'RSI':
                if val >= 70:
                    style = 'background-color: red; color: white; font-weight: bold;'
                elif val <= 30:
                    style = 'background-color: green; color: white; font-weight: bold;'
            elif col == 'Yields':
                if val >= 5.0:
                    style = 'background-color: green; color: white; font-weight: bold;'
            elif col == 'SP100':
                if val == 'True':
                    style = 'background-color: green; color: white; font-weight: bold;'

            html += f'<td style="{style}">{val}</td>'
        html += '</tr>\n'
    html += '</table>'
    return html

html_table = df_to_html_with_inline_style(df)

recp_0 = ['scshao@berkeley.edu', 'poi7415778@gmail.com']
#recp_0 = ['scshao@berkeley.edu', 'crystalchientw@gmail.com', 'poi7415778@gmail.com']

with open('mail2.html', 'r', encoding="utf-8") as f:
    lines = f.read()

if len(df) >0:
	msg_1 = html_table + lines
	today = date.today().strftime('%Y-%m-%d')
	sendMail(today + " 美股近期配息列表", msg_1, recp_0)




