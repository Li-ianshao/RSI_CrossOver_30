import yfinance as yf
from datetime import datetime, timedelta

# 定義股票代碼
tickers = ['XOM', 'TSLA']
# ES 是指標期貨，通常在 Yahoo Finance 顯示為 'ES=F'
tickers.append('ES=F')

# 設定日期
end_date = datetime.today()
start_date = end_date - timedelta(days=30)

# 轉換日期格式為字串
start_str = start_date.strftime('%Y-%m-%d')
end_str = end_date.strftime('%Y-%m-%d')

# 下載股票歷史資料
data = yf.download(tickers, start=start_str, end=end_str)

# 資料結構可能是多層索引，整理成方便存取的格式
for ticker in tickers:
    # 提取該股票的收盤價資料
    close_prices = data['Close'][ticker]
    # 取出第一天和最後一天的收盤價
    first_price = close_prices.iloc[0]
    last_price = close_prices.iloc[-1]
    # 計算漲跌幅百分比
    percent_change = ((last_price - first_price) / first_price) * 100

    print(f"{ticker} 最近一個月的漲跌幅：{percent_change:.2f}%")