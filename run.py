#!/usr/bin/env python

import importlib.util
from python_binance.binance.client import Client # From https://github.com/sammchardy/python-binance/
from tcommas_api import API3Commas
from utils import *
from pprint import pprint
import argparse
import sys
import time
from datetime import datetime, timedelta
from time import gmtime, strftime
import signal
import os
import traceback
if os.name == 'nt':
    from timeout_win import timeout
else:
    from timeout import timeout

#----------------------------------
'''

Goal:-

The goal here is to maximize the amount of positions you have while maintaining your safety levels when using Block Party Future Sniper bot with Binance Futures in 3Commas.
We do this by creating way more bots than we need and starting/stopping them as needed to get to the optimal positions count for the account.
E.g. for a $5000 account, assuming you want $500 per position, you will need 10 positions opened.  With 10 bots you will mostly stay under than number.
Here we add more bots and once we get to the 10 positions, we stop all the other bots.  We restart them (~in order of profitability based on history) once we drop bellow targetted positions.



If you find this useful, buy me a snack:-
ETH: 0xce998ec4898877e17492af9248014d67590c0f46
BTC: 1BQT7tZxStdgGewcgiXjx8gFJAYA4yje6J
LTC: LbG7p6AFCjYy8k7gBsNmwuYdUYR9QkNR65
XTZ: tz1RvdxsdqQd1Udpugjb6qCP9wYJULLQk1DB



Disclaimer:-
Use this at your own risk.  There are inherent risks in bot trading and in adding this layer of automation on top of it.  I'm not responsible for anything :)
This is still work in progress.


Usage:-

- Run main program:

python3 run.py --show_all --beep --colors --auto --report --do_transfer --keep_running --stop_at 1.0 --start_at 0.75 --signal_top_pairs_rnd 20 --binance_account_flag ALL_SUBS


- On a 2 seperate machines, run safe mode in case main one gets killed so this one can stop all bots if things go wrong:

nohup python3 run.py --show_deals --colors --auto --keep_running --stop_at 2.5 --start_at 1.0 --bots_per_position_ratio 4 --keep_running_timer 2400 --pair_allowance 350 --no_start --binance_account_flag ALL_SUBS &
tail -33f nohup.out





Notes:-

- Make sure run_config.py has your 3commas names for accounts, --binance_account_flag to specify part of name that uniqly identifies the account

- Add 'do not start' to the name of the bots you do not want to start automatically

- To set up SMS notification when Margin Ratio is critical add to config file
    ifttt_url = 'https://maker.ifttt.com/trigger/Event_Name/with/key/xyz'
    and set up IFTTT webhook to SMS link



ToDo:-

*** - in deal/position match on ID and not just pair name in case 3commas has a stuck deal...
    - no id for positions to match to
        - Check if we have 2 deals with same pair and show error...

- Check BTC max price in past hour and increase/reduce bots based on that...

- Consider converting it into a webservice...

- allow to select fields to show in deals/positions, use current as default

- switch to returning list of dict for show functions

- also return list of pairs with zero SO, init at [], if in list, then show error...



- make bots_per_position_ratio dynamic based on how many positions needed...
    - delta/target * bots_per_position_ratio

- Detect if deals have more than one of the same pair (S/L)

- if error and +ve profit, sell at market (not currently working)

- Need to consider multiplier when starting/stopping bots an counting them, not just for positions as now

- generate stats on deals history per pair (how much, multiplier, how long, add short and long, $/hr, etc)

- Add notification through email or Google Home? (IFTTT is done for MR >= critical)

- Allow hardcoded Generate list of pairs sorted by first to start.


'''
#----------------------------------


parser = argparse.ArgumentParser()


parser.add_argument("--dry", help='Dry run, do not start/stop bots', action='store_true', default=None)
parser.add_argument("--auto", help='Auto Stop/Start bots based on Margin Ratio', action='store_true', default=None)
parser.add_argument("--stop_at", help='Stop bots when Margin Ratio >= value', type=float, default=2.5)
parser.add_argument("--start_at", help='Start bots when Margin Ratio <= value', type=float, default=1.5)
parser.add_argument("--bot_start_bursts", help='Number of bots to start each time', type=int, default=3)
parser.add_argument("--bots_per_position_ratio", help='Open a max number of bots ratio for each needed position', type=int, default=3)
parser.add_argument("--binance_account_flag", help='A list of binance partial account names identifiers, use optional ALL_SUBS', nargs='+', default=["Main"])
parser.add_argument("--randomize_bots", help='Select pairs/bots to start in random order', action='store_true', default=None)

