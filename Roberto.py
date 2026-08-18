import requests
import yfinance as yf
import pandas as pd
import ta
import time

FINNHUB_API_KEY = "d0noj91r01qn5ghl2c3gd0noj91r01qn5ghl2c40"  # <-- 請填入你自己的 API 金鑰

def get_finnhub_eps(symbol):
    url = f"https://finnhub.io/api/v1/stock/earnings?symbol={symbol}&token={FINNHUB_API_KEY}"
    #url = f"https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    print(f"Fetching EPS for {symbol} - Status: {response.status_code}")  # 除錯用
    if response.status_code == 200:
        try:
            data = response.json()
            metric_data = data.get("metric", {})
            trailing_eps = metric_data.get("epsTrailingTwelveMonths")
            forward_eps = metric_data.get("epsForward")
            print(f"{symbol} EPS -> Trailing: {trailing_eps}, Forward: {forward_eps}")  # 除錯
            return trailing_eps, forward_eps
        except Exception as e:
            print(f"Error parsing EPS for {symbol}: {e}")
    else:
        print(f"API Error: {response.text}")
    return None, None

print(get_finnhub_eps("AAPL"))
