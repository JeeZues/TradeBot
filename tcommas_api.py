#!/usr/bin/env python

import time
import json
import urllib
import hmac, hashlib
import requests

from urllib.parse import urlparse, urlencode
from urllib.request import Request, urlopen

class API3Commas():

    methods = {
            'getAccounts': {'url': '/public/api/ver1/accounts', 'method': 'GET'},
            'getBots': {'url': '/public/api/ver1/botsOPTIONS', 'method': 'GET'},
            'getDeals': {'url': '/public/api/ver1/dealsOPTIONS', 'method': 'GET'},
            'getDeal': {'url': '/public/api/ver1/deals/DEAL_ID/showOPTIONS', 'method': 'GET'},
            'panicSellDeal': {'url': '/public/api/ver1/deals/DEAL_ID/panic_sell', 'method': 'POST'},
            'disableBot': {'url': '/public/api/ver1/bots/BOT_ID/disable', 'method': 'POST'},
            'enableBot': {'url': '/public/api/ver1/bots/BOT_ID/enable', 'method': 'POST'},
    }
    
    def __init__(self, API_KEY, API_SECRET):
        self.API_KEY = API_KEY
        self.API_SECRET = bytearray(API_SECRET, encoding='utf-8')
        self.shift_seconds = 0

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            kwargs.update(command=name)
            return self.call_api(**kwargs)
        return wrapper

    def set_shift_seconds(self, seconds):
        self.shift_seconds = seconds
        
    def call_api(self, **kwargs):
        command = kwargs.pop('command')
        url = self.methods[command]['url']
        for k, v in kwargs.items():
            #print(f"{k} {v}")
            url = url.replace(k, v)
        url = url.replace("OPTIONS", "") # When no OPTIONS are passed
        headers = {}
        api_url = 'https://api.3commas.io' + url
        sign = hmac.new(key = self.API_SECRET, msg = str.encode(url), digestmod = hashlib.sha256).hexdigest()
        headers = {'APIKEY': self.API_KEY,
                   'Signature': str(sign)}
        '''
        print("----------------------------------")
        print(f"command = {command}")
        print(f"sign = {sign}")
        print(f"self.API_SECRET = {self.API_SECRET}")
        print(f"url = {url}")
        print(f"api_url = {api_url}")
        print(f"headers = {headers}")
        print(f"self.methods[command]['method'] = {self.methods[command]['method']}")
        print("----------------------------------")
        '''
        response = requests.request(
            method=self.methods[command]['method'], 
            url=api_url, 
            headers=headers)
        if 'code' in response.text:
            #print(response.text)
            pass
        return response.json()

