#!/usr/bin/env python

import run_config # import settings from run_config.py

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



If you find this useful, Buy me a Bubly:-
ETH: 0xce998ec4898877e17492af9248014d67590c0f46
BTC: 1BQT7tZxStdgGewcgiXjx8gFJAYA4yje6J



Disclaimer:-
Use this at your own risk.  There are inherent risks in bot trading and in adding this layer of automation on top of it.  I'm not responsible for anything :)
This is still work in progress.


Usage:-

- Run main program:
Suggested:
time python3 run.py --show_all --beep --colors --auto --keep_running --stop_at 2 --bot_start_bursts 1 --bots_per_position_ratio 2 --pair_allowance 375 --binance_account_flag "Main"


Actual:

cd ~/Downloads/3CommasAPI/
x time python3 run.py --show_all --beep --colors --auto --keep_running --stop_at 2 --bot_start_bursts 3 --bots_per_position_ratio 3 --keep_running_timer 60 --pair_allowance 500 --binance_account_flag "Main"
x time python3 run.py --show_all --beep --colors --auto --keep_running --stop_at 2 --bot_start_bursts 3 --bots_per_position_ratio 3 --keep_running_timer 65 --pair_allowance 500 --binance_account_flag "Sub 01"
x time python3 run.py --show_all --beep --colors --auto --keep_running --stop_at 2 --bot_start_bursts 3 --bots_per_position_ratio 3 --keep_running_timer 70 --pair_allowance 500 --binance_account_flag "Sub 02"

time python3 run.py --show_all --beep --colors --auto --keep_running --stop_at 1 --start_at 0.75 --bot_start_bursts 2 --bots_per_position_ratio 3 --keep_running_timer 65 --pair_allowance 375 --binance_account_flag "Main"

time python3 run.py --show_all --beep --colors --auto --keep_running --stop_at 1 --start_at 0.75 --bot_start_bursts 2 --bots_per_position_ratio 3 --keep_running_timer 65 --pair_allowance 375 --binance_account_flag "Sub 01"

time python3 run.py --show_all --beep --colors --auto --keep_running --stop_at 1 --start_at 0.75 --bot_start_bursts 2 --bots_per_position_ratio 3 --keep_running_timer 65 --pair_allowance 375 --binance_account_flag "Sub 02" --randomize_bots

- On a 2 seperate machines, run safe mode in case main one gets killed so this one can stop all bots if things go wrong:
nohup python3 run.py --colors --auto --pair_allowance 240 --keep_running --stop_at 2.5 --keep_running_timer 1800 --no_start --binance_account_flag "Main" &
nohup python3 run.py --colors --auto --pair_allowance 240 --keep_running --stop_at 2.5 --keep_running_timer 1800 --no_start --binance_account_flag "Sub 01" &
nohup python3 run.py --colors --auto --pair_allowance 240 --keep_running --stop_at 2.5 --keep_running_timer 1800 --no_start --binance_account_flag "Sub 02" &
tail -f nohup.out




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
parser.add_argument("--start_at", help='Start bots when Margin Ratio <= value', type=float, default=1.5) # not really used currently
parser.add_argument("--bot_start_bursts", help='Number of bots to start each time', type=int, default=3)
parser.add_argument("--bots_per_position_ratio", help='Open a max number of bots ratio for each needed position', type=int, default=3)
parser.add_argument("--binance_account_flag", help='Part of binance account name identifier', default="Main")
parser.add_argument("--randomize_bots", help='Select pairs/bots to start in random order', action='store_true', default=None)

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
parser.add_argument("--signal_top_pairs", help='Use signal count from BlockParty to order pairs', action='store_true', default=None)

parser.add_argument("--keep_running", help='Loop forever (Ctrl+c to stop)', action='store_true', default=None)
parser.add_argument("--keep_running_timer", help='Time to sleep between runs in seconds (default 60)', type=int, default=60)
parser.add_argument("--keep_running_dynamic_timer", help='Adjust timer based on state to reduce load on APIs', action='store_true', default=None)
parser.add_argument("--no_start", help='Run in safe mode (as a backup) with different values to make sure to stop (and not start) bots', action='store_true', default=None)
parser.add_argument("--debug", help='debug', action='store_true', default=None)
parser.add_argument("--verbose", help='Verbose output', action='store_true', default=None)

args = parser.parse_args()

