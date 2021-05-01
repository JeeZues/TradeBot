# TradeBot

## Goal

The goal here is to maximize the amount of positions you have while maintaining your safety levels when using Block Party Future Sniper bot with Binance Futures in 3Commas.
We do this by creating way more bots than we need and starting/stopping them as needed to get to the optimal positions count for the account.
E.g. for a $5000 account, assuming you want $500 per position, you will need 10 positions opened.  With 10 bots you will mostly stay under than number.
Here we add more bots and once we get to the 10 positions, we stop all the other bots.  We restart them (~in order of profitability based on history) once we drop bellow targetted positions.


## Quick start
### by Issac
https://docs.google.com/document/d/18KG07spAS0_U8_APbUrIylvPIz4FORjKenITaJZE67Q/view



## Disclaimer
Use this at your own risk.  There are inherent risks in bot trading and in adding this layer of automation on top of it.  I'm not responsible for anything :)
This is still work in progress, consider an Alpha release...


## Usage

- Run main program:
```
python3 run.py --show_all --beep --colors --auto --keep_running --stop_at 2 --bot_start_bursts 1 --bots_per_position_ratio 2 --pair_allowance 375 --binance_account_flag "Main"
```

- Run backup script on another machine/network:
```
nohup python3 run.py --colors --auto --pair_allowance 240 --keep_running --stop_at 2.5 --keep_running_timer 1800 --safe --binance_account_flag "Main" &
tail -f nohup.out
```


### If you find this useful, Buy me a Bubly
```
ETH: 0xce998ec4898877e17492af9248014d67590c0f46
BTC: 1BQT7tZxStdgGewcgiXjx8gFJAYA4yje6J
```

