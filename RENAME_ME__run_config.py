'''

************************************************************************************************************
************ Copy this file rename_me_run_config.py to run_config.py before adding your info ***************
************************************************************************************************************


Create an API key/secret from https://www.binance.com/en/my/settings/api-management with only Enable Reading
one per account/sub
'''

Binance_APIs = [
    {
         'account_name': 'Binance Futures - Main'
        ,'Binance_API_KEY': 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
        ,'Binance_API_SECRET': 'BBBBBBBBBBBBBBBBBBBBBBBB'
        # Optional argument name and value to override command line ones if multiple flags are used.
        ,'dry': True
        ,'stop_at': 1.0
        ,'start_at': 0.75
        ,'bots_per_position_ratio': 5
        ,'my_top_pairs': ['BTC','STORJ','DODG']
        ,'no_short': True
    }
    ,{
         'account_name': 'Binance Futures - Sub 01'
        ,'Binance_API_KEY': ''
        ,'Binance_API_SECRET': ''
    }
]



'''
Create an API key/secret from https://3commas.io/api_access_tokens/new with BotsRead, BotsWrite, and AccountsRead
'''
TCommas_API_KEY = ''
TCommas_API_SECRET = ''



'''
Optional
'''
#ifttt_url = ''