if args.start_at >= args.stop_at:
    print("Error: start_at can't be more than or equal to stop_at")
    exit(1)

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
@timeout(180)
def run_account(account_id, api_key, api_secret):
    global sig_top_list_ts
    ret = {}

    BinanceClient = Client(api_key, api_secret)
    account = BinanceClient.futures_account()
    usdt_spot_total_balance = get_spot_balance(BinanceClient)

    totalMarginBalance = get_totalMarginBalance(account)
    availableBalanceUSDT = get_availableBalance(account, 'USDT')
    if args.debug:
        print(f"totalMarginBalance = {totalMarginBalance}")
        print(f"availableBalanceUSDT = {availableBalanceUSDT}")
        print(f"usdt_spot_total_balance = {usdt_spot_total_balance}")


    # Tansfer funds from Futures to Spot
    if args.do_transfer: ##ToDo: should we also check MR?
        if availableBalanceUSDT > args.transfer_at + args.transfer_delta:
            transfer_amount = availableBalanceUSDT - args.transfer_at
            print(f"Detected balance of ${availableBalanceUSDT:.2f} over transfer limit ${args.transfer_at}.  Transfering ${transfer_amount:.2f} to spot.")
            if not args.dry:
                res = BinanceClient.futures_account_transfer(asset = 'USDT', amount = transfer_amount, type = 2)
                print(res)
                account = BinanceClient.futures_account()
                totalMarginBalance = get_totalMarginBalance(account)


    margin_ratio = get_margin_ratio(account)

    # Get bots in 100/page chunks
    if args.auto or args.show_bots or args.show_all:
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

    # Show bot table
    if args.show_bots or args.show_all:
        try:
            print(show_bots(bots, account_id))
            print("--------------------")
        except Exception as e:
            print(e)
            traceback.print_exc()
            pass

    '''
    # Show deals/positions table
    if args.show_deals or args.show_positions or args.show_all:
        try:
            deals=get3CommasAPI().getDeals(OPTIONS=f"?account_id={account_id}&scope=active&limit=100")
            show_deals_positions_txt, zeroSO = show_deals_positions(deals, account['positions'], args.colors)
            print(show_deals_positions_txt)
            if "Error" in show_deals_positions_txt:
                beep(5)
        except Exception as e:
            print(e)
            traceback.print_exc()
            pass

    # Show Margin Ratio
    color = YELLOW+BLINK
    if margin_ratio >= args.stop_at:
        color = RED+BLINK+BOLD
    if margin_ratio <= args.start_at:
        color = GREEN
    print(f"{color}****************************{ENDC}")
    print(f"{color}*** Margin Ratio = {margin_ratio:0.2f}% ***{ENDC}")
    print(f"{color}****************************{ENDC}")
    '''

    # Start/Stop Bots
    if args.auto:

        # Get top list of pairs
        top_list = []
        if args.my_top_pairs:
            top_list = args.my_top_pairs
        if args.signal_top_pairs:
            if sig_top_list_ts <= datetime.now() - timedelta(hours=3): # Update signal top list every hour
                sig_top_list, sig_top_list_ts = get_pairs_with_top_signals()
                top_list.extend(sig_top_list)
        top_list = remove_duplicates_from_list(top_list)
        if args.debug:
            print(f"###################")
            print(f"{top_list}")
            print(f"###################")

        # Collect info...
        top_stopped_pairs = get_top_stopped_pairs(bots, account_id)
        totalMaintMargin = get_totalMaintMargin(account)
        max_bot_pairs = get_max_bot_pairs(totalMarginBalance, args.pair_allowance)
        total_bot_pair_count, active_bot_pair_count, dns_bot_pair_count = get_bot_pair_count(bots, account_id)
        active_positions_count = get_active_positions_count(account['positions'], bots)
        stopped_bots_with_positions = get_stopped_bots_with_positions(bots, account_id, account['positions'])
        started_bots_with_positions = get_started_bots_with_positions(bots, account_id, account['positions'])
        bots_pairs_to_start = round(max_bot_pairs - active_positions_count)
        max_bots_running = (bots_pairs_to_start * args.bots_per_position_ratio) + len(started_bots_with_positions) #dynamic_bots_per_position_ratio
        start_up_to_bots = max_bots_running - active_bot_pair_count + active_positions_count
        start_up_to_bots = 0 if start_up_to_bots <= 0  else start_up_to_bots
        started_bots_without_positions = get_started_bots_without_positions(bots, account_id, account['positions'], top_list)
        count_of_started_bots_without_positions = len(started_bots_without_positions)
        need_to_stop = active_bot_pair_count - max_bots_running
        if args.debug:
            print (f"\tmargin_ratio = {margin_ratio}")
            print (f"\ttotalMaintMargin = {totalMaintMargin}")
            print (f"\tlen(top_stopped_pairs) = {len(top_stopped_pairs)}")
            print (f"\tmax_bot_pairs = {max_bot_pairs}")
            print (f"\ttotal_bot_pair_count = {total_bot_pair_count}")
            print (f"\tactive_bot_pair_count = {active_bot_pair_count}")
            print (f"\tdns_bot_pair_count = {dns_bot_pair_count}")
            print (f"\tactive_positions_count = {active_positions_count}")
            print (f"\targs.bots_per_position_ratio = {args.bots_per_position_ratio}")
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
        #if args.debug: print (f"start_up_to_bots = {start_up_to_bots}")

        if margin_ratio >= args.stop_at: # If MR is larger than or equals stop at, stop all bots...
            print(f"{RED}Hight margin_ratio, stopping bots...{ENDC}")
            stop_all_bots(bots, account_id, args.dry)
            if do_ifttt and margin_ratio >= 5: # Or should we check stop_at * 2
                import urllib.request
                ifttt_contents = urllib.request.urlopen(run_config.ifttt_url).read()
                print(ifttt_contents)
        else: # MR is less than stop at
            if bots_pairs_to_start > 0: # need more positions
                if len(stopped_bots_with_positions) > 0:
                    print(f"Starting {len(stopped_bots_with_positions)} stopped bots with active positions...")
                    if margin_ratio < args.start_at:
                        if not args.no_start:
                            for bot_to_start in stopped_bots_with_positions:
                                print(f"Starting {bot_to_start} bot pairs...")
                                start_bot_pair(bots, account_id, bot_to_start, args.dry)
                    else:
                        print(f"{YELLOW}Hight margin_ratio, not starting any bots...{ENDC}")
                else: # no stopped bots with positions to start, start from ones without active positions
                    if args.verbose: print (f"Need to have a max of {max_bots_running} stopped bot pairs...")

                    if active_bot_pair_count > max_bots_running:
                        if args.verbose:
                            print("Already have too many bots running...")
                        if args.debug:
                            print(f"max_bots_running = {max_bots_running}")
                            print(f"active_bot_pair_count = {active_bot_pair_count}")
                            print(f"started_bots_without_positions = {started_bots_without_positions}")
                            print(f"count_of_started_bots_without_positions = {count_of_started_bots_without_positions}")
                        #need_to_stop = active_bot_pair_count - max_bots_running
                        if args.debug:
                            print(f"need_to_stop = {need_to_stop}")
                        if args.verbose:
                            print(f"Need to stop {need_to_stop} extra bot pairs...")
                        if count_of_started_bots_without_positions > 0:
                            stop_list = started_bots_without_positions[:need_to_stop]
                            print("Stopping extra bots...")
                            for bot_to_stop in stop_list:
                                print(f"Stopping {bot_to_stop} bot pairs...")
                                stop_bot_pair(bots, account_id, bot_to_stop, args.dry)
                        else:
                            print("nothing to stop")
                    elif active_bot_pair_count == max_bots_running:
                        print ("No change to number of bots running needed...")
                    else:

                        #count_of_started_bots_without_positions = len(started_bots_without_positions)
                        max_bots_running = max_bots_running - count_of_started_bots_without_positions

                        if args.randomize_bots:
                            stopped_bots_without_positions = get_stopped_bots_without_positions_random(bots, account_id, account['positions'], top_list)
                        else:
                            stopped_bots_without_positions = get_stopped_bots_without_positions(bots, account_id, account['positions'], top_list)
                        if args.debug:
                            print("Pick min from:")
                            print(f"max_bots_running = {max_bots_running}")
                            print(f"args.bot_start_bursts = {args.bot_start_bursts}")
                            print(f"len(stopped_bots_without_positions) = {len(stopped_bots_without_positions)}")
                            print(f"max_bots_running = {max_bots_running}")
                            print(f"start_up_to_bots = {start_up_to_bots}")
                            #print(f" = {}")
                        actual_bots_to_start = min(max_bots_running, 
                                                args.bot_start_bursts, 
                                                len(stopped_bots_without_positions), 
                                                max_bots_running, 
                                                start_up_to_bots)
                        actual_bots_to_start = 0 if actual_bots_to_start <= 0 else actual_bots_to_start # Make sure it's not a negative number

                        if not args.no_start:
                            if margin_ratio < args.start_at:
                                print (f"Incrementally starting {actual_bots_to_start} stopped bots without positions...")
                                burst_pairs_to_start = stopped_bots_without_positions[:actual_bots_to_start] # Assume list is sorted
                                for bot_to_start in burst_pairs_to_start:
                                    print(f"Starting {bot_to_start} bot pairs...")
                                    start_bot_pair(bots, account_id, bot_to_start, args.dry)
                            else:
                                print(f"{YELLOW}Hight margin_ratio, not starting any bots...{ENDC}")

            elif bots_pairs_to_start < 0: # running too much positions
                if args.no_start:
                    print("Hight positions count, stopping all running bots...")
                    stop_all_bots(bots, account_id, args.dry)
                else:
                    #started_bots_without_positions = get_started_bots_without_positions(bots, account_id, account['positions'])
                    print(f"Hight positions count, stopping {len(started_bots_without_positions)} bots without positions")
                    for bot_to_stop in started_bots_without_positions:
                        print(f"Stopping {bot_to_stop} bot pairs...")
                        stop_bot_pair(bots, account_id, bot_to_stop, args.dry)
            else: # the right ammount of positions running
                print("No change to positions count needed...")
                #started_bots_without_positions = get_started_bots_without_positions(bots, account_id, account['positions'])
                print(f"Correct positions count, stopping {len(started_bots_without_positions)} bots without positions")
                for bot_to_stop in started_bots_without_positions:
                    print(f"Stopping {bot_to_stop} bot pairs...")
                    stop_bot_pair(bots, account_id, bot_to_stop, args.dry)



    # Show Margin Ratio
    color = YELLOW+BLINK
    if margin_ratio >= args.stop_at:
        color = RED+BLINK+BOLD
    if margin_ratio <= args.start_at:
        color = GREEN
    print(f"{color}****************************{ENDC}")
    print(f"{color}*** Margin Ratio = {margin_ratio:0.2f}% ***{ENDC}")
    print(f"{color}****************************{ENDC}")


    # Show deals/positions table
    if args.show_deals or args.show_positions or args.show_all:
        try:
            deals=get3CommasAPI().getDeals(OPTIONS=f"?account_id={account_id}&scope=active&limit=100")
            '''
            if args.debug:
                print("############################deals#######################")
                pprint(deals)
                print("############################account#######################")
                pprint(account)
            '''
            show_deals_positions_txt, zeroSO = show_deals_positions(deals, account['positions'], args.colors)
            print(show_deals_positions_txt)
            if "Error" in show_deals_positions_txt:
                beep(beep_time)
        except Exception as e:
            print(e)
            traceback.print_exc()
            pass

    if args.beep and margin_ratio >= args.stop_at:
        new_beep_time = round(beep_time * (1 + (margin_ratio - args.stop_at) * 10))
        beep(new_beep_time)

    ret['margin_ratio'] = margin_ratio
    return ret


