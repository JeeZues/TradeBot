#!/usr/bin/env python


from binance_api import Binance
from tcommas_api import API3Commas
from utils import *
from pprint import pprint
import argparse
import sys
import time
import run_config
from datetime import datetime
from time import gmtime, strftime
import signal

#----------------------------------





parser = argparse.ArgumentParser()


parser.add_argument("--binance_account_flag", help='Part of binance account name identifier', default="Futures")
parser.add_argument("--debug", help='debug', action='store_true', default=None)

args = parser.parse_args()
#----------------------------------


account_id, account_txt = getAccountID(args.binance_account_flag)
print (account_txt)
print ("-------------------------------------------------------------")


chunks = 100
count = 0
bots = []
while True:
    tbots=get3CommasAPI().getBots(OPTIONS=f"?limit={chunks}&offset={chunks*count}")
    count += 1
    if len(tbots) > 0:
        bots.extend(tbots)
    else:
        break

print(list_bot_pairs(bots, account_id, "long"))
print("--------------------")
print(list_bot_pairs(bots, account_id, "short"))
print("--------------------")


#----------------------------------
