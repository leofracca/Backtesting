from binance.client import Client
from binance.enums import *
import csv
from datetime import datetime


client = Client('api_key', 'api_secret')

candlesticks = client.get_historical_klines('BTCUSDT', Client.KLINE_INTERVAL_15MINUTE, "1 Jan, 2022")

f = open('15min_BTC-USDT.csv', 'w', newline='')
csv_writer = csv.writer(f, delimiter=',')

csv_writer.writerow(['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])

for c in candlesticks:
	r = []
	ts = int(c[0])
	date = datetime.utcfromtimestamp(ts / 1000).strftime('%Y-%m-%d %H:%M:%S')
	r.append(date) # Date
	r.append(c[1]) # Open
	r.append(c[2]) # High
	r.append(c[3]) # Low
	r.append(c[4]) # Close
	r.append(c[5]) # Volume
	csv_writer.writerow(r)

f.close()