#----------------------------------
#----------------------------------
#----------------------------------

signal.signal(signal.SIGINT, signal_handler)

print ("-----------------------------------------------------------------")
print ("-----------------------------------------------------------------")

found_account = False
try:
    _ = run_config.Binance_APIs
    for Binance_API in run_config.Binance_APIs:
        #print(
        if args.binance_account_flag in Binance_API['account_name']:
            found_account = True
            account_name = Binance_API['account_name']
            Binance_API_KEY = Binance_API['Binance_API_KEY']
            Binance_API_SECRET = Binance_API['Binance_API_SECRET']
except Exception:
    found_account = True
    account_name = args.binance_account_flag
    Binance_API_KEY = run_config.Binance_API_KEY
    Binance_API_SECRET = run_config.Binance_API_KEY

'''
print(Binance_API_KEY)
print(Binance_API_SECRET)
# Allow keys from shell env
Binance_API_KEY = os.getenv('Binance_API_KEY', Binance_API_KEY)
Binance_API_SECRET = os.getenv('Binance_API_SECRET', Binance_API_SECRET)
print(Binance_API_KEY)
print(Binance_API_SECRET)
'''

if not found_account:
    print(f"Error: could not find account with flag {args.binance_account_flag}")
    exit(1)


account, account_txt = getAccountID(account_name)
if account == "" or account_txt == "":
    print("Error: Need to find account before proceeding...")
    exit(1)

if args.keep_running:
    while True:
        keep_running_timer = args.keep_running_timer
        print (account_txt)
        print ("-----------------------------------------------------------------")
        try:
            ret = run_account(account, Binance_API_KEY, Binance_API_SECRET)
            if ret['margin_ratio'] > args.stop_at and args.keep_running_dynamic_timer:
                keep_running_timer *= 3
            sys.stdout.flush()
        except Exception as e:
            print(e)
            traceback.print_exc()
            keep_running_timer = int(args.keep_running_timer/10) + 10
            pass

        #ts_txt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        #print(f"      - {ts_txt}", end='')
        if args.dry:
            print("*************************")
            print("***Running in DRY mode***")
            print("*************************")
        sys.stdout.flush()
        countdown(keep_running_timer)
        print()
        print ("-----------------------------------------------------------------")
else:
    print (account_txt)
    print ("-----------------------------------------------------------------")
    run_account(account, Binance_API_KEY, Binance_API_SECRET)
    if args.dry:
        print("*************************")
        print("***Running in DRY mode***")
        print("*************************")
    sys.stdout.flush()



