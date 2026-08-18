import json
import bs4 as bs
import requests
import yahoo_fin.stock_info as si       # very good module
import os, shutil
import yfinance as yf
import pandas as pd
import email, smtplib, ssl
from os.path import exists
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
from datetime import datetime
import time
import math

from collections import defaultdict

def proceed(): # 決定是否執行程式
    # 星期六或星期日不執行
    dt = datetime.now()
    weekday = dt.weekday()

    if weekday == 5 or weekday == 6:
        return False

    # 如果今天是國定假日，不執行
    nationalDays = ['01-05', '12-25'] # 還需要增加國定假日不開盤的日期

    dt = dt.strftime("%m-%d")
    if dt in nationalDays:
        return False

def calculateDecrease(s):  # 計算各股票三個月的最大跌幅，回傳一個 dictionary
    decrease = {}
    try:
        ticker = yf.Ticker(s) 
        df = ticker.history(period='3mo')
        Close = round(df.tail(1)['Close'][0],2)                                         # 最新收盤價/現價
        max_close = df['Close'].max()                                                   # 最近三個月內最高價
        min_close = df['Close'].min()                                                   # 最近三個月內最低價
        
        decreased = round((max_close - Close) / (max_close) * 100, 2) # 三個月內最大跌幅 %
        increased = - round((min_close - Close) / (min_close) * 100, 2) # 三個月內最大漲幅 %

        decrease['Dec'] = decreased
        decrease['Inc'] = increased

    except Exception as e:
        print(f'stock {s} fetch error {str(e)}')
    return decrease



def calculateStatic(stocks):
    print('Calculating statics....')
    static = {}

    for s in stocks:
        print(s)
        estimates, actuals, surprises = getEarnings(s)
        
        quote = si.get_quote_table(s)

        PERatio = quote['PE Ratio (TTM)']
        #if 'nan' in PERatio:
        if math.isnan(PERatio):
            PERatio = ''
        else: 
            PERatio = str(PERatio)

        EPS = quote['EPS (TTM)']

        #Volume = int(quote['Volume'])
        #Volume = f"{Volume:,d}"
        
        avg_Volume = int(quote['Avg. Volume'])
        avg_Volume = f"{avg_Volume:,d}"

        div_yield = quote['Forward Dividend & Yield'] 

        if 'N/A' in div_yield:
            div_yield = ''

        div_date = quote['Ex-Dividend Date']

        div_date = str(div_date)
        if 'nan' in div_date:
            div_date = ''

        static[s] = {}
        static[s]['Estimates'] = estimates
        static[s]['Actuals'] = actuals
        static[s]['Surprises'] = surprises

        static[s]['PERatio'] = PERatio
        static[s]['EPS'] = EPS

        static[s]['AVG_Volume'] = avg_Volume

        static[s]['Div_Yields'] = div_yield
        static[s]['Ex_Div_Date'] = div_date

    #print(f'stock function lin3 107 {static}')

    return static


def getData(stock_symbols, decrease): # 讀取與計算股票即時資訊
    stock_data = []

    for s in stock_symbols:
        try:
            # 使用 yfinance 獲取股票資訊
            stock = yf.Ticker(s)
            df = stock.history(period='1d')
            Close = round(df.tail(1)['Close'][0],2)
            print(decrease[s][0])  # decrease['XOM'][1]

            try:
                t = {'Symbol': s, 'Industry':'None', 'Close': Close, 'Decrease': 0, '3mDecrease':decrease[s][0]}
                print(t)
                stock_data.append(t)
            except Exception as e:
                print(f'stock_functions error line 70:{e}')

        except Exception as e:
            print(f'無法獲取 {s} 的資訊：{e}')
            stock_data.append({'symbol': s, 'data': None})
    return stock_data

def getYearData(symbol):
    # 使用 yfinance 獲取股票資訊
    stock = yf.Ticker(symbol)
    df = stock.history(period='1y')
    return df

############################################################################################

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

    mail.login('scshaoifd@gmail.com', 'ttgkpaxtqxvqndai')
    mail.sendmail(me, recp, text)
    mail.quit()

