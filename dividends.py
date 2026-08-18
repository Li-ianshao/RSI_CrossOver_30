# 最近配息的股票以及 RSI < 25 的股票
import yfinance as yf
import pandas as pandas
from datetime import datetime

import matplotlib.pyplot as plt

# Other_stocks = ['CL', 'HAS', 'IP', 'AAP', 'LEG', 'WU', 'XRX', 'KSS', 'JWN', 'DOW', 'CVX', 'SHEL', 'XOM', 'ENBP', 'BP', 'ET', 'KMI', 'TTE', 'O', 'MO', 'T', 'VTRS']

print('Enter a symbol:')
s = input()
ticker = yf.Ticker(s)

df = ticker.history(period='max')

#print(df)

dfgb = df.groupby([df.index.year])['Dividends'].sum()

print(dfgb)

dfgb.plot(kind='bar')
plt.title(s)

plt.show()

