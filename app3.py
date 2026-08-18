from flask import Flask, render_template, request, jsonify
import yfinance as yf
import pandas as pd
from new_stock_functions import *
import warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)

# All stocks considered
Other_stocks = ['CL', 'HAS', 'IP', 'AAP', 'LEG', 'WU', 'XRX', 'KSS', 'JWN', 
		'DOW', 'CVX', 'SHEL', 'XOM', 'ENPH', 'ENBP', 'BP', 'EQNR', 'ET', 'KMI', 'TTE', 'O', 'FUTU', 'MO', 'T', 'VTRS']

targets = {'ENPH':105.0, 'FUTU':56.0, 'VTRS':10.8, 'ET': 13.0, 'KMI':16.0, 'T':15, 'IBM':150.0, 'MO':42.0, 'MSFT':320.0, 'AAPL':150.0}

aristocrats = getAristocrats()
SNP500 = sp500_tickers()

stocks = SNP500 + Other_stocks
stocks = list(set(stocks))  # remove duplicates
stocks = list(map(lambda x: x.replace('.', '-'), stocks)) # e.g. BRK.B, BF.B，要改為 BRK-B, BF-B 才讀得到交易資料

try:
	stocks.remove('SW')
except Exception as e:
	print('SW not existed')

# testing only
#stocks = ['XOM', 'ENPH', 'FUTU', 'GL', 'CHTR']


stocks.sort()
#print(stocks)
no_of_stocks = len(stocks)

# parameters 
threshold = 30.0  # 過濾門檻值
threshold_day = 15.0 #每日帳跌幅門檻

target_text = ''

for x in targets:
	target_text = target_text + x + ":$" + str(targets[x]) + " | "

@app.route('/')
def stock_info():
	print(target_text)
	ticker = request.args.get('ticker')

	if ticker == None:
		start = time.time()

		no_dec_stocks, dec_output, no_inc_stocks, inc_output, no_dayDec_stocks, dayDec_output, targets_reached = getOutputs(stocks, threshold, SNP500, aristocrats, threshold_day, targets)

		end = time.time()
		print(f'主機運算耗時：{round(end - start,2)} 秒')
		return render_template('stock_info_app3.html', 
			threshold_day=threshold_day, threshold=threshold, no_of_stocks=no_of_stocks, 
			data=dec_output, no_dec_stocks = no_dec_stocks,
			data2=inc_output, no_inc_stocks = no_inc_stocks,
			data3=dayDec_output, no_dayDec_stocks = no_dayDec_stocks,
			data4 = targets_reached, text = target_text)
	else:
		data = getTickerInfo(ticker, SNP500, aristocrats)

		return render_template('stock_info_app3_2.html', data = data)


if __name__ == '__main__':
      app.run(host='0.0.0.0', port=8088, debug=True)



