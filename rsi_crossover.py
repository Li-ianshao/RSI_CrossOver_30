import requests
import yfinance as yf
import pandas as pd
import ta
import time

FINNHUB_API_KEY = "d0noj91r01qn5ghl2c3gd0noj91r01qn5ghl2c40"  # ← 請改為你的 Finnhub API 金鑰

tickers = ['XOM', 'MO', 'T', 'AAPL', 'BEN', 'AMD', 'DOW']
rsi_threshold = 30
result_rows = []

def get_recent_eps(symbol, event_date):
    url = f"https://finnhub.io/api/v1/stock/earnings?symbol={symbol}&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        try:
            data = response.json()
            for record in data:
                report_date = pd.to_datetime(record['period'])
                if report_date <= event_date:
                    return record.get('actual'), record.get('estimate')
        except Exception as e:
            print(f"解析 EPS 失敗: {e}")
    else:
        print(f"EPS API 錯誤: {response.status_code} - {response.text}")
    return None, None

for ticker in tickers:
    data = yf.download(ticker, period="10y", interval="1d")
    if data.empty or 'Close' not in data.columns:
        continue

    close_series = data['Close'].squeeze()
    data['RSI'] = ta.momentum.RSIIndicator(close=close_series, window=14).rsi()
    data.dropna(inplace=True)

    for i in range(1, len(data) - 30):
        rsi_prev = data['RSI'].iloc[i - 1]
        rsi_now = data['RSI'].iloc[i]

        if rsi_prev < rsi_threshold and rsi_now >= rsi_threshold:
            event_date = data.index[i]
            closing_prices = close_series.iloc[i:i + 31].tolist()
            if len(closing_prices) < 31:
                continue

            price_day0 = closing_prices[0]
            price_day30 = closing_prices[30]
            pct_change = ((price_day30 - price_day0) / price_day0) * 100

            actual_eps, est_eps = get_recent_eps(ticker, event_date)
            time.sleep(1)  # 控制 API 頻率

            row = {
                'Ticker': ticker,
                'EventDate': event_date.strftime('%Y-%m-%d'),
                'RSI': round(rsi_now, 2),
                'Reported_EPS': actual_eps,
                'Estimated_EPS': est_eps,
                'Price_Day0': round(price_day0, 2),
                'Price_Day30': round(price_day30, 2),
                'PctChange_30Days': round(pct_change, 2)
            }
            row.update({f'Day{j}': round(closing_prices[j], 2) for j in range(31)})
            result_rows.append(row)

# 匯出 CSV
df = pd.DataFrame(result_rows)
df.to_csv("rsi_crossover_with_eps.csv", index=False)
print("✅ 已儲存 rsi_crossover_with_eps.csv")
