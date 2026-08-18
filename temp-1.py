import yfinance as yf
import pandas as pandas

stock = 'AAPL'

ticker = yf.Ticker(stock)
df = ticker.history(period="3mo")

#df = df.dropna()

#df['Surprise(%)'] = round(df['Surprise(%)'] * 100,1)

print(df)
