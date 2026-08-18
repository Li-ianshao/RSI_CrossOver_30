import yfinance as yf
import pandas as pd
import pprint

ticker = yf.Ticker('FE')

info = ticker.info

#print(info)

pp = pprint.PrettyPrinter(depth=6)
pp.pprint(info)

