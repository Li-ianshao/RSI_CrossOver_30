from flask import Flask, render_template, request, jsonify
import yfinance as yf
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)


def get_sp500_tickers():
	url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
	df = pd.read_html(url)[0]
	tickers = df['Symbol'].tolist()
	tickers = [t.replace('.', '-') for t in tickers]
	return tickers

def getAristocrats():
	resp = requests.get('https://en.wikipedia.org/wiki/S%26P_500_Dividend_Aristocrats')
	soup = bs.BeautifulSoup(resp.text, 'lxml')

	table = soup.find('table', {'class': 'wikitable sortable'})

	tickers = []

	for row in table.findAll('tr')[1:]:
		ticker = row.findAll('td')[1].text.rstrip()
		tickers.append(ticker)

	return tickers

aristocrats = getAristocrats()
SNP500 = get_sp500_tickers()
stocks.sort()

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



