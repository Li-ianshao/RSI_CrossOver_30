import yfinance as yf
import time

tickers = ['AAPL', 'T', 'MO', 'XOM', 'KO']
results = []

for symbol in tickers:
    try:
        time.sleep(1.5)
        info = yf.Ticker(symbol).info
        results.append({
            'Ticker': symbol,
            'Dividend Date': info.get('dividendDate'),
            'Dividend Yield (%)': round(info.get('dividendYield', 0)*100, 2),
            'Dividend Amount ($)': round(info.get('dividendRate', 0), 2)
        })
    except Exception as e:
        print(f"{symbol} 讀取失敗: {e}")