def getEarnings(s):
    earnings = si.get_analysts_info(s)['Earnings History']
    estimates = str(earnings.iloc[0,1]) + '/' + str(earnings.iloc[0,2]) + '/' + str(earnings.iloc[0,3]) + '/' + str(earnings.iloc[0,4])
    actuals = str(earnings.iloc[1,1]) + '/' + str(earnings.iloc[1,2]) + '/' + str(earnings.iloc[1,3]) + '/' + str(earnings.iloc[1,4])
    surprises = str(earnings.iloc[3,1]) + '/' + str(earnings.iloc[3,2]) + '/' + str(earnings.iloc[3,3]) + '/' + str(earnings.iloc[3,4])

    return estimates, actuals, surprises

def get_sp500():
    resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = []

    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text
        tickers.append(ticker.rstrip())

    json_object = json.dumps(tickers)

    with open("c:/python310/data/SNP500.json", "w") as outfile:
        outfile.write(json_object)

    return tickers

def getAristocrats():  # 網路搜尋 Aristocrats 股票名單，存為 json 檔案，傳回整個名單
    resp = requests.get('https://en.wikipedia.org/wiki/S%26P_500_Dividend_Aristocrats')
    soup = bs.BeautifulSoup(resp.text, 'lxml')

    table = soup.find('table', {'class': 'wikitable sortable'})

    tickers = []

    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[1].text.rstrip()
        tickers.append(ticker)
    
    json_object = json.dumps(tickers)

    ticker = list(map(lambda x: x.replace('.', '-'), ticker)) # e.g. BRK.B, BF.B，要改為 BRK-B, BF-B 才讀得到交易資料
    ticker.sort()

    return tickers

def getKing():  # 網路搜尋 Aristocrats 股票名單，存為 json 檔案，傳回整個名單
    resp = requests.get('https://www.marketbeat.com/dividends/kings/')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    mydivs = soup.find_all("div", {"class": "ticker-area"})
    
    tickers = []

    for s in mydivs:
        tickers.append(s.text.rstrip())
        #print(s.text.rstrip())

    return tickers

def fetch_stock_prices(stocks, startDate, endDate, folder_path='c:/python310/data'):    # 讀取股票交易資料，儲存為 pkl 檔案，只須執行一次
    # 刪除 working directory 目錄下所有 .pkl 檔案
    '''
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.pkl'):
                os.remove(os.path.join(root, file))
    '''
    
    print('Fetching transaction data')
    
    for s in stocks:
        print(s)
        try:
            ticker = yf.Ticker(s) 
            df = ticker.history(start=startDate, end=endDate)
            df = df[['High', 'Low', 'Close', 'Dividends']]
            # 將日期改為純日期格式，不要時分秒
            df.index = df.index.strftime('%Y-%m-%d') 
            df.to_pickle(folder_path + '/' + s + '.pkl')
        except Exception as e:
            print(f'stock {s} fetch error {str(e)}')
    return stocks

def get_pkl(dirName):
    stocks = []

    for root, dirs, files in os.walk(dirName):
        for file in files:
            if file.endswith('.pkl'):
                file = file[0:len(file)-4]
                stocks.append(file)

    return stocks

