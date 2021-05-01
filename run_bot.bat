@echo off
set script=%USERPROFILE%"\Desktop\TradeBot-main\run.py"
py %script% --show_all --beep --colors --auto --keep_running --stop_at 2 --bot_start_bursts 1 --bots_per_position_ratio 2 --pair_allowance 375 --binance_account_flag "Main"
