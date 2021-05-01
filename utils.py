#from binance_api import Binance
from python_binance.binance.client import Client
from tcommas_api import API3Commas
from pprint import pprint
import sys
import time
import run_config
from datetime import datetime
from time import gmtime, strftime
import random



#----------------------------------

beep_time = 2

#----------------------------------

def timing(f):
    def wrap(*args, **kwargs):
        time1 = time.time()
        ret = f(*args, **kwargs)
        time2 = time.time()
        print('{:s} function took {:.3f} ms'.format(f.__name__, (time2-time1)*1000.0))

        return ret
    return wrap

#@timing
def getBinanceAPI(key, secret):
    api = Binance(
        API_KEY=key,
        API_SECRET=secret
    )
    return api

#@timing
def get3CommasAPI():
    api = API3Commas(
        API_KEY=run_config.TCommas_API_KEY,
        API_SECRET=run_config.TCommas_API_SECRET
    )
    return api


def xstr(s):
    return '' if s is None else str(s)

def xfloat(s):
    return 0.0 if s is None else float(s)

def signal_handler(sig, frame):
    print('\nYou pressed Ctrl+C!')
    sys.exit(0)


def countdown(t):
    #print("", end="\r")
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        #print(timer, end="\r")
        ts_txt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"{timer} - {ts_txt}", end="\r")
        time.sleep(1)
        t -= 1


def beep(btime):
    for i in range(btime):
        sys.stdout.write('\r\a')
        sys.stdout.flush()
        time.sleep(0.5)


def get_spot_balance(Client, coin = 'USDT'):
    coins = Client.get_all_coins_info()
    usdt_spot_total = 0.0
    for a_coin in coins:
        if a_coin['coin'] == coin:
            usdt_spot_total = xfloat(a_coin['free']) + xfloat(a_coin['locked'])
    return usdt_spot_total


def show_positions(positions):
    txt = f"Sym   Amt   entryPrice Margin     PNL       \n"
    for position in sorted(positions, key=lambda k: (k['symbol'])):
        if float(position['positionAmt']) != 0.0:
            txt += f"{position['symbol'].replace('USDT',''):5} {position['positionAmt']:5} {position['entryPrice']:10} {position['positionInitialMargin']:10} {position['unrealizedProfit']}\n"
    return txt[:-1]