parser.add_argument("--no_short", help='Do not start bots with short strategy, only start long', action='store_true', default=None)

parser.add_argument("--show_all", help='Show all info', action='store_true', default=None)
parser.add_argument("--show_positions", help='Show current open positions', action='store_true', default=None)
parser.add_argument("--show_bots", help='Show bots details', action='store_true', default=None)
parser.add_argument("--show_deals", help='Show deals details', action='store_true', default=None)
parser.add_argument("--pair_allowance", help='How much money each pair is allowed, default is $500.00 (agg is $250)', type=float, default=500.0)

parser.add_argument("--do_transfer", help='Transfer runds out from Futures to spot when limit reached.  API key will need Futures permissions', action='store_true', default=None)
parser.add_argument("--transfer_at", help='Transfer when balance is over ammount (default: $5000)', type=float, default=5000.0)
parser.add_argument("--transfer_delta", help='Wait for balance delta before transfering (default: $50)', type=float, default=50.0)

parser.add_argument("--beep", help='Beep when issues detected', action='store_true', default=None)
parser.add_argument("--colors", help='Add colors if system supports it', action='store_true', default=None)

parser.add_argument("--my_top_pairs", help="A list of pairs ordered from best down, e.g. --pairs EOS ENJ AXS", nargs='+', default=None)
parser.add_argument("--signal_top_pairs", help='Use signal count from BlockParty to order pairs (optional min or max to sory by profit percent)',type=str, nargs='?', const="by_count", default=None)
parser.add_argument("--signal_top_pairs_rnd", help='Use signal count from BlockParty to order pairs and randomize first n', type=int)

parser.add_argument("--keep_running", help='Loop forever (Ctrl+c to stop)', action='store_true', default=None)
parser.add_argument("--keep_running_timer", help='Time to sleep between runs in seconds (default 60)', type=int, default=60)
parser.add_argument("--keep_running_dynamic_timer", help='Adjust timer based on state to reduce load on APIs', action='store_true', default=None)
parser.add_argument("--no_start", help='Run in safe mode (as a backup) with different values to make sure to stop (and not start) bots', action='store_true', default=None)

# Dynamic TTP args
parser.add_argument("--enable_dynamic_ttp", help='Enable dynamically altering TTP for deals with at least (default) 5 SOs...', action='store_true', default=None)
parser.add_argument("--dynamic_ttp_so_trigger", help='SO to trigger dynamica TTP (default: 5)', type=int, default=5)
parser.add_argument("--dynamic_ttp", help='TTP to set dynamica TTP to (default: 1.0)', type=float, default=1.0)
parser.add_argument("--default_ttp", help='default TTP for bots, if is different, not dynamic TTP will be altered (default: 0.42)', type=float, default=0.42)


parser.add_argument("--report", help='Log summary report of each account', action='store_true', default=None)
parser.add_argument("--summary", help='Log summary report of all accounts', action='store_true', default=None)


parser.add_argument("--config_filename", help='Use custom config file (default is run_config.py)', default="run_config.py")

#parser.add_argument("--full_auto", help='Comming soon...Maybe!', action='store_true', default=None)

parser.add_argument("--debug", help='debug', action='store_true', default=None)
parser.add_argument("--verbose", help='Verbose output', action='store_true', default=None)

args = parser.parse_args()

# Allow importing run_config from different locations using path
spec = importlib.util.spec_from_file_location("module.name", args.config_filename)
run_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_config)
#pprint(run_config)
#print(run_config.Binance_APIs)


if args.start_at >= args.stop_at:
    print("Error: start_at can't be more than or equal to stop_at")
    exit(1)
