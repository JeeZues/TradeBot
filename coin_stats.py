#!/usr/bin/env python
from collections import Counter

from tcommas_api import API3Commas
from python_binance.binance.client import Client
from utils import *
from pprint import pprint
import argparse
import sys
import time
import run_config
from datetime import datetime
from time import gmtime, strftime
import signal
import os
if os.name == 'nt':
    from timeout_win import timeout
else:
    from timeout import timeout



parser = argparse.ArgumentParser()
parser.add_argument("--coin", help='Coin code', default="BTC")
args = parser.parse_args()

Client = Client()

### Change to get different time ranges and intervals ###
range = "1 day ago UTC" # e.g. "7 days ago UTC", etc.
interval = Client.KLINE_INTERVAL_1HOUR # e.g. Client.KLINE_INTERVAL_1MINUTE, Client.KLINE_INTERVAL_3MINUTE

res = Client.get_historical_klines(f"{args.coin}USDT", interval, range)

l = []
for x in res:
    l.append(xfloat(x[4]))
    print (f"{datetime.utcfromtimestamp(int(x[0])/1000.0).strftime('%Y-%m-%d %H:%M:%S')}\t{xfloat(x[4]):.2f}")

print(f"Record count in {range} with specified interval = {len(l)}")

print(f"Max value = {max(l):.2f}")
print(f"Min value = {min(l):.2f}")
print(f"Delta = {max(l)-min(l):.2f}")

import statistics
print(f"Mean = {statistics.mean(l):.2f}")
print(f"Median low = {statistics.median_low(l):.2f}")
print(f"Median high = {statistics.median_high(l):.2f}")
print(f"Pstdev = {statistics.pstdev(l)}")
print(f"Stdev = {statistics.stdev(l)}")
print(f"Variance = {statistics.variance(l)}")


res = Client.get_avg_price(symbol=f"{args.coin}USDT")
print ("Average price : ")
pprint(res['price'])