def get_active_positions_count(positions, bots):
    count = 0
    for position in positions:
        if float(position['positionAmt']) != 0.0:
            for bot in bots:
                if position['symbol'].replace('USDT','') == ''.join(bot['pairs']).replace('USDT_','') and bot['strategy'] == 'long':
                    count += int((float(bot['base_order_volume'])//10) - 1)
            count += 1
    return count


def get_margin_ratio(a_data):
    return float(a_data['totalMaintMargin']) / float(a_data['totalMarginBalance']) * 100



def get_availableBalance(a_data, asset = 'USDT'):
    balance = 0.0
    for asset in a_data['assets']:
        if asset['asset'] == 'USDT':
            balance = float(asset['walletBalance']) #???
    return balance


def get_totalMarginBalance(a_data):
    return float(a_data['totalMarginBalance'])


def get_totalMaintMargin(a_data):
    return float(a_data['totalMaintMargin'])


def get_max_bot_pairs(balance, pair_allowance):
    return balance/pair_allowance


def show_bots(bots, account_id):
    total = 0.0
    txt = f"\u2B9E {'Pair':<6} {'M':2} {'AD':<3} {'Total':<7} {'L/S':<5} {'Bot Name':<25}\n"
    #for bot in sorted(bots, key=lambda k: (str(k['is_enabled']), ''.join(k['pairs']), k['strategy'])):
    for bot in sorted(bots, key=lambda k: (''.join(k['pairs']), k['strategy'])):
        if account_id == bot['account_id']:
            notes = ""
            if 'do not start' in bot['name'].lower():
                notes += "\u26D4"
            if ''.join(bot['pairs']).replace('USDT_','') not in bot['name']:
                notes += " - Pair does not match bot name"
            total += float(bot['finished_deals_profit_usd'])
            up_down_flag = '\u2B9D' if bot['is_enabled'] else '\u2B9F'
            multiplier = int((float(bot['base_order_volume'])//10))
            txt += f"{up_down_flag} {''.join(bot['pairs']).replace('USDT_',''):<6} {multiplier}X {bot['active_deals_count']:<3} ${float(bot['finished_deals_profit_usd']):<6.2f} {bot['strategy']:<5} {bot['name']:<25} {notes}\n"
    txt += f"\u2B9C {'':13} ${total:<6.2f}\n"
    return txt[:-1]


def list_bot_pairs(bots, account_id, strategy = "long"):
    txt = ""
    #for bot in sorted(bots, key=lambda k: (float(k['finished_deals_profit_usd']))):
    for bot in sorted(bots, key=lambda k: (''.join(k['pairs']).replace('USDT_',''))):
        if account_id == bot['account_id']:
            if bot['strategy'] == strategy:
                txt += f"{''.join(bot['pairs']).replace('USDT_','')} {float(bot['finished_deals_profit_usd'])/(float(bot['base_order_volume'])//10):.2f}\n"
    return txt[:-1]


def get_bot_pair_count(bots, account_id):
    a_count = 0
    count = 0
    dns_count = 0
    for bot in bots:
        if account_id == bot['account_id'] and bot['strategy'] == 'long':
            count += 1
            if bot['is_enabled']:
                a_count += 1
            if 'do not start' in bot['name']:
                dns_count += 1
    return count, a_count, dns_count


def stop_all_bots(bots, account_id, dry):
    for bot in sorted(bots, key=lambda k: (''.join(k['pairs']))):
        if account_id == bot['account_id']:
            if bot['is_enabled']:
                print(f"Stopping {bot['name']}... ", end='')
                if not dry:
                    xbot = get3CommasAPI().disableBot(BOT_ID=f"{bot['id']}")
                    if xbot['is_enabled']:
                        print(f"{RED}Error: Could not disable bot{ENDC}")
                    else:
                        print("Bot is now disabled")
                else:
                    print("")
            else:
                #print("Bot is already disabled")
                pass


def start_all_bots(bots, account_id, dry):
    for bot in sorted(bots, key=lambda k: (''.join(k['pairs']))):
        #if args.binance_account_flag in bot['account_name']:
        if account_id == bot['account_id']:
            if bot['is_enabled'] or 'do not start' in bot['name']:
                pass # nothing to do
            else:
                print(f"Starting {bot['name']}... ", end='')
                if not dry:
                    xbot = get3CommasAPI().enableBot(BOT_ID=f"{bot['id']}")
                    if xbot['is_enabled']:
                        print("Bot is now enabled")
                    else:
                        print(f"{RED}Error: Could not enable bot{ENDC}")
                else:
                    print("")


# Maybe can combine both functions with default None
def start_bot_pair(bots, account_id, pair_to_start, dry):
    for bot in sorted(bots, key=lambda k: (''.join(k['pairs']))):
        #if args.binance_account_flag in bot['account_name']:
        if account_id == bot['account_id']:
            if bot['is_enabled'] or 'do not start' in bot['name'] or not ''.join(bot['pairs']).endswith(pair_to_start):
                pass # nothing to do
            else:
                print(f"Starting {bot['name']}... ", end='')
                if not dry:
                    xbot = get3CommasAPI().enableBot(BOT_ID=f"{bot['id']}")
                    if xbot['is_enabled']:
                        print("Bot is now enabled")
                    else:
                        print(f"{RED}Error: Could not enable bot{ENDC}")
                else:
                    print("")


def stop_bot_pair(bots, account_id, pair_to_stop, dry):
    for bot in sorted(bots, key=lambda k: (''.join(k['pairs']))):
        #if args.binance_account_flag in bot['account_name']:
        if account_id == bot['account_id']:
            if bot['is_enabled'] and ''.join(bot['pairs']).endswith(pair_to_stop):
                print(f"Stopping {bot['name']}... ", end='')
                if not dry:
                    xbot = get3CommasAPI().disableBot(BOT_ID=f"{bot['id']}")
                    if xbot['is_enabled']:
                        print(f"{RED}Error: Could not disable bot{ENDC}")
                    else:
                        print("Bot is now disabled")
                else:
                    print("")


# Get sorted list of stopped pairs by profit accounting for multiplier...
def get_top_stopped_pairs(bots, account_id):
    l = []
    for bot in sorted(bots, key=lambda k: (float(k['finished_deals_profit_usd'])/float(k['base_order_volume'])), reverse = True):
        #if args.binance_account_flag in bot['account_name'] and bot['strategy'] == "long" and not bot['is_enabled'] and 'do not start' not in bot['name']:
        if account_id == bot['account_id'] and bot['strategy'] == "long" and not bot['is_enabled'] and 'do not start' not in bot['name']:
            l.append(''.join(bot['pairs']).replace('USDT_',''))
    # intersect with args.pairs and keep order from args.pairs...
    return l


# Combine both with and without functions
# stopped bots with positions
def get_stopped_bots_with_positions(bots, account_id, positions):
    positions_l = []
    for position in sorted(positions, key=lambda k: (k['symbol'])):
        if float(position['positionAmt']) != 0.0:
            positions_l.append(position['symbol'].replace('USDT',''))

    bot_l = []
    for bot in sorted(bots, key=lambda k: (float(k['finished_deals_profit_usd'])/float(k['base_order_volume'])), reverse = True):
        if account_id == bot['account_id'] and bot['strategy'] == "long" and not bot['is_enabled'] and 'do not start' not in bot['name']:
            if ''.join(bot['pairs']).replace('USDT_','') in positions_l:
                bot_l.append(''.join(bot['pairs']).replace('USDT_',''))
    return bot_l


# sorted stopped bots without positions
def get_stopped_bots_without_positions(bots, account_id, positions):
    positions_l = []
    for position in sorted(positions, key=lambda k: (k['symbol'])):
        if float(position['positionAmt']) != 0.0:
            positions_l.append(position['symbol'].replace('USDT',''))

    bot_l = []
    for bot in sorted(bots, key=lambda k: (float(k['finished_deals_profit_usd'])/float(k['base_order_volume'])), reverse = True):
        if account_id == bot['account_id'] and bot['strategy'] == "long" and not bot['is_enabled'] and 'do not start' not in bot['name']:
            if ''.join(bot['pairs']).replace('USDT_','') not in positions_l:
                bot_l.append(''.join(bot['pairs']).replace('USDT_',''))
    return bot_l

# Random stopped bots without positions
def get_stopped_bots_without_positions_random(bots, account_id, positions):
    positions_l = []
    for position in sorted(positions, key=lambda k: (k['symbol'])):
        if float(position['positionAmt']) != 0.0:
            positions_l.append(position['symbol'].replace('USDT',''))

    bot_l = []
    random.shuffle(bots)
    for bot in bots:
        if account_id == bot['account_id'] and bot['strategy'] == "long" and not bot['is_enabled'] and 'do not start' not in bot['name']:
            if ''.join(bot['pairs']).replace('USDT_','') not in positions_l:
                bot_l.append(''.join(bot['pairs']).replace('USDT_',''))
    return bot_l


# get count of stopped bots without active positions
def get_count_of_stopped_bots_without_positions(bots, account_id, positions):
    positions_l = []
    for position in sorted(positions, key=lambda k: (k['symbol'])):
        if float(position['positionAmt']) != 0.0:
            positions_l.append(position['symbol'].replace('USDT',''))

    count = 0
    for bot in bots:
        if account_id == bot['account_id'] and bot['strategy'] == "long" and not bot['is_enabled'] and 'do not start' not in bot['name']:
            if ''.join(bot['pairs']).replace('USDT_','') not in positions_l:
                count += 1
    return count


# get count of started bots without active positions
def get_count_of_started_bots_without_positions(bots, account_id, positions):
    positions_l = []
    for position in sorted(positions, key=lambda k: (k['symbol'])):
        if float(position['positionAmt']) != 0.0:
            positions_l.append(position['symbol'].replace('USDT',''))

    count = 0
    for bot in bots:
        if account_id == bot['account_id'] and bot['strategy'] == "long" and bot['is_enabled'] and 'do not start' not in bot['name']:
            if ''.join(bot['pairs']).replace('USDT_','') not in positions_l:
                count += 1
    return count



# get a list of started bots without active positions
def get_started_bots_without_positions(bots, account_id, positions):
    positions_l = []
    for position in sorted(positions, key=lambda k: (k['symbol'])):
        if float(position['positionAmt']) != 0.0:
            positions_l.append(position['symbol'].replace('USDT',''))

    bot_l = []
    for bot in bots:
        if account_id == bot['account_id'] and bot['strategy'] == "long" and bot['is_enabled'] and 'do not start' not in bot['name']:
            if ''.join(bot['pairs']).replace('USDT_','') not in positions_l:
                bot_l.append(''.join(bot['pairs']).replace('USDT_',''))
    return bot_l



# get a list of started bots with active positions
def get_started_bots_with_positions(bots, account_id, positions):
    positions_l = []
    for position in sorted(positions, key=lambda k: (k['symbol'])):
        if float(position['positionAmt']) != 0.0:
            positions_l.append(position['symbol'].replace('USDT',''))

    bot_l = []
    for bot in bots:
        if account_id == bot['account_id'] and bot['strategy'] == "long" and bot['is_enabled'] and 'do not start' not in bot['name']:
            if ''.join(bot['pairs']).replace('USDT_','') in positions_l:
                bot_l.append(''.join(bot['pairs']).replace('USDT_',''))
    return bot_l



# return FIRST matching accountID
#@timing
def getAccountID(binance_account_flag):
    accounts=get3CommasAPI().getAccounts()
    if type(accounts) != type([]):
        print("ERROR: Expected to get a list from 3Commas, got:")
        pprint(accounts)
    found = False
    account_id = ""
    account_txt = ""
    accounts_found = ""
    for account in accounts:
        accounts_found += f"{account['exchange_name']}\t:\t{account['name']}\n"
        if account['exchange_name'] == "Binance Futures USDT-M" and binance_account_flag in account['name']:
            txt = f"Using {account['name']} from exchange {account['exchange_name']}"
            account_id = account['id']
            account_txt = txt
            found = True
    if not found:
        print(f"ERROR: Expected to find {binance_account_flag} in 3Commas account names:")
        print(accounts_found)
    return account_id, account_txt



def show_deals(deals):

    # Get field from structure
    def gf(data, field):
        return data[field]

    def get_deal_cost_reserved(deal):
        current_active_safety_orders = gf(deal, 'current_active_safety_orders')
        completed_safety_orders_count = deal['completed_safety_orders_count']
        safety_order_volume = float(gf(deal, 'safety_order_volume'))
        martingale_volume_coefficient = float(gf(deal, 'martingale_volume_coefficient'))
        active_safety_orders_count = gf(deal, 'active_safety_orders_count')
        max_safety_orders = gf(deal, 'max_safety_orders')

        cost = 0
        max_cost = 0
        for i in range(completed_safety_orders_count, current_active_safety_orders + completed_safety_orders_count):
            cost += safety_order_volume * martingale_volume_coefficient ** i    
        for i in range(completed_safety_orders_count, max_safety_orders):
            max_cost += safety_order_volume * martingale_volume_coefficient ** i
        return cost, max_cost


    ts = datetime.utcnow()
    ts_txt = ts.strftime('%Y-%m-%dT%H:%M:%SZ')
    total_bought_volume = 0.0
    total_deals_cost_reserved = 0.0
    txt = ""

    active_deals = sorted(deals, key=lambda k: (float(k['bought_volume'])))#, reverse = True)
    txt = f"{'Pair':6} : {'SOs':9} : ${'Bought':8} : ${'Reserve':7} : {'%Profit':7} : Age(DHM)\n"

    for ad in active_deals:
        error_message = f"{RED}{xstr(ad['error_message'])}{xstr(ad['failed_message'])}{ENDC}"
        a_flag = ''
        if ad['current_active_safety_orders_count'] == 0:
            a_flag = f'{RED}***Zero Active***{ENDC}'
            #if ad['completed_safety_orders_count'] != ad['max_safety_orders']:
            if ad['completed_safety_orders_count'] == 0:
                a_flag = f'{GREEN}***Closing/Opening***{ENDC}'
            else:
                a_flag = f'{YELLOW}***SO***{ENDC}'

        actual_usd_profit = float(ad['actual_usd_profit'])
        created_at_ts = datetime.strptime(ad['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
        created_at_ts_diff = ts - created_at_ts
        reserved_cost, max_reserved_cost = get_deal_cost_reserved(ad)
        
        age_d = created_at_ts_diff.days
        age_d_str = str(age_d).rjust(2, '0')+' ' if age_d > 0 else '   '
        age_h = int((created_at_ts_diff.total_seconds()/3600)%24)
        age_h_str = str(age_h).rjust(2, '0')+':' if age_h > 0 else '   '
        age_m = int(((created_at_ts_diff.total_seconds()/3600) - int(created_at_ts_diff.total_seconds()/3600))*60)
        age_m_str = str(age_m).rjust(2, '0')# if age_m > 0 else '  '
        age = f"{age_d_str:3}{age_h_str:3}{age_m_str:2}"

        txt += f"{ad['pair'].replace('USDT_',''):6} : c{ad['completed_safety_orders_count']} a{ad['current_active_safety_orders_count']} m{ad['max_safety_orders']} : ${float(ad['bought_volume']):8.2f} : ${reserved_cost:7.2f} : {ad['actual_profit_percentage']:6}% : {age} {a_flag}{error_message}\n"

        total_bought_volume += float(ad['bought_volume'])
        total_deals_cost_reserved += reserved_cost
    txt += f"{'':18} : ${total_bought_volume:8.2f} : ${total_deals_cost_reserved:7.2f}"
    return txt



#@timing
def show_deals_positions(deals, positions, zeroSO = [], colors = True, unicode = True):

    newZeroSO = []
    if colors:
        ENDC   = '\033[0m'
        RED    = '\033[91m'
        GREEN  = '\033[92m'
        YELLOW = '\033[93m'
        BLINK  = '\033[5m'
        BOLD   = '\033[1m'
        BLUE   = '\033[94m'
    else:
        ENDC   = ''
        RED    = ''
        GREEN  = ''
        YELLOW = ''
        BLINK  = ''
        BOLD   = ''
        BLUE   = ''

    if unicode:
        UP   = ''
        DOWN = ''
    else:
        UP   = ''
        DOWN = ''

    # Get field from structure
    def gf(data, field):
        return data[field]

    def get_deal_cost_reserved(deal):
        current_active_safety_orders = gf(deal, 'current_active_safety_orders')
        completed_safety_orders_count = deal['completed_safety_orders_count']
        safety_order_volume = xfloat(gf(deal, 'safety_order_volume'))
        martingale_volume_coefficient = xfloat(gf(deal, 'martingale_volume_coefficient'))
        active_safety_orders_count = gf(deal, 'active_safety_orders_count')
        max_safety_orders = gf(deal, 'max_safety_orders')

        cost = 0
        max_cost = 0
        for i in range(completed_safety_orders_count, current_active_safety_orders + completed_safety_orders_count):
            cost += safety_order_volume * martingale_volume_coefficient ** i    
        for i in range(completed_safety_orders_count, max_safety_orders):
            max_cost += safety_order_volume * martingale_volume_coefficient ** i
        return cost, max_cost


    deal_position_list = []
    deal_position = {}
    ts = datetime.utcnow()
    ts_txt = ts.strftime('%Y-%m-%dT%H:%M:%SZ')
    total_bought_volume = 0.0
    total_deals_cost_reserved = 0.0
    txt = ""

    active_deals = sorted(deals, key=lambda k: (xfloat(k['bought_volume'])))#, reverse = True)
    txt = f"{'Pair':6} {'%Profit':6} {'Amt':5} {'entPrice':10} {'SOs':9} ${'Bought':7} ${'Reserve':7} ${'Price':6} ${'TTP':6} Age(DHM)\n"

    for ad in active_deals:
    
        #if 'BAL' in ad['pair'].replace('USDT_',''):
        #    txt += f"{ad}\n"
        #pprint(ad)
    
        ad_pair = ad['pair'].replace('USDT_','')
        updated_at_ts = datetime.strptime(ad['updated_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
        updated_at_ts_diff = ts - updated_at_ts
        created_at_ts = datetime.strptime(ad['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
        created_at_ts_diff = ts - created_at_ts
        #pprint(ad)
        #exit()  take_profit_price current_price
        deal_position = {**ad}
        position_txt = ""
        for position in sorted(positions, key=lambda k: (k['symbol'])):
            if ad['pair'].replace('USDT_','') == position['symbol'].replace('USDT',''):
                if xfloat(position['positionAmt']) != 0.0:
                    position_txt = f"{position['positionAmt']:5} {position['entryPrice']:10}"
                    position['positionLeverage'] = position['leverage']
                    deal_position = {**ad, **position}
                    #pprint(position)

        deal_position['notes'] = ''

        error_message = f"{RED}{xstr(ad['error_message'])}{xstr(ad['failed_message'])}{ENDC}"
        if position_txt == "":
            if created_at_ts_diff.total_seconds() < 90:
                position_txt = f"No Positions Yet"
            else:
                position_txt = f"{RED}NoPosition Found{ENDC}"
        a_flag = ''
        if ad['current_active_safety_orders_count'] == 0:
            newZeroSO.append(ad_pair)
            a_flag = f'\n    {RED}***Zero Active***{ENDC}'
            #if ad['completed_safety_orders_count'] != ad['max_safety_orders']:
            if ad['completed_safety_orders_count'] == 0:
                a_flag = f'\n    {GREEN}***Closing/Opening***{ENDC}'
            else:
                a_flag = f'\n    {YELLOW}***SO***{ENDC}'
                '''
                if ad_pair in zeroSO:
                    a_flag = f'\n    {RED}***SO***{ENDC}'
                else:
                    a_flag = f'\n    {YELLOW}***SO***{ENDC}'
                '''

        actual_usd_profit = xfloat(ad['actual_usd_profit'])
        reserved_cost, max_reserved_cost = get_deal_cost_reserved(ad)
        deal_position['reserved_cost'] = reserved_cost
        deal_position['max_reserved_cost'] = max_reserved_cost
        
        
        age_d = created_at_ts_diff.days
        age_d_str = str(age_d).rjust(2, '0')+' ' if age_d > 0 else '   '
        age_h = int((created_at_ts_diff.total_seconds()/3600)%24)
        age_h_str = str(age_h).rjust(2, '0')+':' if age_h > 0 else '   '
        age_m = int(((created_at_ts_diff.total_seconds()/3600) - int(created_at_ts_diff.total_seconds()/3600))*60)
        age_m_str = str(age_m).rjust(2, '0')# if age_m > 0 else '  '
        age = f"{age_d_str:3}{age_h_str:3}{age_m_str:2}"
        deal_position['create_age_txt'] = age
        deal_position['create_age'] = created_at_ts_diff.total_seconds()
        deal_position['update_age'] = updated_at_ts_diff.total_seconds()        

        color = ''
        if xfloat(ad['actual_profit_percentage']) < -10.0:
            color = RED + BLINK + BOLD
            deal_position['color'] = RED + BLINK + BOLD
        elif xfloat(ad['actual_profit_percentage']) < -5.0:
            color = RED + BOLD
            deal_position['color'] = RED + BOLD
        elif xfloat(ad['actual_profit_percentage']) < -2.0:
            color = RED
            deal_position['color'] = RED
        elif xfloat(ad['actual_profit_percentage']) < 0.0:
            color = YELLOW
            deal_position['color'] = YELLOW
        if xfloat(ad['actual_profit_percentage']) >= xfloat(ad['take_profit']):
            color = BLUE
            deal_position['color'] = BLUE
        elif xfloat(ad['actual_profit_percentage']) > 0.0:
            color = GREEN
            deal_position['color'] = GREEN
        txt += f"{color}{ad['pair'].replace('USDT_',''):6} {xfloat(ad['actual_profit_percentage']):6.2f}% {position_txt} c{ad['completed_safety_orders_count']} a{ad['current_active_safety_orders_count']} m{ad['max_safety_orders']} ${xfloat(ad['bought_volume']):7.2f} ${reserved_cost:7.2f} ${xfloat(ad['current_price']):6.2f} ${xfloat(ad['take_profit_price']):6.2f} {age} {a_flag}{error_message}{ENDC}\n"


        # Special case handeling
        if "error" in error_message.lower():
            txt += f"{RED}Detected error in deal ID {ad['id']}{ENDC}\n"
            if xfloat(ad['actual_profit_percentage']) > 0.01:
                txt += f"{GREEN}Detected +ve profit ({xfloat(ad['actual_profit_percentage']):0.2f}%) in deal ID {ad['id']}{ENDC}\n"
                txt += f"{YELLOW}Panic Selling deal ID {ad['id']} at {xfloat(ad['actual_profit_percentage']):0.2f}%{ENDC}\n"
                #txt += "********* DRY No-Op*********\n"
                panicSell = get3CommasAPI().panicSellDeal(DEAL_ID=f"{ad['id']}")
                print(panicSell)
                #txt += f"{panicSell}\n"
                beep(3)
            else:
                txt += f"{RED}Detected -ve profit ({xfloat(ad['actual_profit_percentage']):0.2f}%) in deal ID {ad['id']}{ENDC}\n"
                txt += f"{RED}********* Manual action needed *********{ENDC}\n"
                beep(3)
        #elif ad['current_active_safety_orders_count'] == 0:
        #    txt += "Detected zero active SO count...\n"
        #    txt += f"{ad}\n" ### Testing to see if we can identify if this is an issue or not...





        '''
ICX     -1.02% 58    2.2131     c3 a0 m11 $ 128.41 $   0.00 $  2.19 $  2.22       38 
    ***SO***
    
        c{ad['completed_safety_orders_count']} 
        a{ad['current_active_safety_orders_count']} 
        m{ad['max_safety_orders']}
    
        '''

        if deal_position['error_message'] or deal_position['failed_message']:
            deal_position['notes'] += f"{xstr(deal_position['error_message'])} {xstr(deal_position['failed_message'])}"
        if deal_position['current_active_safety_orders_count'] == 0:
            if deal_position['completed_safety_orders_count'] == deal_position['max_safety_orders']:
                deal_position['notes'] += ' *** Reached max SOs ***'
            else: #if deal_position['completed_safety_orders_count'] == 0:
                if deal_position['completed_safety_orders_count'] == 0:
                    if deal_position['create_age'] <= 60:
                        deal_position['notes'] += ' Opening deal'
                    else:
                        if xfloat(deal_position['actual_profit_percentage']) >= xfloat(deal_position['take_profit']):
                            deal_position['notes'] += ' *** TTP ***'
                        else:
                            deal_position['notes'] += ' ???'
                else:
                    if deal_position['update_age'] <= 60:
                        deal_position['notes'] += ' Updating deal'
                    else:
                        if xfloat(deal_position['actual_profit_percentage']) >= xfloat(deal_position['take_profit']):
                            deal_position['notes'] += ' *** TTP ***'
                        else:
                            deal_position['notes'] += ' *** Missing SO ***'


        # For debugging new structure...
        #if deal_position['notes'] != '':
        #    txt += f"{deal_position['notes']}\n"




        total_bought_volume += xfloat(ad['bought_volume'])
        total_deals_cost_reserved += reserved_cost

    for position in sorted(positions, key=lambda k: (k['symbol'])):
        if xfloat(position['positionAmt']) != 0.0:
            found_position_without_deal = False
            for ad in active_deals:
                if ad['pair'].replace('USDT_','') == position['symbol'].replace('USDT',''):
                    found_position_without_deal = True
            if not found_position_without_deal:
                txt += f"{position['symbol'].replace('USDT',''):6} {'':7} {position['positionAmt']:5} {position['entryPrice']:10} {RED}No Deal for position found{ENDC}\n"
                position['positionLeverage'] = position['leverage']
                deal_position = {**position}
                deal_position['error_message'] = 'No Deal for position found'
                deal_position['color'] = RED
                # Check how old updateTime was
                deal_position['notes'] = 'No Deal for position found'

                if deal_position['notes'] and deal_position['notes'] != '':
                    txt += f"{deal_position['notes']}\n"


    deal_position_list.append(deal_position.copy())
    #pprint(deal_position_list)
    txt += f"{'':41} ${total_bought_volume:7.2f} ${total_deals_cost_reserved:7.2f}"
    return txt, newZeroSO

#----------------------------------
#----------------------------------
#----------------------------------
#----------------------------------