def doLoop():
    global desc_filter

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)

    # 先檢查特別關注股票是否可以買進
    watch_list = {'AAPL':150.0, 'AMD': 70.0,'BEN':22.0, 'ENPH': 95.0, 'ET':11.0, 'FUTU': 30.0,'IBM':125.0, 'KMI':16.0, 'MSFT':240.0, 'MMM':85.0, 'MO':39.0, 'VTRS':8.95}

    for s in watch_list:
        #print(s, '->', watch_list[s])
        try:
            ticker = yf.Ticker(s)
            df = df = ticker.history(period='1mo')
            Close = round(df.tail(1)['Close'][0],2)

            if Close <= watch_list[s]:
                print(f'stock {s} current price is below target price {watch_list[s]}')

                if s not in sent:
                    sendMail("美股" + s + '跌到買進目標價' + str(watch_list[s]), 'As title', "scshao@berkeley.edu")
                    sent.append(s)
        except Exception as e:
            print(f'stock {s} fetch error {str(e)}')


    headers_1 = ['代碼', 'industry', '收盤價', '漲跌幅%', '3mo漲跌幅', 'P/E', 'EPS_TTM', 'Vol./Avg. Vol.', 'Div&Yields', 'Ex. Div_date', 'Estimate', 'Actual', 'Surprise', 'RSI', 'UBBAND/Middle/LBBAND', 'MACDHist']
    df_Outputs = pd.DataFrame(columns = headers_1)
    df_Outputs_2 = pd.DataFrame(columns = headers_1)

    # 計算股票近三個月的最大跌幅，超過 30% 的列出來
    for s in stocks:
        #print(s)
        try:
            ticker = yf.Ticker(s) 
            df = ticker.history(period='3mo')
            Close = round(df.tail(1)['Close'][0],2)                                         # 最新收盤價/現價
            prev_close = round(df.tail(2)['Close'][0],2)                                    # 前一日收盤價
            change = round((Close - prev_close) / prev_close * 100,2)                       # 當日漲跌幅
            
            max_close = df['Close'].max()                                                   # 最近三個月內最高價
            min_close = df['Close'].min()                                                   # 最近三個月內最低價
            
            decreased = round((max_close - Close) / (max_close) * 100, 2) # 三個月內最大跌幅 %
            increased = - round((min_close - Close) / (min_close) * 100, 2) # 三個月內最大漲幅 %

            #print(df)
            
            if decreased >= desc_filter or increased >= desc_filter:
                if s in aristocrats:
                    s_ = s + '/AR'
                elif s not in stocks:
                    s_ = s + '/NSP'
                else:
                    s_ = s
                
                industry = ticker.info['industry']

                # 查詢這些股票的營收數據
                estimates, actuals, surprises = getEarnings(s)
                quote = si.get_quote_table(s)
                PERatio = quote['PE Ratio (TTM)']
                #if 'nan' in PERatio:
                if math.isnan(PERatio):
                    PERatio = ''
                else: 
                    PERatio = str(PERatio)

                EPS = quote['EPS (TTM)']
                
                Volume = int(quote['Volume'])
                Volume = f"{Volume:,d}"
                
                avg_Volume = int(quote['Avg. Volume'])
                avg_Volume = f"{avg_Volume:,d}"

                div_yield = quote['Forward Dividend & Yield'] 
                if 'N/A' in div_yield:
                    div_yield = ''

                div_date = quote['Ex-Dividend Date']
                #print(type(div_date))
                div_date = str(div_date)
                if 'nan' in div_date:
                    div_date = ''

                # 查詢這些股票的技術面數據 RSI, BBAND, MACD
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

                headers_1 = ['代碼', 'industry', '收盤價', '漲跌幅%', '3mo漲跌幅', 'P/E', 'EPS_TTM', 'Vol./Avg. Vol.', 'Div&Yields', 'Div_date', 'Estimate', 'Actual', 'Surprise', 'RSI', 'UBBAND/LBBAND', 'MACDHist']
                if decreased >= desc_filter:
                    df_Outputs.loc[len(df_Outputs.index)] = [s_, industry, '$' + str(Close), str(change) + '%', decreased, PERatio, EPS, str(Volume) + '/' + str(avg_Volume), div_yield, div_date, estimates, actuals, surprises, str(RSI), BBAND, str(MACD)] 
                if increased >= desc_filter:
                    df_Outputs_2.loc[len(df_Outputs_2.index)] = [s_, industry, '$' + str(Close), str(change) + '%', increased, PERatio, EPS, str(Volume) + '/' + str(avg_Volume), div_yield, div_date, estimates, actuals, surprises, str(RSI), BBAND, str(MACD)] 

        except Exception as e:
                print(f'stock {s} fetch error {str(e)}')

    df_Outputs = df_Outputs.sort_values(by=['3mo漲跌幅'], ascending = False)
    df_Outputs = df_Outputs.reset_index(drop=True)
    df_Outputs['3mo漲跌幅'] = df_Outputs['3mo漲跌幅'].astype(str) + '%'

    df_Outputs_2 = df_Outputs_2.sort_values(by=['3mo漲跌幅'], ascending = False)
    df_Outputs_2 = df_Outputs_2.reset_index(drop=True)
    df_Outputs_2['3mo漲跌幅'] = df_Outputs_2['3mo漲跌幅'].astype(str) + '%'

    print('\n\n$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
    print("跌多股票列表")
    print(tabulate(df_Outputs, headers_1, tablefmt="grid"))
    df_Outputs.to_csv('USstocks/' + str(date.today()) + '_desc.csv')
    print('\n\n$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n')
    print('漲多股票列表')
    print(tabulate(df_Outputs_2, headers_1, tablefmt="grid"))
    df_Outputs_2.to_csv('USStocks/' + str(date.today()) + '_incr.csv')
    print('\n\n$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n\n\n')




