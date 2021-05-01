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
from timeout import timeout

#----------------------------------
'''


'''
#----------------------------------


parser = argparse.ArgumentParser()


parser.add_argument("--dry", help='Dry run', action='store_true', default=None)
parser.add_argument("--binance_account_flag", help='Part of binance account name identifier', default=None)
parser.add_argument("--all", help='All accounts from config file', action='store_true', default=None)


args = parser.parse_args()
if (args.all and args.binance_account_flag) or (not args.all and not args.binance_account_flag):
    print("Error: Can't use --all flag with --binance_account_flag, need one specified")
    exit(1)

#----------------------------------

def stop_account(account_id, api_key, api_secret):
    account=getBinanceAPI(api_key, api_secret).futuresAccount()

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
    stop_all_bots(bots, account_id, args.dry)


#----------------------------------

print ("-----------------------------------------------------------------")

for Binance_API in run_config.Binance_APIs:
    if args.binance_account_flag and args.binance_account_flag in Binance_API['account_name']:
        account_name = Binance_API['account_name']
        Binance_API_KEY = Binance_API['Binance_API_KEY']
        Binance_API_SECRET = Binance_API['Binance_API_SECRET']
        account, account_txt = getAccountID(account_name)
        print (account_txt)
        stop_account(account, Binance_API_KEY, Binance_API_SECRET)
        print ("-----------------------------------------------------------------")
        break
    elif args.all:
        account_name = Binance_API['account_name']
        Binance_API_KEY = Binance_API['Binance_API_KEY']
        Binance_API_SECRET = Binance_API['Binance_API_SECRET']
        account, account_txt = getAccountID(account_name)
        print (account_txt)
        stop_account(account, Binance_API_KEY, Binance_API_SECRET)
        print ("-----------------------------------------------------------------")


if args.dry:
    print("*************************")
    print("***Running in DRY mode***")
    print("*************************")
sys.stdout.flush()


print ("-----------------------------------------------------------------")