'''
enable_dynamic_ttp = None
if args.enable_dynamic_ttp:
    enable_dynamic_ttp['dynamic_ttp_so_trigger'] = args.dynamic_ttp_so_trigger
    enable_dynamic_ttp['dynamic_ttp'] = args.dynamic_ttp
    enable_dynamic_ttp['default_ttp'] = args.default_ttp
'''
#----------------------------------

beep_time = 10

if args.colors:
    ENDC   = '\033[0m'
    RED    = '\033[91m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    BLINK  = '\033[5m'
    BOLD   = '\033[1m'
else:
    ENDC   = ''
    RED    = ''
    GREEN  = ''
    YELLOW = ''
    BLINK  = ''
    BOLD   = ''

sig_top_list_ts = datetime.now() - timedelta(hours=10)
signals_list = []

#----------------------------------

do_ifttt = True
try:
    _ = run_config.ifttt_url
except Exception:
    do_ifttt = False

#----------------------------------


#----------------------------------
#----------------------------------
#----------------------------------
#@timing
@timeout(300)
def run_account(account_dict, bots):
    account_id = account_dict['3Commas_Account_ID']
    api_key = account_dict['Binance_API_KEY']
    api_secret = account_dict['Binance_API_SECRET']
    global sig_top_list_ts
    global signals_list
    ret = {}
    ret['output'] = ""
    ret['beep'] = False

    BinanceClient = Client(api_key, api_secret)
    account = BinanceClient.futures_account()
    usdt_spot_total_balance = get_spot_balance(BinanceClient)

    totalMarginBalance = get_totalMarginBalance(account)
    availableBalanceUSDT = get_availableBalance(account, 'USDT')
    if account_dict['debug']:
        print(f"totalMarginBalance = {totalMarginBalance}")
        print(f"availableBalanceUSDT = {availableBalanceUSDT}")
        print(f"usdt_spot_total_balance = {usdt_spot_total_balance}")


    # Tansfer funds from Futures to Spot
    if account_dict['do_transfer']: ##ToDo: should we also check MR?
        if availableBalanceUSDT > account_dict['transfer_at'] + account_dict['transfer_delta']:
            transfer_amount = availableBalanceUSDT - account_dict['transfer_at']
            print(f"Detected balance of ${availableBalanceUSDT:.2f} over transfer limit ${account_dict['transfer_at']}.  Transfering ${transfer_amount:.2f} to spot.")
            if not account_dict['dry']:
                res = BinanceClient.futures_account_transfer(asset = 'USDT', amount = transfer_amount, type = 2)
                print(res)
                account = BinanceClient.futures_account()
                totalMarginBalance = get_totalMarginBalance(account)

    margin_ratio = get_margin_ratio(account)

    # Show bot table
    if account_dict['show_bots'] or account_dict['show_all']:
        try:
            print(show_bots(bots, account_id))
            print("--------------------")
        except Exception as e:
            print(e)
            traceback.print_exc()
            pass

    # Start/Stop Bots
    if account_dict['auto']:

        strategy = ["long", "short"]
        if account_dict['no_short']:
            strategy = ["long"]

        # Get top list of pairs
        top_list = []
        if account_dict['my_top_pairs']:
            top_list = account_dict['my_top_pairs']
        if account_dict['signal_top_pairs'] or account_dict['signal_top_pairs_rnd']:
            if sig_top_list_ts <= datetime.now() - timedelta(hours=3): # Update signal top list every hour
                signals_list, sig_top_list_ts = get_bot_signals()
            if str(account_dict['signal_top_pairs']).lower() in ["min", "max"]:
                sig_top_list = get_pairs_with_top_signals_by_profit(signals_list, profit_indicator = account_dict['signal_top_pairs'].lower())
            else:
                sig_top_list = get_pairs_with_top_signals(signals_list)
            top_list.extend(sig_top_list)
        if account_dict['signal_top_pairs_rnd']:
            top_list_rnd = top_list[:account_dict['signal_top_pairs_rnd']]
            random.shuffle(top_list_rnd)
            top_list = top_list_rnd + top_list[account_dict['signal_top_pairs_rnd']:]

        top_list = remove_duplicates_from_list(top_list)
        if account_dict['debug']:
            print(f"###################")
            print(f"{top_list}")
            print(f"###################")

        # Collect info...
        totalMaintMargin = get_totalMaintMargin(account)
        max_bot_pairs = get_max_bot_pairs(totalMarginBalance, account_dict['pair_allowance'])
        total_bot_pair_count, active_bot_pair_count, dns_bot_pair_count = get_bot_pair_count(bots, account_id)
        active_positions_count = get_active_positions_count(account['positions'], bots, account_id)
        stopped_bots_with_positions = get_stopped_bots_with_positions(bots, account_id, account['positions'])
        started_bots_with_positions = get_started_bots_with_positions(bots, account_id, account['positions'])
        bots_pairs_to_start = round(max_bot_pairs - active_positions_count)
        max_bots_running = (bots_pairs_to_start * account_dict['bots_per_position_ratio']) + len(started_bots_with_positions) #dynamic_bots_per_position_ratio
        start_up_to_bots = max_bots_running - active_bot_pair_count + active_positions_count
        start_up_to_bots = 0 if start_up_to_bots <= 0  else start_up_to_bots
        started_bots_without_positions = get_started_bots_without_positions(bots, account_id, account['positions'], top_list)
        count_of_started_bots_without_positions = len(started_bots_without_positions)
        need_to_stop = active_bot_pair_count - max_bots_running
        if account_dict['debug']:
            print (f"\tmargin_ratio = {margin_ratio}")
            print (f"\ttotalMaintMargin = {totalMaintMargin}")
            print (f"\tmax_bot_pairs = {max_bot_pairs}")
            print (f"\ttotal_bot_pair_count = {total_bot_pair_count}")
            print (f"\tactive_bot_pair_count = {active_bot_pair_count}")
            print (f"\tdns_bot_pair_count = {dns_bot_pair_count}")
            print (f"\tactive_positions_count = {active_positions_count}")
            print (f"\taccount_dict['bots_per_position_ratio'] = {account_dict['bots_per_position_ratio']}")
            print (f"\tbots_pairs_to_start = {bots_pairs_to_start}")
            print (f"\tmax_bots_running = {max_bots_running}")
            print (f"\tstart_up_to_bots = {start_up_to_bots}")
            print (f"\tcount_of_started_bots_without_positions = {count_of_started_bots_without_positions}")
            print (f"\tneed_to_stop = {need_to_stop}")
            print (f"\tlen(stopped_bots_with_positions) = {len(stopped_bots_with_positions)}")
            print (f"\tlen(started_bots_with_positions) = {len(started_bots_with_positions)}")
            
            print (f"\t\tPositions target({round(max_bot_pairs)}) - running ({active_positions_count}) = delta ({bots_pairs_to_start})")
            print (f"\t\tBots running ({active_bot_pair_count})")
            print (f"\t\tBots running with positions ({len(started_bots_with_positions)})")

        print(f"Margin Balance = ${totalMarginBalance:<.2f} (${totalMaintMargin:<.2f}) : USDT Furures (Spot) = ${availableBalanceUSDT:<.2f} $({usdt_spot_total_balance:<.2f})")
        print(f"Bots Active/Total: {active_bot_pair_count}/{total_bot_pair_count} ({dns_bot_pair_count} dns)")
        print(f"Positions delta ({bots_pairs_to_start}) = target ({round(max_bot_pairs)}) - running ({active_positions_count})")

        ret['Margin Balance'] = f"Margin Balance = ${totalMarginBalance:<.2f} (${totalMaintMargin:<.2f}) : USDT Furures (Spot) = ${availableBalanceUSDT:<.2f} $({usdt_spot_total_balance:<.2f})"
        ret['Bots Active/Total'] = f"Bots Active/Total: {active_bot_pair_count}/{total_bot_pair_count} ({dns_bot_pair_count} dns)"
        ret['Positions delta'] = f"Positions delta ({bots_pairs_to_start}) = target ({round(max_bot_pairs)}) - running ({active_positions_count})"
        
        ret['summary'] = f"MR = {margin_ratio:0.2f}% - {ret['Bots Active/Total']} - target ({round(max_bot_pairs)}) - running ({active_positions_count})"

        if margin_ratio >= account_dict['stop_at']: # If MR is larger than or equals stop at, stop all bots...
            print(f"{RED}High margin ratio, stopping bots...{ENDC}")
            ret['output'] += f"{RED}High margin ratio, stopping bots...{ENDC}\n"
            stop_all_bots(bots, account_id, account_dict['dry'])
            if do_ifttt and margin_ratio >= 5: # Or should we check stop_at * 2
                import urllib.request
                ifttt_contents = urllib.request.urlopen(run_config.ifttt_url).read()
                print(ifttt_contents)
        else: # MR is less than stop at
            if bots_pairs_to_start > 0: # need more positions
                if len(stopped_bots_with_positions) > 0:
                    print(f"Starting {len(stopped_bots_with_positions)} stopped bots with active positions...")
                    ret['output'] += f"Starting {len(stopped_bots_with_positions)} stopped bots with active positions...\n"
                    if margin_ratio < account_dict['start_at']:
                        if not account_dict['no_start']:
                            for bot_to_start in stopped_bots_with_positions:
                                print(f"Starting {bot_to_start} bot pairs...")
                                ret['output'] += f"Starting {bot_to_start} bot pairs...\n"
                                start_bot_pair(bots, account_id, bot_to_start, account_dict['dry'], strategy = strategy)
                    else:
                        print(f"{YELLOW}High margin ratio, not starting any bots...{ENDC}")
                        ret['output'] += f"{YELLOW}High margin ratio, not starting any bots...{ENDC}\n"
                else: # no stopped bots with positions to start, start from ones without active positions
                    if account_dict['verbose']: print (f"Need to have a max of {max_bots_running} stopped bot pairs...")

                    if active_bot_pair_count > max_bots_running:
                        if account_dict['verbose']:
                            print("Already have too many bots running...")
                        if account_dict['debug']:
                            print(f"max_bots_running = {max_bots_running}")
                            print(f"active_bot_pair_count = {active_bot_pair_count}")
                            print(f"started_bots_without_positions = {started_bots_without_positions}")
                            print(f"count_of_started_bots_without_positions = {count_of_started_bots_without_positions}")
                        if account_dict['debug']:
                            print(f"need_to_stop = {need_to_stop}")
                        if account_dict['verbose']:
                            print(f"Need to stop {need_to_stop} extra bot pairs...")
                        if count_of_started_bots_without_positions > 0:
                            stop_list = started_bots_without_positions[:need_to_stop]
                            print("Stopping extra bots...")
                            ret['output'] += "Stopping extra bots...\n"
                            for bot_to_stop in stop_list:
                                print(f"Stopping {bot_to_stop} bot pairs...")
                                ret['output'] += f"Stopping {bot_to_stop} bot pairs...\n"
                                stop_bot_pair(bots, account_id, bot_to_stop, account_dict['dry'])
                        else:
                            print("nothing to stop")
                            ret['output'] += "nothing to stop\n"
                    elif active_bot_pair_count == max_bots_running:
                        print ("No change to number of bots running needed...")
                        ret['output'] += "No change to number of bots running needed...\n"
                    else:
                        max_bots_running = max_bots_running - count_of_started_bots_without_positions
                        if account_dict['randomize_bots']:
                            stopped_bots_without_positions = get_stopped_bots_without_positions_random(bots, account_id, account['positions'], top_list)
                        else:
                            stopped_bots_without_positions = get_stopped_bots_without_positions(bots, account_id, account['positions'], top_list)
                        if account_dict['debug']:
                            print("Pick min from:")
                            print(f"max_bots_running = {max_bots_running}")
                            print(f"account_dict['bot_start_bursts'] = {account_dict['bot_start_bursts']}")
                            print(f"len(stopped_bots_without_positions) = {len(stopped_bots_without_positions)}")
                            print(f"max_bots_running = {max_bots_running}")
                            print(f"start_up_to_bots = {start_up_to_bots}")
                        actual_bots_to_start = min(max_bots_running, 
                                                account_dict['bot_start_bursts'], 
                                                len(stopped_bots_without_positions), 
                                                max_bots_running, 
                                                start_up_to_bots)
                        actual_bots_to_start = 0 if actual_bots_to_start <= 0 else actual_bots_to_start # Make sure it's not a negative number

                        if not account_dict['no_start']:
                            if margin_ratio < account_dict['start_at']:
                                print (f"Incrementally starting {actual_bots_to_start} stopped bots without positions...")
                                ret['output'] += f"Incrementally starting {actual_bots_to_start} stopped bots without positions...\n"
                                burst_pairs_to_start = stopped_bots_without_positions[:actual_bots_to_start] # Assume list is sorted
                                for bot_to_start in burst_pairs_to_start:
                                    print(f"Starting {bot_to_start} bot pairs...")
                                    ret['output'] += f"Starting {bot_to_start} bot pairs...\n"
                                    start_bot_pair(bots, account_id, bot_to_start, account_dict['dry'], strategy = strategy)
                            else:
                                print(f"{YELLOW}High margin ratio, not starting any bots...{ENDC}")
                                ret['output'] += f"{YELLOW}High margin ratio, not starting any bots...{ENDC}\n"

            elif bots_pairs_to_start < 0: # running too much positions
                if account_dict['no_start']:
                    print("High positions count, stopping all running bots...")
                    ret['output'] += "High positions count, stopping all running bots..."
                    stop_all_bots(bots, account_id, account_dict['dry'])
                else:
                    print(f"High positions count, stopping {len(started_bots_without_positions)} bots without positions")
                    ret['output'] += f"High positions count, stopping {len(started_bots_without_positions)} bots without positions\n"
                    for bot_to_stop in started_bots_without_positions:
                        print(f"Stopping {bot_to_stop} bot pairs...")
                        ret['output'] += f"Stopping {bot_to_stop} bot pairs...\n"
                        stop_bot_pair(bots, account_id, bot_to_stop, account_dict['dry'])
            else: # the right ammount of positions running
                print("No change to positions count needed...")
                ret['output'] += "No change to positions count needed...\n"
                print(f"Correct positions count, stopping {len(started_bots_without_positions)} bots without positions")
                ret['output'] += f"Correct positions count, stopping {len(started_bots_without_positions)} bots without positions\n"
                for bot_to_stop in started_bots_without_positions:
                    print(f"Stopping {bot_to_stop} bot pairs...")
                    ret['output'] += f"Stopping {bot_to_stop} bot pairs...\n"
                    stop_bot_pair(bots, account_id, bot_to_stop, account_dict['dry'])

    # Show Margin Ratio
    color = YELLOW+BLINK
    if margin_ratio >= account_dict['stop_at']:
        color = RED+BLINK+BOLD
    if margin_ratio <= account_dict['start_at']:
        color = GREEN
    print(f"{color}****************************{ENDC}")
    print(f"{color}*** Margin Ratio = {margin_ratio:0.2f}% ***{ENDC}")
    print(f"{color}****************************{ENDC}")
    ret['margin_ratio_txt'] = f"{color}****************************{ENDC}\n{color}*** Margin Ratio = {margin_ratio:0.2f}% ***{ENDC}\n{color}****************************{ENDC}"


    # Show deals/positions table
    if account_dict['show_deals'] or account_dict['show_positions'] or account_dict['show_all']:
        try:
            deals=get3CommasAPI().getDeals(OPTIONS=f"?account_id={account_id}&scope=active&limit=100")
            show_deals_positions_txt, zeroSO = show_deals_positions(deals, account['positions'], account_dict, colors = account_dict['colors'])
            ret['show_deals_positions'] = show_deals_positions_txt
            print(show_deals_positions_txt)
            if "Error" in show_deals_positions_txt:
                ret['beep'] = True
        except Exception as e:
            print(e)
            traceback.print_exc()
            pass

    if account_dict['beep'] and margin_ratio >= account_dict['stop_at']:
        ret['beep'] = True

    ret['margin_ratio'] = margin_ratio
    return ret



#----------------------------------
#----------------------------------
#----------------------------------

signal.signal(signal.SIGINT, signal_handler)
listen()

print ("-----------------------------------------------------------------")
print ("-----------------------------------------------------------------")

accountAPIs = []
found_account = False

try:
    _ = run_config.Binance_APIs
    for Binance_API in run_config.Binance_APIs:
        args_binance_account_flag = []
        if args.binance_account_flag == ['ALL_SUBS']:
            for xBinance_API in run_config.Binance_APIs:
                args_binance_account_flag.append(xBinance_API['account_name'])
        else:
            args_binance_account_flag = args.binance_account_flag
        for binance_account_flag in args_binance_account_flag:
            if binance_account_flag in Binance_API['account_name']:
                found_account = True
                account, account_txt, account_info = getAccountID(Binance_API['account_name'])
                if account == "" or account_txt == "":
                    print("Error: Need to find account before proceeding...")
                    exit(1)

                account_dict = {
                    'account_name': Binance_API['account_name']
                    ,'Binance_API_KEY': Binance_API['Binance_API_KEY']
                    ,'Binance_API_SECRET': Binance_API['Binance_API_SECRET']
                    ,'3Commas_Account_ID': account
                    ,'3Commas_Account_Txt': f"{account_txt}"
                    ,'3Commas_Account_Info': account_info
                    }

                for arg in vars(args):
                    account_dict[arg] = getattr(args, arg)
                    if arg in Binance_API:
                        if Binance_API[arg] != getattr(args, arg):
                            print (f"{Binance_API['account_name']} - Overriding value for {arg} from command line ({getattr(args, arg)}) with one from config file ({Binance_API[arg]})")
                            account_dict[arg] = Binance_API[arg]

                accountAPIs.append(account_dict)
                if args.debug:
                    pprint(account_dict)

except Exception as e:
    print(e)
    traceback.print_exc()
    print("Make sure you have Binance_APIs setup in run_config.py")
    exit(9)

if not found_account:
    print(f"Error: could not find account with flag {args.binance_account_flag}")
    exit(1)


while True:
    keep_running_timer = args.keep_running_timer
    try:
        bots = None
        ret_margin_ratio = []
        ret_beep = False
        if args.auto or args.show_bots or args.show_all:
            bots = get_bots()


        if args.summary:
            with open(f"run_summary.txt", "a") as myfile:
                print (f"-----------------------------------------------------------------", file=myfile)


        for sub_account in accountAPIs:
            print ("-----------------------------------------------------------------")
            print (sub_account['3Commas_Account_Txt'])
            print ("-----------------------------------------------------------------")
            ret = run_account(sub_account, bots)
            ret_margin_ratio.append(ret['margin_ratio'])
            ret_beep = ret['beep'] or ret_beep
            if sub_account['summary']:
                with open(f"run_summary.txt", "a") as myfile:
                    print (f"{sub_account['3Commas_Account_Info']['name']} - {ret['summary']}", file=myfile)
            if sub_account['report']:
                with open(f"run_report_{sub_account['3Commas_Account_ID']}.txt", "a") as myfile:
                    print ("-----------------------------------------------------------------", file=myfile)
                    print (sub_account['3Commas_Account_Txt'], file=myfile)
                    print ("-----------------------------------------------------------------", file=myfile)
                    if args.verbose: print (ret['output'], file=myfile)
                    print (ret['Margin Balance'], file=myfile)
                    print (ret['Bots Active/Total'], file=myfile)
                    print (ret['Positions delta'], file=myfile)
                    print (ret['margin_ratio_txt'], file=myfile)
                    print (ret['show_deals_positions'], file=myfile)
                    if args.dry:
                        print("*************************", file=myfile)
                        print("***Running in DRY mode***", file=myfile)
                        print("*************************", file=myfile)
                    print (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), file=myfile)
        
        if args.summary:
            with open(f"run_summary.txt", "a") as myfile:
                print (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), file=myfile)

        if min(ret_margin_ratio) > sub_account['stop_at'] and args.keep_running_dynamic_timer:
            keep_running_timer *= 3
        sys.stdout.flush()
    except Exception as e:
        print(e)
        traceback.print_exc()
        keep_running_timer = int(args.keep_running_timer/10) + 10
        pass

    if args.dry:
        print("*************************")
        print("***Running in DRY mode***")
        print("*************************")
    sys.stdout.flush()
    if not args.keep_running:
        break
    if args.beep and ret_beep:
        beep(beep_time)
    countdown(keep_running_timer)
    print()
    print ("-----------------------------------------------------------------")

