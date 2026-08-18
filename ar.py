
import json
import bs4 as bs
import requests

def getAristocrats():
	resp = requests.get('https://en.wikipedia.org/wiki/S%26P_500_Dividend_Aristocrats')
	soup = bs.BeautifulSoup(resp.text, 'lxml')

	table = soup.find('table', {'class': 'wikitable sortable'})

	tickers = []

	for row in table.findAll('tr')[1:]:
		ticker = row.findAll('td')[1].text.rstrip()
		tickers.append(ticker)

	return tickers


tickers = getAristocrats()
print(tickers)