#!/usr/bin/env python

from pprint import pprint
import requests
import argparse



#----------------------------------
'''
Usage:-

- Run main program:
time python3 


Notes:-

- 


ToDo:-

- 


XYZ:-


https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing?start=1&limit=3&sortBy=market_cap&sortType=desc&convert=USD,btc,eth&cryptoType=all&tagType=all&aux=ath,atl,high24h,low24h,num_market_pairs,cmc_rank,date_added,tags,platform,max_supply,circulating_supply,total_supply,volume_7d,volume_30d


https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing?start=1&limit=3&sortBy=market_cap&sortType=desc&convert=USD&cryptoType=all&tagType=all&aux=high24h,low24h,num_market_pairs,cmc_rank,date_added,tags,platform,max_supply,circulating_supply,total_supply,volume_7d,volume_30d


'''
#----------------------------------


parser = argparse.ArgumentParser()



parser.add_argument("--max", help='Max number pairs to return', type=int, default=30)
parser.add_argument("--csv", help='CSV output format', action='store_true', default=None)
parser.add_argument("--debug", help='debug', action='store_true', default=None)

args = parser.parse_args()


start = 1
limit = 30
max_limit = args.max

#----------------------------------

def getCryptoCurrencyList(start, limit):
    #url = f"https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing?start={start}&limit={limit}&sortBy=market_cap&sortType=desc&convert=USD,btc,eth&cryptoType=all&tagType=all&aux=ath,atl,high24h,low24h,num_market_pairs,cmc_rank,date_added,tags,platform,max_supply,circulating_supply,total_supply,volume_7d,volume_30d"
    url = f"https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing?start={start}&limit={limit}&sortBy=market_cap&sortType=desc&convert=USD&cryptoType=all&tagType=all&aux=high24h,low24h,num_market_pairs,cmc_rank,date_added,tags,platform,max_supply,circulating_supply,total_supply,volume_7d,volume_30d"

    headers = {}
    response = requests.request(
        method="GET", 
        url=url, 
        headers=headers)
    return response.json()['data']['cryptoCurrencyList']


def getFullCryptoCurrencyList(start, limit, max_limit):
    fullCryptoCurrencyList = []
    while (True):
        CryptoCurrencyList = getCryptoCurrencyList(start, limit)
        if len(CryptoCurrencyList) <= 0 or start >= max_limit:
            break
        for cryptoCurrency in CryptoCurrencyList:
            usd_price = 0.0
            usd_fullyDilluttedMarketCap = 0.0
            usd_marketCap = 0.0
            usd_percentChange1h = 0.0
            usd_percentChange24h = 0.0
            usd_percentChange7d = 0.0
            usd_percentChange30d = 0.0
            usd_percentChange90d = 0.0
            usd_volume24h = 0.0
            usd_ytdPriceChangePercentage = 0.0
            for quote in cryptoCurrency['quotes']:
                if quote['name'] == 'USD':
                    usd_price = quote['price']
                    usd_fullyDilluttedMarketCap = quote['fullyDilluttedMarketCap']
                    usd_marketCap = quote['marketCap']
                    usd_percentChange1h = quote['percentChange1h']
                    usd_percentChange24h = quote['percentChange24h']
                    usd_percentChange7d = quote['percentChange7d']
                    usd_percentChange30d = quote['percentChange30d']
                    usd_percentChange90d = quote['percentChange90d']
                    usd_volume24h = quote['volume24h']
                    usd_ytdPriceChangePercentage = quote['ytdPriceChangePercentage']
            coin = { 'symbol': cryptoCurrency['symbol']
                    ,'name': cryptoCurrency['name']
                    ,'totalSupply': cryptoCurrency['totalSupply']
                    ,'circulatingSupply': cryptoCurrency['circulatingSupply']
                    ,'low24h': cryptoCurrency['low24h']
                    ,'high24h': cryptoCurrency['high24h']
                    ,'dateAdded': cryptoCurrency['dateAdded']
                    ,'usd_price': usd_price
                    ,'usd_fullyDilluttedMarketCap': usd_fullyDilluttedMarketCap
                    ,'usd_marketCap': usd_marketCap
                    ,'usd_percentChange1h': usd_percentChange1h
                    ,'usd_percentChange24h': usd_percentChange24h
                    ,'usd_percentChange7d': usd_percentChange7d
                    ,'usd_percentChange30d': usd_percentChange30d
                    ,'usd_percentChange90d': usd_percentChange90d
                    ,'usd_volume24h': usd_volume24h
                    ,'usd_ytdPriceChangePercentage': usd_ytdPriceChangePercentage
                    ,'cmcRank': cryptoCurrency['cmcRank']

                    }
            fullCryptoCurrencyList.append(coin)
        start = start + limit
    return fullCryptoCurrencyList[:max_limit]



def showFullCryptoCurrencyList(start, limit, max_limit):
    txt = ""
    fullCryptoCurrencyList = getFullCryptoCurrencyList(start, limit, max_limit)
    if args.csv:
        txt += f"Symbol,Rank,Price,24h Change,7d Change,Market Cap,24h Volume,Circulating Supply,Name\n"
    else:
        txt += f"{'Sym':4} {'Rank':4} {'Price':10} {'24h%':5} {'7d%':6} {'Market Cap':18} {'Volume (24h)':16} {'Circulating Supply (Name)'}\n"
    for ac in fullCryptoCurrencyList:
        if args.csv:
            txt += f"{ac['symbol']},{ac['cmcRank']},{ac['usd_price']},{ac['usd_percentChange24h']},{ac['usd_percentChange7d']},{ac['usd_marketCap']},{ac['usd_volume24h']},{ac['circulatingSupply']},{ac['name']}\n"
        else:
            txt += f"{ac['symbol']:5} {ac['cmcRank']:3} ${ac['usd_price']:9,.2f} {ac['usd_percentChange24h']:>4.1f}% {ac['usd_percentChange7d']:>5.1f}% ${ac['usd_marketCap']:17,.0f} ${ac['usd_volume24h']:15,.0f} {ac['circulatingSupply']:,.0f} ({ac['name']})\n"
    return txt[:-1]

#----------------------------------
#----------------------------------
#----------------------------------


print(showFullCryptoCurrencyList(start, limit, max_limit))


#----------------------------------
