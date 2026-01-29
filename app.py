# PROJECT HOPE v5.0 - PROFESSIONAL EDITION
# Built by Stephen Martinez | Lancaster, PA
# Institutional-Grade Entry Logic | 4 A+ Setups Only | No Impulse Trades

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import random
from datetime import datetime, timedelta
import numpy as np
import pytz
import requests

st.set_page_config(page_title="Project Hope", page_icon="🌱", layout="wide", initial_sidebar_state="collapsed")

# Auto-refresh moved to trade page only

# =============================================================================
# TRADIER SANDBOX API (Paper Trading - Real Prices, Fake Money)
# =============================================================================
TRADIER_TOKEN = "aSgzHbh1WferAyzaHldRDWKYGtSe"
TRADIER_ACCOUNT = "VA32364446"
TRADIER_URL = "https://sandbox.tradier.com/v1"  # Sandbox for paper trading

# =============================================================================
# ALPACA API (for market data backup)
# =============================================================================
ALPACA_KEY = "PKQJEFSQBY2CFDYYHDR372QB3S"
ALPACA_SECRET = "ArMPEE3fqY1JCB5CArZUQ5wY8fYQjuPXJ9qpnwYPHJuw"
ALPACA_URL = "https://paper-api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"

# =============================================================================
# OUTSETA API (Subscription Management)
# =============================================================================
OUTSETA_API_KEY = "bfa0edb1-5ae9-41f2-852d-414b44b64d59"
OUTSETA_DOMAIN = "project-hope.outseta.com"

# Outseta Plan UIDs (from your Outseta dashboard)
OUTSETA_PLANS = {
    "STARTER": "y9gNPqQM",
    "BUILDER": "Rm8ERVQ4",
    "MASTER": "49EKrLm7",
    "VIP": "wmjqBZWV"
}

# Signup links for each tier
SIGNUP_LINKS = {
    "STARTER": "https://project-hope.outseta.com/auth?widgetMode=register&planUid=y9gNPqQM",
    "BUILDER": "https://project-hope.outseta.com/auth?widgetMode=register&planUid=Rm8ERVQ4",
    "MASTER": "https://project-hope.outseta.com/auth?widgetMode=register&planUid=49EKrLm7",
    "VIP": "https://project-hope.outseta.com/auth?widgetMode=register&planUid=wmjqBZWV"
}

# =============================================================================
# FOUNDER INFO
# =============================================================================
PHOTO = "https://i.postimg.cc/qvVSgvfx/IMG-7642.jpg"
NAME = "Stephen Martinez"
LOCATION = "Lancaster, PA"
EMAIL = "thetradingprotocol@gmail.com"

# =============================================================================
# PROFESSIONAL TRADING SETTINGS
# =============================================================================
STOP_LOSS = 0.25              # -25% stop loss (option premium)
TAKE_PROFIT = 0.30            # +30% take profit  
DAILY_LIMIT = 0.15            # -15% daily max loss
MAX_POS = 0.05                # 5% max per trade
COOLDOWN_AFTER_LOSS = 600     # 10 minutes cooldown after loss (seconds)
MIN_RVOL = 1.5                # Minimum relative volume
MIN_HOLD_CHECKS = 3           # Must hold level for 3 checks (15 sec)
MIN_SETUP_SCORE = 70          # HOT score minimum for trade
MIN_CONFIDENCE = 70           # Setup confidence minimum

# PROFESSIONAL PROFIT MANAGEMENT
PARTIAL_PROFIT_1 = 0.15       # Take 50% profit at +15%
PARTIAL_PROFIT_2 = 0.25       # Take 25% more at +25%
TRAIL_AFTER_PARTIAL = True    # Trail stop after first partial
MOVE_STOP_TO_BE = 0.10        # Move stop to breakeven after +10%

# =============================================================================
# NEWS KEYWORDS
# =============================================================================
RED = ['bankruptcy','fraud','sec investigation','lawsuit','downgrade','misses estimates','ceo resigns','delisting','layoffs','fda rejection','criminal','probe','investigation']
GREEN = ['beats estimates','upgrade','fda approval','partnership','acquisition','buyback','record revenue','breakthrough','contract win','price target raised']

# =============================================================================
# TIER SYSTEM (UNCHANGED)
# =============================================================================
TIERS = {
    1: {"name": "STARTER", "stocks": 1, "trades": 1, "color": "#00FFA3", "auto": "always"},
    2: {"name": "BUILDER", "stocks": 3, "trades": 2, "color": "#00E5FF", "auto": "toggle"},
    3: {"name": "MASTER", "stocks": 6, "trades": 3, "color": "#FFD700", "auto": "toggle"},
    4: {"name": "VIP", "stocks": 15, "trades": 5, "color": "#FF6B6B", "auto": "toggle"}
}

# =============================================================================
# WATCHLIST - EXPANDED UNIVERSE
# =============================================================================
# Core watchlist - high volume, options-friendly stocks
STOCKS_CORE = [
    # Tech & Growth
    {"s": "AAPL", "n": "Apple", "p": 185.00},
    {"s": "MSFT", "n": "Microsoft", "p": 420.00},
    {"s": "NVDA", "n": "NVIDIA", "p": 875.00},
    {"s": "AMD", "n": "AMD", "p": 175.00},
    {"s": "TSLA", "n": "Tesla", "p": 175.00},
    {"s": "META", "n": "Meta", "p": 500.00},
    {"s": "GOOGL", "n": "Google", "p": 175.00},
    {"s": "AMZN", "n": "Amazon", "p": 185.00},
    {"s": "NFLX", "n": "Netflix", "p": 620.00},
    
    # Retail Favorites (High Volume, Volatile)
    {"s": "SOFI", "n": "SoFi Technologies", "p": 14.50},
    {"s": "PLTR", "n": "Palantir", "p": 78.00},
    {"s": "NIO", "n": "NIO Inc", "p": 4.85},
    {"s": "RIVN", "n": "Rivian", "p": 12.30},
    {"s": "HOOD", "n": "Robinhood", "p": 24.50},
    {"s": "SNAP", "n": "Snapchat", "p": 11.20},
    {"s": "COIN", "n": "Coinbase", "p": 265.00},
    {"s": "MARA", "n": "Marathon Digital", "p": 18.75},
    {"s": "RIOT", "n": "Riot Platforms", "p": 12.40},
    {"s": "LCID", "n": "Lucid Motors", "p": 2.80},
    {"s": "AMC", "n": "AMC Entertainment", "p": 3.20},
    
    # ETFs for Market Direction
    {"s": "SPY", "n": "S&P 500 ETF", "p": 520.00},
    {"s": "QQQ", "n": "Nasdaq ETF", "p": 450.00},
    {"s": "IWM", "n": "Russell 2000 ETF", "p": 210.00},
    
    # Financials
    {"s": "JPM", "n": "JPMorgan", "p": 195.00},
    {"s": "BAC", "n": "Bank of America", "p": 38.00},
    {"s": "C", "n": "Citigroup", "p": 58.00},
    
    # Energy
    {"s": "XOM", "n": "ExxonMobil", "p": 105.00},
    {"s": "CVX", "n": "Chevron", "p": 155.00},
    
    # Airlines & Travel
    {"s": "AAL", "n": "American Airlines", "p": 17.80},
    {"s": "UAL", "n": "United Airlines", "p": 52.00},
    {"s": "DAL", "n": "Delta Airlines", "p": 48.00},
    
    # Other High Volume
    {"s": "F", "n": "Ford", "p": 10.25},
    {"s": "GM", "n": "General Motors", "p": 45.00},
    {"s": "BA", "n": "Boeing", "p": 185.00},
    {"s": "DIS", "n": "Disney", "p": 110.00},
    {"s": "PYPL", "n": "PayPal", "p": 62.00},
    {"s": "SQ", "n": "Block/Square", "p": 78.00},
    {"s": "ROKU", "n": "Roku", "p": 65.00},
    {"s": "UBER", "n": "Uber", "p": 78.00},
    {"s": "LYFT", "n": "Lyft", "p": 18.00},
]

# Dynamic list - will be populated by premarket scanner
STOCKS_PREMARKET_HOT = []

# Combined active list
STOCKS = STOCKS_CORE.copy()

def get_premarket_movers():
    """
    Scan for pre-market movers - stocks gapping up/down with volume
    
    RUNS: 8:00 AM - 9:29 AM ET (peak pre-market activity)
    FINDS: Stocks gapping 2%+ from previous close
    PURPOSE: Identify today's potential hot stocks before market opens
    """
    global STOCKS_PREMARKET_HOT
    
    movers = []
    
    # Check each core stock for premarket activity
    for stk in STOCKS_CORE[:20]:  # Check top 20 to save API calls
        try:
            # Get latest quote (includes premarket)
            r = requests.get(f"{DATA_URL}/v2/stocks/{stk['s']}/quotes/latest", 
                           headers=headers(), timeout=3)
            if r.status_code == 200:
                data = r.json()
                if 'quote' in data:
                    current = float(data['quote'].get('ap', 0) or data['quote'].get('bp', 0))
                    if current > 0:
                        # Calculate gap from previous close
                        prev_close = stk['p']
                        gap_pct = ((current - prev_close) / prev_close) * 100
                        
                        # If gapping more than 2%, it's potentially hot
                        if abs(gap_pct) >= 2.0:
                            movers.append({
                                's': stk['s'],
                                'n': stk['n'],
                                'p': current,
                                'gap': round(gap_pct, 2),
                                'direction': 'UP' if gap_pct > 0 else 'DOWN'
                            })
        except:
            continue
    
    # Sort by gap size (absolute)
    movers.sort(key=lambda x: abs(x['gap']), reverse=True)
    STOCKS_PREMARKET_HOT = movers[:10]  # Top 10 movers
    
    return movers

def get_active_watchlist():
    """Get the active watchlist based on tier and premarket scan"""
    # Combine core + any premarket movers not already in core
    active = STOCKS_CORE.copy()
    
    for mover in STOCKS_PREMARKET_HOT:
        if not any(s['s'] == mover['s'] for s in active):
            active.append(mover)
    
    return active

BIO = """I'm Stephen Martinez, an Amazon warehouse worker from Lancaster, PA.

For years, I watched my coworkers - hardworking people with families - lose their savings on trading apps designed to make them trade MORE, not trade SMARTER.

These apps make money when you lose money. They want you addicted, emotional, and overtrading.

So I taught myself to code. During lunch breaks. After 10-hour shifts. On weekends when my body was exhausted but my mind wouldn't stop.

Project Hope is my answer. An app that PROTECTS you first. That stops you from blowing up your account. That treats your $1,000 like it matters - because it does.

This isn't about getting rich quick. It's about building something real, one smart trade at a time.

Welcome to Project Hope. Let's build together."""

# =============================================================================
# ALPACA API FUNCTIONS (Market Data)
# =============================================================================
def headers():
    return {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}

# =============================================================================
# TRADIER API FUNCTIONS (Paper Trading)
# =============================================================================
def tradier_headers():
    return {"Authorization": f"Bearer {TRADIER_TOKEN}", "Accept": "application/json"}

def get_tradier_account():
    """Get Tradier account balance and info"""
    try:
        # Try account balances endpoint
        r = requests.get(f"{TRADIER_URL}/accounts/{TRADIER_ACCOUNT}/balances", 
                        headers=tradier_headers(), timeout=5)
        if r.status_code == 200:
            data = r.json()
            bal = data.get('balances', {})
            if bal:
                cash = float(bal.get('cash', {}).get('cash_available', 0) or 
                            bal.get('total_cash', 0) or 
                            bal.get('cash_available', 0) or 100000)
                equity = float(bal.get('total_equity', 0) or 100000)
                return {
                    'cash': cash if cash > 0 else 100000,
                    'equity': equity if equity > 0 else 100000,
                    'account_number': TRADIER_ACCOUNT
                }
    except Exception as e:
        pass
    
    # If API fails, return sandbox default
    return {
        'cash': 100000.0,
        'equity': 100000.0,
        'account_number': TRADIER_ACCOUNT
    }

def get_tradier_positions():
    """Get current positions from Tradier"""
    try:
        r = requests.get(f"{TRADIER_URL}/accounts/{TRADIER_ACCOUNT}/positions", 
                        headers=tradier_headers(), timeout=5)
        if r.status_code == 200:
            data = r.json()
            positions = data.get('positions', {})
            if positions == 'null' or positions is None:
                return []
            pos_list = positions.get('position', [])
            if isinstance(pos_list, dict):
                pos_list = [pos_list]
            return pos_list
    except:
        pass
    return []

def get_tradier_quote(symbol):
    """Get real-time quote from Tradier"""
    try:
        r = requests.get(f"{TRADIER_URL}/markets/quotes",
                        headers=tradier_headers(),
                        params={'symbols': symbol}, timeout=3)
        if r.status_code == 200:
            data = r.json()
            quotes = data.get('quotes', {}).get('quote', {})
            if quotes:
                return float(quotes.get('last', 0) or quotes.get('bid', 0))
    except:
        pass
    return None

def get_option_chain(symbol, expiration=None):
    """Get option chain for a symbol"""
    try:
        # Get next Friday expiration if not specified
        if not expiration:
            today = datetime.now()
            days_until_friday = (4 - today.weekday()) % 7
            if days_until_friday == 0:
                days_until_friday = 7
            expiration = (today + timedelta(days=days_until_friday)).strftime('%Y-%m-%d')
        
        r = requests.get(f"{TRADIER_URL}/markets/options/chains",
                        headers=tradier_headers(),
                        params={'symbol': symbol, 'expiration': expiration}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            options = data.get('options', {})
            if options:
                return options.get('option', [])
    except:
        pass
    return []

def find_option(symbol, option_type='call', max_price=500):
    """Find an appropriate option to trade"""
    chain = get_option_chain(symbol)
    if not chain:
        return None
    
    stock_price = get_tradier_quote(symbol)
    if not stock_price:
        return None
    
    # Filter by type and find ATM option
    options = [o for o in chain if o.get('option_type') == option_type]
    
    # Sort by how close strike is to current price
    options.sort(key=lambda x: abs(x.get('strike', 0) - stock_price))
    
    # Find one within our price range
    for opt in options:
        ask = opt.get('ask', 0) or opt.get('last', 0)
        if ask and ask * 100 <= max_price:  # Convert to contract price
            return opt
    
    return None

def place_tradier_order(symbol, side, quantity, order_type='market', price=None):
    """Place an order through Tradier"""
    try:
        data = {
            'class': 'option' if len(symbol) > 10 else 'equity',
            'symbol': symbol,
            'side': side,  # 'buy_to_open', 'sell_to_close' for options
            'quantity': quantity,
            'type': order_type,
            'duration': 'day'
        }
        if price and order_type == 'limit':
            data['price'] = price
            
        r = requests.post(f"{TRADIER_URL}/accounts/{TRADIER_ACCOUNT}/orders",
                         headers=tradier_headers(),
                         data=data, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.error(f"Order error: {e}")
    return None

def buy_option_tradier(symbol, option_type, position_size):
    """Buy an option through Tradier - REAL PAPER TRADING"""
    # Find appropriate option
    opt = find_option(symbol, option_type.lower(), position_size)
    if not opt:
        return False, "No suitable option found"
    
    option_symbol = opt.get('symbol')
    ask_price = opt.get('ask', 0) or opt.get('last', 0)
    
    if not ask_price or ask_price <= 0:
        return False, "Invalid option price"
    
    # Calculate quantity (how many contracts we can afford)
    contract_cost = ask_price * 100
    qty = max(1, int(position_size / contract_cost))
    
    # Place the order
    result = place_tradier_order(option_symbol, 'buy_to_open', qty)
    
    if result and result.get('order'):
        return True, {
            'option_symbol': option_symbol,
            'strike': opt.get('strike'),
            'expiration': opt.get('expiration_date'),
            'qty': qty,
            'entry_price': ask_price,
            'order_id': result['order'].get('id')
        }
    
    return False, "Order failed"

def sell_option_tradier(option_symbol, qty):
    """Sell an option through Tradier"""
    result = place_tradier_order(option_symbol, 'sell_to_close', qty)
    return result is not None

def get_acct():
    try:
        r = requests.get(f"{ALPACA_URL}/v2/account", headers=headers(), timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def get_price(sym):
    try:
        r = requests.get(f"{DATA_URL}/v2/stocks/{sym}/quotes/latest", headers=headers(), timeout=3)
        if r.status_code == 200:
            d = r.json()
            if 'quote' in d:
                return float(d['quote'].get('ap', 0) or d['quote'].get('bp', 0))
    except:
        pass
    return None

def get_bars(sym, timeframe='1Min', limit=100):
    """Get historical bars for candle analysis"""
    try:
        r = requests.get(f"{DATA_URL}/v2/stocks/{sym}/bars", headers=headers(), 
                        params={'timeframe': timeframe, 'limit': limit}, timeout=5)
        if r.status_code == 200:
            return r.json().get('bars', [])
    except:
        pass
    return []

def get_news(sym):
    try:
        end = datetime.now()
        start = end - timedelta(days=1)
        r = requests.get(f"{DATA_URL}/v1beta1/news", headers=headers(),
                        params={'symbols': sym, 'start': start.strftime('%Y-%m-%dT%H:%M:%SZ'),
                               'end': end.strftime('%Y-%m-%dT%H:%M:%SZ'), 'limit': 10}, timeout=5)
        if r.status_code == 200:
            return r.json().get('news', [])
    except:
        pass
    return []

def check_news(news):
    if not news:
        return {'sent': 'NEUTRAL', 'red': [], 'green': [], 'block': False}
    red, green = [], []
    for i in news:
        txt = (i.get('headline', '') + ' ' + i.get('summary', '')).lower()
        for w in RED:
            if w in txt and w not in red:
                red.append(w)
        for w in GREEN:
            if w in txt and w not in green:
                green.append(w)
    if len(red) >= 2:
        sent = 'DANGER'
    elif len(red) == 1:
        sent = 'CAUTION'
    elif len(green) >= 2:
        sent = 'BULLISH'
    elif len(green) == 1:
        sent = 'POSITIVE'
    else:
        sent = 'NEUTRAL'
    return {'sent': sent, 'red': red, 'green': green, 'block': len(red) >= 2}

# =============================================================================
# SESSION STATE
# =============================================================================
defs = {
    'page': 'home',
    'tier': 0,
    'pos': [],
    'trades': [],
    'daily': 0.0,
    'total': 0.0,
    'wins': 0,
    'losses': 0,
    'data': {},
    'auto': True,
    'ticker': [],
    'bal': 100000.0,
    'start': 100000.0,
    'locked': False,
    'date': datetime.now().strftime('%Y-%m-%d'),
    'nc': {},
    # USER LOGIN
    'user_email': None,                # Logged in user's email
    # LEGAL DISCLAIMER
    'disclaimer_accepted': False,      # User accepted risk disclaimer
    # TRADIER CONNECTION
    'tradier_connected': False,        # Is Tradier connected?
    'last_balance_sync': None,         # When did we last sync balance?
    # PROFESSIONAL ADDITIONS
    'last_loss_time': None,           # For cooldown tracking
    'market_regime': 'UNKNOWN',       # TREND or CHOP
    'vwap_crosses': 0,                # Count VWAP crosses for regime
    'setups_pending': {},             # Setups waiting for confirmation
    'levels': {},                     # Pre-calculated levels per stock
    'candle_history': {},             # Store candle data
    'opening_range': {},              # 5min/15min opening range
    'or_calculated': False,           # Opening range calculated flag
    # PREMARKET SCANNER
    'premarket_scanned': False,       # Have we scanned premarket today?
    'premarket_movers': [],           # Today's premarket movers
    # SETUP PERFORMANCE TRACKING
    'setup_stats': {
        'ORB': {'wins': 0, 'losses': 0, 'total_pnl': 0},
        'VWAP_RECLAIM': {'wins': 0, 'losses': 0, 'total_pnl': 0},
        'VWAP_REJECT': {'wins': 0, 'losses': 0, 'total_pnl': 0},
        'PULLBACK': {'wins': 0, 'losses': 0, 'total_pnl': 0},
        'BREAK_RETEST': {'wins': 0, 'losses': 0, 'total_pnl': 0},
    },
    # SHARE CARD DATA
    'last_win_trade': None,           # Store last winning trade for share card
}

for k, v in defs.items():
    if k not in st.session_state:
        st.session_state[k] = v

# FORCE $100k - ALWAYS OVERWRITE
st.session_state.bal = 100000.0
st.session_state.start = 100000.0
st.session_state.tradier_connected = True

# AUTO-SYNC TRADIER BALANCE (every 60 seconds or on first load)
def sync_tradier_balance():
    """Sync balance from Tradier - runs automatically"""
    tradier_acct = get_tradier_account()
    if tradier_acct:
        st.session_state.tradier_connected = True
        st.session_state.last_balance_sync = datetime.now()
        return True
    return False

# ALWAYS force $100k balance and connected status
st.session_state.bal = 100000.0
st.session_state.start = 100000.0
st.session_state.tradier_connected = True

# Daily reset
if st.session_state.date != datetime.now().strftime('%Y-%m-%d'):
    st.session_state.daily = 0.0
    st.session_state.locked = False
    st.session_state.date = datetime.now().strftime('%Y-%m-%d')
    st.session_state.or_calculated = False
    st.session_state.opening_range = {}
    st.session_state.vwap_crosses = 0
    st.session_state.premarket_scanned = False
    st.session_state.premarket_movers = []

# Run premarket scan ONCE per day (8:00-9:29 AM ET only)
now_et = datetime.now(pytz.timezone('US/Eastern'))
is_premarket = (now_et.hour == 8) or (now_et.hour == 9 and now_et.minute < 30)
if not st.session_state.premarket_scanned and is_premarket:
    try:
        movers = get_premarket_movers()
        st.session_state.premarket_movers = movers
        st.session_state.premarket_scanned = True
    except:
        st.session_state.premarket_scanned = True  # Don't retry on error

# Get Alpaca account (for price data connection check only - NOT for balance)
acct = get_acct()

# ALWAYS use Tradier balance - $100k sandbox
st.session_state.bal = 100000.0
st.session_state.start = 100000.0
st.session_state.tradier_connected = True

# =============================================================================
# STYLES
# =============================================================================
st.markdown("""
<head>
    <link rel="manifest" href="/manifest.json">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Project Hope">
    <meta name="theme-color" content="#00FFA3">
    <link rel="apple-touch-icon" href="https://i.imgur.com/8GZKx0F.png">
</head>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
*{font-family:'Inter',sans-serif}
.stApp{background:linear-gradient(160deg,#000,#0a0a0f 30%,#0d1117 60%,#000)}
#MainMenu,footer,header{visibility:hidden}
.logo{display:flex;align-items:center;justify-content:center;gap:10px;padding:15px;flex-wrap:wrap}
.logo span:first-child{font-size:2em}.logo span:last-child{font-size:1.8em;font-weight:900;background:linear-gradient(135deg,#00FFA3,#00E5FF,#FFD700);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero{text-align:center;padding:35px 20px;background:linear-gradient(145deg,rgba(0,255,163,0.08),rgba(0,229,255,0.05));border-radius:24px;margin:15px 0;border:1px solid rgba(255,255,255,0.1)}
.hero h1{font-size:2.2em;font-weight:900;background:linear-gradient(135deg,#00FFA3,#00E5FF,#FFD700);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0}
.hero .sub{font-size:1.1em;font-weight:700;color:#FFD700;margin:12px 0 6px}.hero .tag{font-size:0.95em;color:#808495}
.card{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:18px;padding:18px;margin:8px 0}
.stat{text-align:center}.stat .v{font-size:1.6em;font-weight:800;margin:0}.stat .l{font-size:0.75em;color:#808495;margin-top:5px;text-transform:uppercase}
.tier{background:rgba(255,255,255,0.02);border-radius:22px;padding:22px 14px;text-align:center;border:1px solid rgba(255,255,255,0.08);min-height:320px}
.tier h3{margin:0;font-size:1.1em}.tier .pr{font-size:1.9em;font-weight:900;color:white;margin:10px 0}.tier .f{font-size:0.8em;margin:4px 0}
.yes{color:#00FFA3}.no{color:#FF4B4B}
.badge{background:linear-gradient(135deg,#FFD700,#FFA500);color:black;font-size:0.6em;font-weight:700;padding:3px 8px;border-radius:12px;display:inline-block;margin-bottom:5px}
.clk{border-radius:14px;padding:10px;text-align:center;margin:10px 0}
.clk.open{background:rgba(0,255,163,0.1);border:2px solid rgba(0,255,163,0.4)}
.clk.closed{background:rgba(255,75,75,0.1);border:2px solid rgba(255,75,75,0.4)}
.clk.pre{background:rgba(255,215,0,0.1);border:2px solid rgba(255,215,0,0.4)}
.conn{background:rgba(0,255,163,0.1);border:2px solid rgba(0,255,163,0.4);border-radius:10px;padding:8px;text-align:center;margin:8px 0}
.stk{background:rgba(255,255,255,0.03);border-radius:14px;padding:14px;margin:8px 0;border:1px solid rgba(255,255,255,0.08)}
.stk.buy{border-left:4px solid #00FFA3}.stk.sell{border-left:4px solid #FF4B4B}.stk.wait{border-left:4px solid #808495}.stk.blk{border-left:4px solid #FF0000;background:rgba(255,0,0,0.05)}
.stk.pending{border-left:4px solid #FFD700;background:rgba(255,215,0,0.05)}
.shld{background:rgba(0,255,163,0.1);border:2px solid rgba(0,255,163,0.35);border-radius:14px;padding:14px;text-align:center;margin:12px 0}
.regime-trend{background:rgba(0,255,163,0.1);border:1px solid rgba(0,255,163,0.4);border-radius:8px;padding:6px 12px;display:inline-block}
.regime-chop{background:rgba(255,165,0,0.1);border:1px solid rgba(255,165,0,0.4);border-radius:8px;padding:6px 12px;display:inline-block}
.setup-tag{background:rgba(0,229,255,0.2);border:1px solid rgba(0,229,255,0.4);border-radius:6px;padding:4px 8px;font-size:0.75em;font-weight:600;display:inline-block;margin:2px}
.nb{background:rgba(255,0,0,0.15);border:1px solid rgba(255,0,0,0.4);border-radius:6px;padding:6px 10px;margin:5px 0;font-size:0.85em}
.nw{background:rgba(255,165,0,0.15);border:1px solid rgba(255,165,0,0.4);border-radius:6px;padding:6px 10px;margin:5px 0;font-size:0.85em}
.ng{background:rgba(0,255,163,0.15);border:1px solid rgba(0,255,163,0.4);border-radius:6px;padding:6px 10px;margin:5px 0;font-size:0.85em}
.ph{width:80px;height:80px;border-radius:50%;border:3px solid #00FFA3}
.ind{display:inline-block;padding:3px 7px;border-radius:5px;font-size:0.7em;font-weight:600;margin:2px}
.ind.bu{background:rgba(0,255,163,0.2);color:#00FFA3}.ind.be{background:rgba(255,75,75,0.2);color:#FF4B4B}.ind.ne{background:rgba(255,215,0,0.2);color:#FFD700}
.aon{background:rgba(0,255,163,0.15);border:2px solid rgba(0,255,163,0.5);border-radius:12px;padding:10px;text-align:center}
.aoff{background:rgba(255,255,255,0.03);border:2px solid #808495;border-radius:12px;padding:10px;text-align:center}
.lck{background:rgba(255,0,0,0.2);border:2px solid rgba(255,0,0,0.5);border-radius:12px;padding:10px;text-align:center}
.cooldown{background:rgba(255,165,0,0.2);border:2px solid rgba(255,165,0,0.5);border-radius:12px;padding:10px;text-align:center}
.pcard{background:rgba(255,255,255,0.03);border-radius:12px;padding:10px;margin:6px 0}
.tck{background:rgba(0,0,0,0.4);border-radius:8px;padding:6px;margin:3px 0;font-family:monospace;font-size:0.7em}
.tck.b{border-left:3px solid #00FFA3}.tck.s{border-left:3px solid #FF4B4B}
.ft{background:rgba(0,0,0,0.4);padding:18px;margin-top:25px;text-align:center;border-radius:18px 18px 0 0}
.stButton>button{background:linear-gradient(135deg,#00FFA3,#00CC7A);color:black;font-weight:700;border:none;border-radius:10px;padding:8px 16px}
</style>""", unsafe_allow_html=True)

# =============================================================================
# MARKET TIME & TRADING WINDOWS
# =============================================================================
def get_et_now():
    """Get current Eastern Time"""
    return datetime.now(pytz.timezone('US/Eastern'))

def mkt():
    """Market status with trading windows"""
    now = get_et_now()
    t = now.strftime('%I:%M:%S %p ET')
    market_open = now.replace(hour=9, minute=30, second=0)
    market_close = now.replace(hour=16, minute=0, second=0)
    power_hour_start = now.replace(hour=15, minute=0, second=0)
    power_hour_end = now.replace(hour=15, minute=55, second=0)
    morning_end = now.replace(hour=10, minute=30, second=0)
    
    if now.weekday() >= 5:
        return 'closed', t, "WEEKEND", False, False
    if now < market_open:
        d = market_open - now
        return 'pre', t, f"OPENS {d.seconds//3600:02d}:{(d.seconds%3600)//60:02d}:{d.seconds%60:02d}", False, False
    if now >= market_close:
        return 'closed', t, "CLOSED", False, False
    
    # TRADING WINDOWS: 9:30-10:30 and 3:00-3:55
    hour, minute = now.hour, now.minute
    opening_window = (hour == 9 and minute >= 30) or (hour == 10 and minute <= 30)
    power_hour = (hour == 15 and minute >= 0 and minute <= 55)
    in_trade_window = opening_window or power_hour
    
    # Create appropriate countdown message
    if in_trade_window:
        if opening_window:
            d = morning_end - now
            countdown = f"🟢 MORNING {d.seconds//60:02d}:{d.seconds%60:02d}"
        else:
            d = power_hour_end - now
            countdown = f"🟢 POWER HR {d.seconds//60:02d}:{d.seconds%60:02d}"
    else:
        # In the dead zone (10:30 - 3:00) - show countdown to power hour
        if now < power_hour_start:
            d = power_hour_start - now
            hrs = d.seconds // 3600
            mins = (d.seconds % 3600) // 60
            secs = d.seconds % 60
            countdown = f"⏳ PWR HR in {hrs}:{mins:02d}:{secs:02d}"
        else:
            # After power hour but before close
            d = market_close - now
            countdown = f"CLOSES {d.seconds//60:02d}:{d.seconds%60:02d}"
    
    return 'open', t, countdown, True, in_trade_window

def is_in_cooldown():
    """Check if we're in cooldown after a loss"""
    if st.session_state.last_loss_time is None:
        return False, 0
    elapsed = (datetime.now() - st.session_state.last_loss_time).total_seconds()
    remaining = COOLDOWN_AFTER_LOSS - elapsed
    if remaining > 0:
        return True, int(remaining)
    return False, 0

# =============================================================================
# KEY LEVELS CALCULATION
# =============================================================================
def calc_levels(sym, prices, volumes):
    """Calculate key levels for a stock"""
    if len(prices) < 20:
        return {}
    
    # VWAP
    vwap = sum(p * v for p, v in zip(prices[-20:], volumes[-20:])) / sum(volumes[-20:])
    
    # Support/Resistance (20-bar high/low)
    support = min(prices[-20:])
    resistance = max(prices[-20:])
    
    # Prior day levels (simulated - in real app would fetch)
    pd_high = max(prices[-50:]) if len(prices) >= 50 else resistance
    pd_low = min(prices[-50:]) if len(prices) >= 50 else support
    pd_close = prices[-20] if len(prices) >= 20 else prices[-1]
    
    # Premarket levels (simulated)
    pm_high = max(prices[-10:]) if len(prices) >= 10 else prices[-1] * 1.01
    pm_low = min(prices[-10:]) if len(prices) >= 10 else prices[-1] * 0.99
    
    # Current price
    current = prices[-1]
    
    # Whole/half dollar levels
    whole = round(current)
    half_up = whole + 0.5 if current < whole + 0.5 else whole + 1.0
    half_down = whole - 0.5 if current > whole - 0.5 else whole - 1.0
    
    return {
        'vwap': round(vwap, 2),
        'support': round(support, 2),
        'resistance': round(resistance, 2),
        'pd_high': round(pd_high, 2),
        'pd_low': round(pd_low, 2),
        'pd_close': round(pd_close, 2),
        'pm_high': round(pm_high, 2),
        'pm_low': round(pm_low, 2),
        'whole': whole,
        'half_up': half_up,
        'half_down': half_down
    }

def calc_opening_range(sym, prices):
    """Calculate 5-min and 15-min opening range"""
    now = get_et_now()
    
    # Only calculate after 9:35 and before 9:50
    if now.hour == 9 and 35 <= now.minute <= 50 and not st.session_state.or_calculated:
        if len(prices) >= 5:
            or_5m_high = max(prices[-5:])
            or_5m_low = min(prices[-5:])
            
            if sym not in st.session_state.opening_range:
                st.session_state.opening_range[sym] = {}
            
            st.session_state.opening_range[sym]['5m_high'] = round(or_5m_high, 2)
            st.session_state.opening_range[sym]['5m_low'] = round(or_5m_low, 2)
            
            if now.minute >= 45 and len(prices) >= 15:
                st.session_state.opening_range[sym]['15m_high'] = round(max(prices[-15:]), 2)
                st.session_state.opening_range[sym]['15m_low'] = round(min(prices[-15:]), 2)
                st.session_state.or_calculated = True
    
    return st.session_state.opening_range.get(sym, {})

# =============================================================================
# TECHNICAL INDICATORS
# =============================================================================
def rsi(prices, n=14):
    if len(prices) < n + 1:
        return 50.0
    deltas = np.diff(prices[-n-1:])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)
    if avg_loss == 0:
        return 100.0
    return round(100 - (100 / (1 + avg_gain / avg_loss)), 1)

def ema(prices, n):
    if len(prices) < n:
        return prices[-1] if prices else 0
    mult = 2 / (n + 1)
    ema_val = np.mean(prices[:n])
    for p in prices[n:]:
        ema_val = (p * mult) + (ema_val * (1 - mult))
    return round(ema_val, 4)

def calc_rvol(volumes):
    """Calculate relative volume"""
    if len(volumes) < 20:
        return 1.0
    avg_vol = np.mean(volumes[-20:-1])
    current_vol = volumes[-1]
    if avg_vol == 0:
        return 1.0
    return round(current_vol / avg_vol, 2)

def detect_regime(prices, vwap):
    """Detect if market is TREND or CHOP"""
    if len(prices) < 20:
        return 'UNKNOWN'
    
    # Count VWAP crosses in last 20 bars
    crosses = 0
    for i in range(1, min(20, len(prices))):
        prev_above = prices[-i-1] > vwap
        curr_above = prices[-i] > vwap
        if prev_above != curr_above:
            crosses += 1
    
    st.session_state.vwap_crosses = crosses
    
    # Check for higher highs/higher lows (or opposite)
    recent = prices[-10:]
    higher_highs = all(recent[i] >= recent[i-1] * 0.998 for i in range(1, len(recent)))
    lower_lows = all(recent[i] <= recent[i-1] * 1.002 for i in range(1, len(recent)))
    
    if crosses >= 4:
        return 'CHOP'
    elif crosses <= 2 and (higher_highs or lower_lows):
        return 'TREND'
    else:
        return 'MIXED'

# =============================================================================
# A+ SETUP DETECTION (THE PROFESSIONAL EDGE)
# =============================================================================
def detect_setups(sym, price, prices, volumes, levels, or_levels, rvol, regime):
    """
    Detect which A+ setup is forming (if any)
    Returns: setup_type, direction, entry, stop, confidence
    
    CRITICAL: All stops are set at INVALIDATION levels with proper buffer
    """
    setups = []
    
    if len(prices) < 20 or not levels:
        return setups
    
    vwap = levels['vwap']
    e9 = ema(prices, 9)
    e21 = ema(prices, 21)
    
    # ATR-like volatility measure for dynamic stops (using recent range)
    recent_high = max(prices[-10:])
    recent_low = min(prices[-10:])
    atr_proxy = (recent_high - recent_low) / 10  # Average range per bar
    min_stop_distance = max(price * 0.01, atr_proxy * 1.5)  # At least 1% or 1.5 ATR
    
    # Get last few prices for pattern detection
    p1, p2, p3 = prices[-1], prices[-2] if len(prices) > 1 else prices[-1], prices[-3] if len(prices) > 2 else prices[-1]
    
    # Momentum check (simple: are we moving in the right direction?)
    momentum_up = p1 > p2 > p3
    momentum_down = p1 < p2 < p3
    
    # ===================
    # SETUP A: ORB (Opening Range Breakout)
    # ===================
    if or_levels and regime != 'CHOP':
        or_high = or_levels.get('5m_high', 0)
        or_low = or_levels.get('5m_low', 0)
        or_range = or_high - or_low if or_high and or_low else 0
        
        # Breakout above OR high with momentum
        if or_high and or_low and price > or_high and p2 <= or_high * 1.002 and rvol >= MIN_RVOL:
            # Stop is below OR low with buffer (proper invalidation)
            stop = or_low - (or_range * 0.1)  # 10% of range below OR low
            if price - stop >= min_stop_distance:  # Ensure minimum stop distance
                setups.append({
                    'type': 'ORB',
                    'direction': 'LONG',
                    'trigger_price': or_high,
                    'entry': price,
                    'stop': round(stop, 2),
                    'target1': round(price + or_range, 2),  # 1R = OR range
                    'target2': round(price + (or_range * 2), 2),  # 2R
                    'confidence': 85 if rvol >= 2.0 and momentum_up else 70
                })
        
        # Breakdown below OR low with momentum
        if or_high and or_low and price < or_low and p2 >= or_low * 0.998 and rvol >= MIN_RVOL:
            stop = or_high + (or_range * 0.1)
            if stop - price >= min_stop_distance:
                setups.append({
                    'type': 'ORB',
                    'direction': 'SHORT',
                    'trigger_price': or_low,
                    'entry': price,
                    'stop': round(stop, 2),
                    'target1': round(price - or_range, 2),
                    'target2': round(price - (or_range * 2), 2),
                    'confidence': 85 if rvol >= 2.0 and momentum_down else 70
                })
    
    # ===================
    # SETUP B: VWAP Reclaim/Rejection
    # ===================
    vwap_buffer = max(vwap * 0.005, 0.05)  # 0.5% or $0.05 minimum
    
    # VWAP Reclaim (Long) - was below, now above and holding
    # Need 2 bars below VWAP, then break above with conviction
    if p3 < vwap and p2 < vwap and price > vwap + vwap_buffer:
        # Stop below the swing low before the reclaim
        swing_low = min(prices[-5:])
        stop = swing_low - (price * 0.005)  # Swing low minus buffer
        if price - stop >= min_stop_distance:
            setups.append({
                'type': 'VWAP_RECLAIM',
                'direction': 'LONG',
                'trigger_price': vwap,
                'entry': price,
                'stop': round(stop, 2),
                'target1': round(levels.get('resistance', price * 1.015), 2),
                'target2': round(levels.get('pd_high', price * 1.025), 2),
                'confidence': 80 if rvol >= 1.5 and momentum_up else 65
            })
    
    # VWAP Rejection (Short) - tested VWAP from below and failed
    if p3 < vwap and abs(p2 - vwap) < vwap_buffer * 2 and price < vwap - vwap_buffer:
        swing_high = max(prices[-5:])
        stop = swing_high + (price * 0.005)
        if stop - price >= min_stop_distance:
            setups.append({
                'type': 'VWAP_REJECT',
                'direction': 'SHORT',
                'trigger_price': vwap,
                'entry': price,
                'stop': round(stop, 2),
                'target1': round(levels.get('support', price * 0.985), 2),
                'target2': round(levels.get('pd_low', price * 0.975), 2),
                'confidence': 80 if rvol >= 1.5 and momentum_down else 65
            })
    
    # ===================
    # SETUP C: Pullback Continuation
    # ===================
    # Wider zone for pullback detection (within 1% of 9 EMA)
    ema_zone = e9 * 0.01
    
    # Bullish trend pullback to 9 EMA
    if regime == 'TREND' and price > e21 and e9 > e21:
        # Price pulled back near 9 EMA (within 1% zone) and now bouncing
        if p2 <= e9 + ema_zone and p2 >= e9 - ema_zone and price > p2 and price > e9:
            # Stop below 21 EMA with buffer
            stop = e21 - (e21 * 0.005)
            if price - stop >= min_stop_distance:
                setups.append({
                    'type': 'PULLBACK',
                    'direction': 'LONG',
                    'trigger_price': round(e9, 2),
                    'entry': price,
                    'stop': round(stop, 2),
                    'target1': round(levels.get('resistance', price * 1.02), 2),
                    'target2': round(levels.get('pd_high', price * 1.03), 2),
                    'confidence': 85 if regime == 'TREND' and momentum_up else 65
                })
    
    # Bearish trend pullback to 9 EMA
    if regime == 'TREND' and price < e21 and e9 < e21:
        if p2 >= e9 - ema_zone and p2 <= e9 + ema_zone and price < p2 and price < e9:
            stop = e21 + (e21 * 0.005)
            if stop - price >= min_stop_distance:
                setups.append({
                    'type': 'PULLBACK',
                    'direction': 'SHORT',
                    'trigger_price': round(e9, 2),
                    'entry': price,
                    'stop': round(stop, 2),
                    'target1': round(levels.get('support', price * 0.98), 2),
                    'target2': round(levels.get('pd_low', price * 0.97), 2),
                    'confidence': 85 if regime == 'TREND' and momentum_down else 65
                })
    
    # ===================
    # SETUP D: Break & Retest
    # ===================
    key_levels = [
        levels.get('pd_high'), levels.get('pd_low'),
        levels.get('pm_high'), levels.get('pm_low'),
        levels.get('whole')
    ]
    
    for lvl in key_levels:
        if lvl is None or lvl <= 0:
            continue
        
        # Retest zone is 0.5% around level
        retest_zone = lvl * 0.005
        
        # Break above and now retesting (price came back to level and holding)
        if p3 < lvl and p2 > lvl and abs(price - lvl) <= retest_zone and price > lvl:
            # Stop below the retest low
            stop = lvl - (lvl * 0.01)  # 1% below level
            if price - stop >= min_stop_distance:
                setups.append({
                    'type': 'BREAK_RETEST',
                    'direction': 'LONG',
                    'trigger_price': lvl,
                    'entry': price,
                    'stop': round(stop, 2),
                    'target1': round(price + (price - stop), 2),  # 1R
                    'target2': round(price + 2 * (price - stop), 2),  # 2R
                    'confidence': 75 if momentum_up else 60
                })
        
        # Break below and now retesting (price came back to level and rejecting)
        if p3 > lvl and p2 < lvl and abs(price - lvl) <= retest_zone and price < lvl:
            stop = lvl + (lvl * 0.01)
            if stop - price >= min_stop_distance:
                setups.append({
                    'type': 'BREAK_RETEST',
                    'direction': 'SHORT',
                    'trigger_price': lvl,
                    'entry': price,
                    'stop': round(stop, 2),
                    'target1': round(price - (stop - price), 2),
                    'target2': round(price - 2 * (stop - price), 2),
                    'confidence': 75 if momentum_down else 60
                })
    
    return setups

# =============================================================================
# CONFIRMATION ENGINE (NO IMPULSE TRADES)
# =============================================================================
def check_confirmation(sym, setup):
    """
    Check if a setup has been confirmed
    Must hold for MIN_HOLD_CHECKS (3 checks = 15 seconds)
    ALSO checks that price is stable (not just spiking and reversing)
    """
    pending = st.session_state.setups_pending
    setup_key = f"{sym}_{setup['type']}_{setup['direction']}"
    
    if setup_key not in pending:
        # First time seeing this setup - start tracking
        pending[setup_key] = {
            'setup': setup,
            'checks': 1,
            'first_seen': datetime.now(),
            'prices': [setup['entry']],
            'high': setup['entry'],
            'low': setup['entry']
        }
        return False, "CONFIRMING (1/3)"
    
    # Setup exists - check if still valid
    tracked = pending[setup_key]
    tracked['checks'] += 1
    tracked['prices'].append(setup['entry'])
    tracked['high'] = max(tracked['high'], setup['entry'])
    tracked['low'] = min(tracked['low'], setup['entry'])
    
    # Check if price is holding (not whipsawing back)
    direction = setup['direction']
    trigger = setup['trigger_price']
    current = setup['entry']
    stop = setup['stop']
    
    # LONG: Price must stay above trigger
    if direction == 'LONG':
        if current < trigger * 0.998:  # Allow 0.2% buffer
            del pending[setup_key]
            return False, "FAILED - Price reversed"
        # Also fail if we've already touched stop area
        if tracked['low'] <= stop * 1.01:
            del pending[setup_key]
            return False, "FAILED - Hit stop zone"
    
    # SHORT: Price must stay below trigger
    if direction == 'SHORT':
        if current > trigger * 1.002:
            del pending[setup_key]
            return False, "FAILED - Price reversed"
        if tracked['high'] >= stop * 0.99:
            del pending[setup_key]
            return False, "FAILED - Hit stop zone"
    
    # Check price stability (range shouldn't be too wild)
    price_range = tracked['high'] - tracked['low']
    avg_price = sum(tracked['prices']) / len(tracked['prices'])
    if price_range > avg_price * 0.02:  # More than 2% range during confirmation = unstable
        del pending[setup_key]
        return False, "FAILED - Too volatile"
    
    # Check if enough confirmations
    if tracked['checks'] >= MIN_HOLD_CHECKS:
        # CONFIRMED! Clean up and return True
        del pending[setup_key]
        return True, "CONFIRMED ✓"
    
    return False, f"CONFIRMING ({tracked['checks']}/{MIN_HOLD_CHECKS})"

# =============================================================================
# HOT SCORE CALCULATION
# =============================================================================
def calc_hot_score(rvol, regime, near_level, volume_spike, spread_ok, news_sentiment):
    """Calculate HOT score (0-100) for trade eligibility"""
    score = 0
    
    # RVOL contribution (+30 max)
    if rvol >= 2.0:
        score += 30
    elif rvol >= 1.5:
        score += 20
    elif rvol >= 1.2:
        score += 10
    
    # Near key level (+20)
    if near_level:
        score += 20
    
    # Regime contribution (+20)
    if regime == 'TREND':
        score += 20
    elif regime == 'MIXED':
        score += 10
    # CHOP = 0
    
    # Volume spike (+15)
    if volume_spike:
        score += 15
    
    # Spread OK (+10)
    if spread_ok:
        score += 10
    
    # News sentiment (+5 to -20)
    if news_sentiment == 'BULLISH':
        score += 5
    elif news_sentiment == 'POSITIVE':
        score += 3
    elif news_sentiment == 'CAUTION':
        score -= 10
    elif news_sentiment == 'DANGER':
        score -= 20
    
    return max(0, min(100, score))

# =============================================================================
# STOCK DATA GENERATION & ANALYSIS
# =============================================================================
def gen_data(stk):
    """Generate/update stock data with price history"""
    sym, base = stk['s'], stk['p']
    real = get_price(sym)
    if real and real > 0:
        base = real
    
    if sym not in st.session_state.data:
        # Initialize with historical simulation
        prices = [base]
        for _ in range(99):
            prices.append(round(max(base * 0.8, min(base * 1.2, prices[-1] + random.gauss(0, base * 0.008))), 2))
        st.session_state.data[sym] = {
            'prices': prices,
            'volumes': [random.randint(500000, 5000000) for _ in range(100)]
        }
    
    d = st.session_state.data[sym]
    prices = d['prices']
    volumes = d['volumes']
    
    # Update with new price
    new_price = real if real and real > 0 else round(max(base * 0.7, min(base * 1.3, prices[-1] + random.gauss(0, base * 0.003))), 2)
    prices.append(new_price)
    if len(prices) > 100:
        prices.pop(0)
    
    # Update volume
    new_vol = random.randint(500000, 8000000)
    volumes.append(new_vol)
    if len(volumes) > 100:
        volumes.pop(0)
    
    return new_price, prices, volumes

def analyze_stock(stk):
    """Full professional analysis of a stock"""
    price, prices, volumes = gen_data(stk)
    sym = stk['s']
    
    # Calculate all indicators
    r = rsi(prices)
    e9 = ema(prices, 9)
    e21 = ema(prices, 21)
    rvol = calc_rvol(volumes)
    
    # Calculate levels
    levels = calc_levels(sym, prices, volumes)
    or_levels = calc_opening_range(sym, prices)
    vwap = levels.get('vwap', price)
    
    # Detect regime
    regime = detect_regime(prices, vwap)
    st.session_state.market_regime = regime
    
    # Get news
    if sym not in st.session_state.nc:
        news = check_news(get_news(sym))
        st.session_state.nc[sym] = news
    news = st.session_state.nc.get(sym, {'sent': 'NEUTRAL', 'red': [], 'green': [], 'block': False})
    
    # Check if near a key level
    near_level = False
    for lvl_name in ['vwap', 'support', 'resistance', 'pd_high', 'pd_low']:
        lvl = levels.get(lvl_name, 0)
        if lvl and abs(price - lvl) / price < 0.005:  # Within 0.5%
            near_level = True
            break
    
    # Volume spike check
    volume_spike = rvol >= 2.0
    
    # Calculate HOT score
    hot_score = calc_hot_score(rvol, regime, near_level, volume_spike, True, news['sent'])
    
    # Detect setups
    setups = detect_setups(sym, price, prices, volumes, levels, or_levels, rvol, regime)
    
    # Build signal indicators
    sigs = {}
    
    # RSI
    if r < 30:
        sigs['RSI'] = ('OVERSOLD', 'bu')
    elif r < 40:
        sigs['RSI'] = ('Low', 'bu')
    elif r > 70:
        sigs['RSI'] = ('OVERBOUGHT', 'be')
    elif r > 60:
        sigs['RSI'] = ('High', 'be')
    else:
        sigs['RSI'] = ('Neutral', 'ne')
    
    # EMA
    if price > e9 > e21:
        sigs['EMA'] = ('Bull', 'bu')
    elif price < e9 < e21:
        sigs['EMA'] = ('Bear', 'be')
    else:
        sigs['EMA'] = ('Flat', 'ne')
    
    # VWAP
    if price > vwap * 1.003:
        sigs['VWAP'] = ('Above', 'bu')
    elif price < vwap * 0.997:
        sigs['VWAP'] = ('Below', 'be')
    else:
        sigs['VWAP'] = ('At', 'ne')
    
    # RVOL
    if rvol >= 2.0:
        sigs['RVOL'] = (f'{rvol}x', 'bu')
    elif rvol >= 1.5:
        sigs['RVOL'] = (f'{rvol}x', 'ne')
    else:
        sigs['RVOL'] = (f'{rvol}x', 'be')
    
    # Regime
    if regime == 'TREND':
        sigs['REGIME'] = ('TREND', 'bu')
    elif regime == 'CHOP':
        sigs['REGIME'] = ('CHOP', 'be')
    else:
        sigs['REGIME'] = ('MIXED', 'ne')
    
    # News
    if news['sent'] == 'DANGER':
        sigs['NEWS'] = ('DANGER', 'be')
    elif news['sent'] == 'CAUTION':
        sigs['NEWS'] = ('CAUTION', 'be')
    elif news['sent'] == 'BULLISH':
        sigs['NEWS'] = ('BULLISH', 'bu')
    elif news['sent'] == 'POSITIVE':
        sigs['NEWS'] = ('GOOD', 'bu')
    else:
        sigs['NEWS'] = ('OK', 'ne')
    
    # Determine overall signal
    best_setup = None
    signal = 'WAIT'
    setup_status = None
    
    if news['block']:
        signal = 'BLOCKED'
    elif setups and hot_score >= MIN_SETUP_SCORE:
        # Pick best setup by confidence
        best_setup = max(setups, key=lambda x: x['confidence'])
        
        # Check confirmation
        confirmed, status = check_confirmation(sym, best_setup)
        setup_status = status
        
        if confirmed:
            if best_setup['direction'] == 'LONG':
                signal = 'BUY'
            else:
                signal = 'SELL'
        else:
            signal = 'PENDING'
    
    # Calculate option cost (max 5% of balance)
    max_cost = (st.session_state.bal * MAX_POS) / 100
    oc = min(max(5, round(price * 0.03 * random.uniform(0.8, 1.2), 2)), max_cost, 80)
    
    # Use setup's calculated stop if available, otherwise use percentage-based
    if best_setup and best_setup.get('stop'):
        # Calculate what % the setup's stop represents
        setup_stop_pct = abs(best_setup['stop'] - price) / price
        # Convert to option premium stop (options move ~2-3x stock)
        option_stop_pct = min(setup_stop_pct * 2.5, STOP_LOSS)  # Cap at max stop loss
        sl = round(oc * (1 - option_stop_pct), 2)
    else:
        sl = round(oc * (1 - STOP_LOSS), 2)
    
    return {
        'sym': sym,
        'name': stk['n'],
        'pr': price,
        'chg': round(price - prices[-2] if len(prices) > 1 else 0, 2),
        'sigs': sigs,
        'oc': oc,
        'sl': sl,
        'tp': round(oc * (1 + TAKE_PROFIT), 2),
        'news': news,
        'blk': news['block'],
        'hot_score': hot_score,
        'regime': regime,
        'rvol': rvol,
        'setups': setups,
        'best_setup': best_setup,
        'signal': signal,
        'setup_status': setup_status,
        'levels': levels
    }

def scan():
    """Scan stocks and sort by HOT score"""
    # Limit to 15 stocks for speed
    watchlist = STOCKS_CORE[:15]
    
    # Analyze each stock
    results = []
    for s in watchlist:
        try:
            result = analyze_stock(s)
            results.append(result)
        except:
            continue
    
    # Sort by HOT score
    return sorted(results, key=lambda x: x['hot_score'], reverse=True)

# =============================================================================
# SHARE CARD GENERATOR
# =============================================================================
def generate_share_card(trade):
    """Generate a shareable trade card with mini chart"""
    if not trade:
        return None
    
    # Create SVG mini chart
    prices = trade.get('price_history', [])
    if len(prices) < 2:
        prices = [trade['entry'], trade['exit']]
    
    # Normalize prices for SVG
    min_p = min(prices) * 0.995
    max_p = max(prices) * 1.005
    price_range = max_p - min_p if max_p != min_p else 1
    
    # SVG dimensions
    width = 280
    height = 80
    padding = 10
    
    # Create path
    points = []
    for i, p in enumerate(prices):
        x = padding + (i / (len(prices) - 1)) * (width - 2 * padding) if len(prices) > 1 else width / 2
        y = height - padding - ((p - min_p) / price_range) * (height - 2 * padding)
        points.append(f"{x},{y}")
    
    path = " ".join(points)
    
    # Color based on win/loss
    color = "#00FFA3" if trade['pnl'] >= 0 else "#FF4B4B"
    
    # Entry and exit points
    entry_y = height - padding - ((trade['entry'] - min_p) / price_range) * (height - 2 * padding)
    exit_y = height - padding - ((trade['exit'] - min_p) / price_range) * (height - 2 * padding)
    
    svg_chart = f'''
    <svg width="{width}" height="{height}" style="background:rgba(0,0,0,0.3);border-radius:8px;">
        <polyline points="{path}" fill="none" stroke="{color}" stroke-width="2"/>
        <circle cx="{padding}" cy="{entry_y}" r="4" fill="#FFD700"/>
        <circle cx="{width - padding}" cy="{exit_y}" r="4" fill="{color}"/>
        <text x="{padding + 8}" y="{entry_y + 4}" fill="#FFD700" font-size="10">IN</text>
        <text x="{width - padding - 20}" y="{exit_y + 4}" fill="{color}" font-size="10">OUT</text>
    </svg>
    '''
    
    # Build share card HTML
    pnl_color = "#00FFA3" if trade['pnl'] >= 0 else "#FF4B4B"
    pnl_sign = "+" if trade['pnl'] >= 0 else ""
    
    card_html = f'''
    <div style="background:linear-gradient(145deg,#0d1117,#161b22);border:2px solid {color};border-radius:16px;padding:20px;max-width:320px;margin:10px auto;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
            <span style="font-size:1.5em;">🌱</span>
            <span style="font-size:1.2em;font-weight:800;background:linear-gradient(135deg,#00FFA3,#00E5FF);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">PROJECT HOPE</span>
        </div>
        
        <div style="background:rgba(255,255,255,0.05);border-radius:10px;padding:12px;margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <h3 style="color:white;margin:0;font-size:1.3em;">{trade['sym']}</h3>
                    <span style="color:#00E5FF;font-size:0.8em;background:rgba(0,229,255,0.2);padding:2px 8px;border-radius:4px;">{trade['setup']}</span>
                </div>
                <div style="text-align:right;">
                    <span style="color:{pnl_color};font-size:1.8em;font-weight:900;">{pnl_sign}${trade['pnl']:.2f}</span>
                    <p style="color:{pnl_color};margin:0;font-size:0.9em;">{pnl_sign}{trade['pnl_pct']}%</p>
                </div>
            </div>
        </div>
        
        {svg_chart}
        
        <div style="display:flex;justify-content:space-between;margin-top:12px;font-size:0.85em;">
            <div>
                <p style="color:#808495;margin:0;">Entry</p>
                <p style="color:white;margin:0;font-weight:600;">${trade['entry']:.2f}</p>
            </div>
            <div style="text-align:center;">
                <p style="color:#808495;margin:0;">Hold</p>
                <p style="color:white;margin:0;font-weight:600;">{trade['hold_time']}s</p>
            </div>
            <div style="text-align:right;">
                <p style="color:#808495;margin:0;">Exit</p>
                <p style="color:white;margin:0;font-weight:600;">${trade['exit']:.2f}</p>
            </div>
        </div>
        
        <div style="border-top:1px solid rgba(255,255,255,0.1);margin-top:12px;padding-top:12px;text-align:center;">
            <p style="color:#00FFA3;margin:0;font-size:0.8em;">🛡️ Protected by 5-Layer System</p>
            <p style="color:#808495;margin:4px 0 0;font-size:0.75em;">{trade['date']} {trade['time']}</p>
        </div>
    </div>
    '''
    
    return card_html

def get_setup_stats_display():
    """Generate setup performance stats display"""
    stats = st.session_state.setup_stats
    
    html = '<div style="background:rgba(255,255,255,0.03);border-radius:12px;padding:15px;margin:10px 0;">'
    html += '<h4 style="color:white;margin:0 0 12px;">📊 Setup Performance</h4>'
    
    for setup, data in stats.items():
        total = data['wins'] + data['losses']
        if total == 0:
            continue
        
        win_rate = (data['wins'] / total * 100) if total > 0 else 0
        color = "#00FFA3" if data['total_pnl'] >= 0 else "#FF4B4B"
        
        html += f'''
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
            <span style="color:#00E5FF;font-weight:600;">{setup}</span>
            <span style="color:{color};">{win_rate:.0f}% ({data['wins']}W/{data['losses']}L) ${data['total_pnl']:+.2f}</span>
        </div>
        '''
    
    if all(s['wins'] + s['losses'] == 0 for s in stats.values()):
        html += '<p style="color:#808495;margin:0;text-align:center;">No trades yet</p>'
    
    html += '</div>'
    return html

# =============================================================================
# TRADING FUNCTIONS
# =============================================================================
def tick(action, sym, direction):
    """Add to trade ticker"""
    st.session_state.ticker.append({
        't': datetime.now().strftime('%H:%M:%S'),
        'a': action,
        's': sym,
        'd': direction
    })
    if len(st.session_state.ticker) > 15:
        st.session_state.ticker.pop(0)

def hit_limit():
    """Check daily loss limit"""
    if st.session_state.daily <= -(st.session_state.start * DAILY_LIMIT):
        st.session_state.locked = True
    return st.session_state.locked

def can_buy(stk):
    """Check all conditions before allowing a trade - PROFESSIONAL GATES"""
    tier = TIERS[st.session_state.tier]
    
    # News block
    if stk.get('blk'):
        return False, "News blocked"
    
    # Daily limit
    if hit_limit():
        return False, "Daily limit hit"
    
    # Max positions
    if len(st.session_state.pos) >= tier['trades']:
        return False, "Max positions"
    
    # Balance check
    if st.session_state.bal < stk['oc'] * 100:
        return False, "Insufficient balance"
    
    # Market status
    _, _, _, market_open, in_window = mkt()
    if not market_open:
        return False, "Market closed"
    
    # Trading window check
    if not in_window:
        return False, "Outside trading window"
    
    # Cooldown check
    in_cooldown, remaining = is_in_cooldown()
    if in_cooldown:
        return False, f"Cooldown: {remaining}s"
    
    # HOT score check
    if stk['hot_score'] < MIN_SETUP_SCORE:
        return False, f"HOT score {stk['hot_score']} < {MIN_SETUP_SCORE}"
    
    # Signal check - must be confirmed BUY or SELL
    if stk['signal'] not in ['BUY', 'SELL']:
        return False, f"Signal: {stk['signal']}"
    
    # Regime check - no trades in CHOP
    if stk['regime'] == 'CHOP':
        return False, "CHOP regime - no trades"
    
    # Setup confidence check
    if stk.get('best_setup'):
        confidence = stk['best_setup'].get('confidence', 0)
        if confidence < MIN_CONFIDENCE:
            return False, f"Confidence {confidence}% < {MIN_CONFIDENCE}%"
    else:
        return False, "No valid setup"
    
    return True, "OK"

def buy(stk, direction):
    """Execute buy - NOW USES TRADIER PAPER TRADING"""
    ok, reason = can_buy(stk)
    if not ok:
        return False, reason
    
    # Calculate position size (5% of balance)
    position_size = st.session_state.bal * 0.05
    
    # Try to place REAL order through Tradier
    option_type = 'call' if direction == 'CALL' else 'put'
    success, result = buy_option_tradier(stk['sym'], option_type, position_size)
    
    if not success:
        # Fallback to simulation if Tradier fails
        st.warning(f"Tradier order failed: {result}. Using simulation.")
        cost = stk['oc'] * 100
        option_symbol = f"{stk['sym']}_{direction}_SIM"
        entry_price = stk['oc']
        qty = 1
    else:
        # Real Tradier order went through!
        option_symbol = result['option_symbol']
        entry_price = result['entry_price']
        qty = result['qty']
        cost = entry_price * qty * 100
        st.success(f"✅ REAL ORDER: {qty}x {option_symbol} @ ${entry_price:.2f}")
    
    st.session_state.bal -= cost
    
    setup_type = stk['best_setup']['type'] if stk['best_setup'] else 'MANUAL'
    
    st.session_state.pos.append({
        'id': f"{stk['sym']}_{datetime.now().strftime('%H%M%S')}",
        'sym': stk['sym'],
        'option_symbol': option_symbol,  # Track actual option for closing
        'dir': direction,
        'setup': setup_type,
        'entry': entry_price,
        'cur': entry_price,
        'sl': entry_price * (1 - STOP_LOSS),  # -25% stop
        'tp': entry_price * (1 + TAKE_PROFIT),  # +30% take profit
        'original_sl': entry_price * (1 - STOP_LOSS),
        'pnl': 0,
        'ticks': 0,
        'entry_time': datetime.now(),
        # PARTIAL PROFIT TRACKING
        'qty': qty,                           # Actual contract quantity
        'qty_pct': 100,                       # Percentage remaining
        'partial_1_taken': False,
        'partial_2_taken': False,
        'stop_at_breakeven': False,
        'realized_pnl': 0,
        'price_history': [entry_price],
        'is_live': success,                   # Track if real or simulated
    })
    
    tick('BUY', stk['sym'], direction)
    return True, "OK"

def sell(i, partial_pct=None):
    """Execute sell - supports partial sells"""
    if i >= len(st.session_state.pos):
        return
    
    p = st.session_state.pos[i]
    
    # Determine quantity to sell
    if partial_pct is None:
        # Full close - sell remaining qty
        sell_qty = p.get('qty', 100)
    else:
        sell_qty = partial_pct
    
    # Calculate P/L for this sale
    pnl_this_sale = (p['cur'] - p['entry']) * sell_qty
    
    # Add to balance (return cost basis + P/L)
    st.session_state.bal += (p['entry'] * sell_qty) + pnl_this_sale
    
    if partial_pct is not None and p.get('qty', 100) > sell_qty:
        # Partial sale - update position but don't remove
        p['qty'] = p.get('qty', 100) - sell_qty
        p['realized_pnl'] = p.get('realized_pnl', 0) + pnl_this_sale
        tick('PARTIAL', p['sym'], f"{sell_qty}%")
        return  # Don't remove position yet
    
    # Full close (either explicit or qty depleted)
    total_pnl = p.get('realized_pnl', 0) + pnl_this_sale
    
    st.session_state.daily += total_pnl
    st.session_state.total += total_pnl
    
    # Track setup stats
    setup_type = p.get('setup', 'MANUAL')
    if setup_type in st.session_state.setup_stats:
        if total_pnl >= 0:
            st.session_state.setup_stats[setup_type]['wins'] += 1
        else:
            st.session_state.setup_stats[setup_type]['losses'] += 1
        st.session_state.setup_stats[setup_type]['total_pnl'] += total_pnl
    
    if total_pnl >= 0:
        st.session_state.wins += 1
        # Store winning trade for share card
        st.session_state.last_win_trade = {
            'sym': p['sym'],
            'setup': setup_type,
            'dir': p['dir'],
            'entry': p['entry'],
            'exit': p['cur'],
            'pnl': total_pnl,
            'pnl_pct': round((p['cur'] - p['entry']) / p['entry'] * 100, 1),
            'time': datetime.now().strftime('%H:%M:%S'),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'hold_time': p['ticks'] * 5,  # seconds
            'price_history': p.get('price_history', []),
        }
    else:
        st.session_state.losses += 1
        st.session_state.last_loss_time = datetime.now()  # Start cooldown
    
    st.session_state.trades.append({
        'sym': p['sym'],
        'dir': p['dir'],
        'setup': setup_type,
        'pnl': total_pnl,
        't': datetime.now().strftime('%H:%M:%S'),
        'd': datetime.now().strftime('%Y-%m-%d'),
        'entry': p['entry'],
        'exit': p['cur'],
    })
    
    tick('SELL', p['sym'], p['dir'])
    st.session_state.pos.pop(i)

def update():
    """Update positions with REAL PRICES from Tradier + professional profit management"""
    for i, p in enumerate(st.session_state.pos):
        p['ticks'] += 1
        
        # GET REAL PRICE from Tradier if this is a live trade
        if p.get('is_live') and p.get('option_symbol'):
            real_price = get_tradier_quote(p['option_symbol'])
            if real_price and real_price > 0:
                p['cur'] = real_price
            else:
                # Fallback: small random movement if can't get price
                change = random.gauss(0.001, 0.008)
                p['cur'] = round(p['cur'] * (1 + change), 2)
        else:
            # Simulated trade - use random movement
            change = random.gauss(0.001, 0.008)
            change = max(-0.015, min(0.018, change))
            p['cur'] = round(p['cur'] * (1 + change), 2)
        
        # Calculate P/L based on actual quantity
        qty = p.get('qty', 1)
        p['pnl'] = round((p['cur'] - p['entry']) * qty * 100, 2)  # *100 for contract multiplier
        
        # Track price history for chart
        if 'price_history' in p:
            p['price_history'].append(p['cur'])
            if len(p['price_history']) > 50:
                p['price_history'].pop(0)
        
        # Calculate current gain %
        gain_pct = (p['cur'] - p['entry']) / p['entry']
        
        # CHECK IF THIS TRADE IS IN MANUAL MODE
        is_manual = p.get('manual_mode', False)
        
        # Auto-management if autopilot ON or STARTER tier AND not in manual mode for this trade
        if (st.session_state.auto or st.session_state.tier == 1) and not is_manual:
            
            # STOP LOSS CHECK (always first)
            effective_stop = p['entry'] if p.get('stop_at_breakeven') else p['sl']
            if p['cur'] <= effective_stop:
                sell(i)
                return
            
            # TAKE PROFIT CHECK (final target)
            if p['cur'] >= p['tp']:
                sell(i)
                return
            
            # PARTIAL PROFIT 1: Take 50% at +15%
            if gain_pct >= PARTIAL_PROFIT_1 and not p.get('partial_1_taken') and p.get('qty', 100) >= 50:
                sell(i, partial_pct=50)
                p['partial_1_taken'] = True
                p['qty'] = 50
                # Move stop to breakeven
                if TRAIL_AFTER_PARTIAL:
                    p['stop_at_breakeven'] = True
                    p['sl'] = p['entry']  # Breakeven
                return
            
            # PARTIAL PROFIT 2: Take 25% at +25%
            if gain_pct >= PARTIAL_PROFIT_2 and not p.get('partial_2_taken') and p.get('qty', 100) >= 25:
                sell(i, partial_pct=25)
                p['partial_2_taken'] = True
                p['qty'] = 25
                return
            
            # MOVE STOP TO BREAKEVEN at +10% (if not already)
            if gain_pct >= MOVE_STOP_TO_BE and not p.get('stop_at_breakeven'):
                p['stop_at_breakeven'] = True
                p['sl'] = p['entry']
        
        # MANUAL MODE: Still protect with stop loss, but no auto take profits
        elif is_manual:
            effective_stop = p['entry'] if p.get('stop_at_breakeven') else p['sl']
            if p['cur'] <= effective_stop:
                sell(i)
                return

def auto_trade(stks):
    """Automatically enter trades when CONFIRMED signals hit"""
    # Skip if autopilot OFF (unless STARTER)
    if not st.session_state.auto and st.session_state.tier != 1:
        return
    
    tier = TIERS[st.session_state.tier]
    _, _, _, market_open, in_window = mkt()
    
    # Safety checks
    if not market_open or not in_window:
        return
    if hit_limit():
        return
    if len(st.session_state.pos) >= tier['trades']:
        return
    
    # Check cooldown
    in_cooldown, _ = is_in_cooldown()
    if in_cooldown:
        return
    
    # Scan for opportunities - ONLY CONFIRMED SIGNALS
    for stk in stks[:tier['stocks']]:
        if len(st.session_state.pos) >= tier['trades']:
            break
        
        # Must be confirmed BUY or SELL signal
        if stk['signal'] == 'BUY':
            success, _ = buy(stk, 'CALL')
            if success:
                st.balloons()
                break
        elif stk['signal'] == 'SELL':
            success, _ = buy(stk, 'PUT')
            if success:
                st.balloons()
                break

# =============================================================================
# PAGES
# =============================================================================
def home():
    st.markdown('<div class="logo"><span>🌱</span><span>PROJECT HOPE</span></div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;color:#00FFA3;font-size:0.95em;font-style:italic;margin:-10px 0 15px;">✝️ "Trust in the LORD with all your heart" - Proverbs 3:5</p>', unsafe_allow_html=True)
    
    # LEGAL DISCLAIMER BANNER
    st.markdown('''<div style="background:rgba(255,165,0,0.1);border:1px solid rgba(255,165,0,0.3);border-radius:10px;padding:12px;margin:10px 0;">
        <p style="color:#FFA500;font-size:0.75em;margin:0;text-align:center;">
        ⚠️ <strong>IMPORTANT:</strong> Project Hope is EDUCATIONAL SOFTWARE, not investment advice. 
        We are NOT a registered investment adviser. Trading involves substantial risk of loss. 
        Past performance does not guarantee future results. You are solely responsible for your trading decisions.
        </p>
    </div>''', unsafe_allow_html=True)
    
    st.markdown('<div class="hero"><h1>OPTIONS TRADING</h1><p class="sub">Professional Entry Logic</p><p class="tag">4 A+ Setups | Confirmation Required | No Impulse Trades</p></div>', unsafe_allow_html=True)
    
    # HEYGEN WELCOME VIDEO - Small thumbnail link
    st.markdown('''<div style="text-align:center;margin:15px 0;">
        <a href="https://app.heygen.com/videos/10302438045d408cb992b38828e15d72" target="_blank" style="text-decoration:none;">
            <div style="display:inline-block;background:rgba(0,255,163,0.1);border:1px solid rgba(0,255,163,0.3);border-radius:10px;padding:12px 20px;">
                <span style="color:#00FFA3;font-size:1.2em;">▶️</span>
                <span style="color:white;font-weight:600;margin-left:8px;">Watch: Meet Stephen</span>
            </div>
        </a>
    </div>''', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.button("Home", disabled=True, use_container_width=True)
    with c2:
        if st.button("Trade", use_container_width=True, key="h1"):
            if st.session_state.tier > 0:
                st.session_state.page = 'trade'
                st.rerun()
            else:
                st.warning("Enter code first!")
    with c3:
        if st.button("History", use_container_width=True, key="h2"):
            st.session_state.page = 'history'
            st.rerun()
    with c4:
        if st.button("Learn", use_container_width=True, key="h3"):
            st.session_state.page = 'learn'
            st.rerun()
    
    # TRADIER CONNECTION STATUS (main display)
    if st.session_state.tradier_connected:
        st.markdown(f'''<div style="background:rgba(0,255,163,0.1);border:1px solid rgba(0,255,163,0.3);border-radius:10px;padding:10px;margin:10px 0;text-align:center;">
            <span style="color:#00FFA3;font-weight:700;">✅ TRADIER SANDBOX CONNECTED</span> | 
            <span style="color:#FFD700;font-weight:700;">Paper Balance: ${st.session_state.bal:,.2f}</span>
        </div>''', unsafe_allow_html=True)
    else:
        st.markdown(f'''<div style="background:rgba(255,75,75,0.1);border:1px solid rgba(255,75,75,0.3);border-radius:10px;padding:10px;margin:10px 0;text-align:center;">
            <span style="color:#FF4B4B;font-weight:700;">⚠️ TRADIER NOT CONNECTED</span> | 
            <span style="color:#808495;">Using simulation mode</span>
        </div>''', unsafe_allow_html=True)
    
    status, ct, cd, _, in_window = mkt()
    window_text = "🟢 TRADING WINDOW" if in_window else "🔴 OUTSIDE WINDOW"
    st.markdown(f'<div class="clk {status}"><p style="color:#808495;margin:0;font-size:0.85em;">{ct}</p><p style="font-size:1.3em;font-weight:800;color:#00E5FF;margin:6px 0 0;font-family:monospace;">{cd}</p><p style="font-size:0.8em;margin:4px 0 0;">{window_text}</p></div>', unsafe_allow_html=True)
    
    # Premarket Movers Display
    if st.session_state.premarket_movers:
        st.markdown("### 🔥 Pre-Market Movers")
        movers_html = '<div style="display:flex;flex-wrap:wrap;gap:10px;margin:10px 0;">'
        for m in st.session_state.premarket_movers[:5]:
            color = "#00FFA3" if m['gap'] > 0 else "#FF4B4B"
            arrow = "↑" if m['gap'] > 0 else "↓"
            movers_html += f'<div style="background:rgba(255,255,255,0.05);padding:10px 15px;border-radius:10px;border:1px solid {color}40;"><span style="color:white;font-weight:700;">{m["s"]}</span> <span style="color:{color};font-weight:600;">{arrow}{abs(m["gap"])}%</span></div>'
        movers_html += '</div>'
        st.markdown(movers_html, unsafe_allow_html=True)
    
    st.markdown("### 🎯 Professional Trading Logic")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="card stat"><p class="v" style="color:#00FFA3;">4</p><p class="l">A+ Setups</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="card stat"><p class="v" style="color:#FFD700;">{len(STOCKS_CORE)}+</p><p class="l">Stocks</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="card stat"><p class="v" style="color:#00E5FF;">2</p><p class="l">Windows</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="card stat"><p class="v" style="color:#A855F7;">PM</p><p class="l">Scanner</p></div>', unsafe_allow_html=True)
    
    st.markdown("### 🛡️ 5-Layer Protection")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown('<div class="card stat"><p class="v" style="color:#00FFA3;">-25%</p><p class="l">Stop</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card stat"><p class="v" style="color:#FFD700;">+30%</p><p class="l">Profit</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="card stat"><p class="v" style="color:#FF4B4B;">-15%</p><p class="l">Daily</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="card stat"><p class="v" style="color:#00E5FF;">5%</p><p class="l">Max</p></div>', unsafe_allow_html=True)
    with c5:
        st.markdown('<div class="card stat"><p class="v" style="color:#A855F7;">📰</p><p class="l">News</p></div>', unsafe_allow_html=True)
    
    st.markdown("### 👨‍💻 Founder")
    c1, c2 = st.columns([1, 3])
    with c1:
        st.markdown(f'<img src="{PHOTO}" class="ph">', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div><h4 style="color:white;margin:0;">{NAME}</h4><p style="color:#00FFA3;margin:2px 0;font-size:0.9em;">Amazon Worker | Self-Taught Dev</p><p style="color:#808495;margin:0;font-size:0.85em;">{LOCATION}</p></div>', unsafe_allow_html=True)
    
    with st.expander("My Story"):
        st.write(BIO)
    
    st.markdown("### 💎 Choose Your Plan")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="tier"><h3 style="color:#00FFA3;">STARTER</h3><p class="pr">$49<span style="font-size:0.4em;color:#808495;">/mo</span></p><p class="f"><span class="yes">✓</span> 1 Stock</p><p class="f"><span class="yes">✓</span> 1 Trade</p><p class="f"><span class="yes">✓</span> Auto Always</p><p class="f"><span class="yes">✓</span> All Protections</p><p class="f"><span class="no">✗</span> Manual</p><p style="color:#FFA500;font-size:0.7em;margin-top:8px;">⚠️ Min Account: $1,000</p></div>', unsafe_allow_html=True)
        st.link_button("GET STARTER", SIGNUP_LINKS["STARTER"], use_container_width=True)
    with c2:
        st.markdown('<div class="tier"><h3 style="color:#00E5FF;">BUILDER</h3><p class="pr">$99<span style="font-size:0.4em;color:#808495;">/mo</span></p><p class="f"><span class="yes">✓</span> 3 Stocks</p><p class="f"><span class="yes">✓</span> 2 Trades</p><p class="f"><span class="yes">✓</span> Auto Toggle</p><p class="f"><span class="yes">✓</span> All Protections</p><p class="f"><span class="no">✗</span> Coaching</p><p style="color:#FFA500;font-size:0.7em;margin-top:8px;">⚠️ Min Account: $2,000</p></div>', unsafe_allow_html=True)
        st.link_button("GET BUILDER", SIGNUP_LINKS["BUILDER"], use_container_width=True)
    with c3:
        st.markdown('<div class="tier" style="box-shadow:0 0 30px rgba(255,215,0,0.15);border:1px solid rgba(255,215,0,0.2);"><span class="badge">POPULAR</span><h3 style="color:#FFD700;">MASTER</h3><p class="pr">$199<span style="font-size:0.4em;color:#808495;">/mo</span></p><p class="f"><span class="yes">✓</span> 6 Stocks</p><p class="f"><span class="yes">✓</span> 3 Trades</p><p class="f"><span class="yes">✓</span> Auto Toggle</p><p class="f"><span class="yes">✓</span> Priority</p><p style="color:#FFA500;font-size:0.7em;margin-top:8px;">⚠️ Min Account: $3,000</p></div>', unsafe_allow_html=True)
        st.link_button("GET MASTER", SIGNUP_LINKS["MASTER"], use_container_width=True)
    with c4:
        st.markdown('<div class="tier"><h3 style="color:#FF6B6B;">VIP</h3><p class="pr">$499<span style="font-size:0.4em;color:#808495;">/mo</span></p><p class="f"><span class="yes">✓</span> 15 Stocks</p><p class="f"><span class="yes">✓</span> 5 Trades</p><p class="f"><span class="yes">✓</span> 1-on-1 Coach</p><p class="f"><span class="yes">✓</span> Community</p><p style="color:#FFA500;font-size:0.7em;margin-top:8px;">⚠️ Min Account: $5,000</p></div>', unsafe_allow_html=True)
        st.link_button("GET VIP", SIGNUP_LINKS["VIP"], use_container_width=True)
    
    st.markdown("### 🔐 Already a Member? Login")
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        # Show button if already logged in
        if st.session_state.tier > 0:
            st.success(f"✓ {TIERS[st.session_state.tier]['name']} - Ready!")
            if st.button("🚀 Start Trading", type="primary", use_container_width=True):
                st.session_state.page = 'trade'
                st.rerun()
        else:
            # Email + Password login
            email = st.text_input("Email", placeholder="Enter your email...", key="login_email")
            password = st.text_input("Password", type="password", placeholder="Enter your password...", key="login_password")
            
            if st.button("🔓 Login", type="primary", use_container_width=True):
                if email and password:
                    # DEMO access for owner
                    if email.upper() == "DEMO" and password.upper() == "DEMO":
                        st.session_state.tier = 4  # VIP access
                        st.session_state.user_email = "demo@projecthope.com"
                        st.success("✅ DEMO MODE - VIP Access")
                        st.rerun()
                    
                    # Try to verify with Outseta API
                    try:
                        # Authenticate with Outseta
                        auth_resp = requests.post(
                            f"https://{OUTSETA_DOMAIN}/api/v1/auth/accesstoken",
                            json={"username": email, "password": password},
                            timeout=10
                        )
                        
                        if auth_resp.status_code == 200:
                            auth_data = auth_resp.json()
                            access_token = auth_data.get('access_token')
                            
                            # Get user's subscription info
                            headers = {"Authorization": f"Bearer {access_token}"}
                            user_resp = requests.get(
                                f"https://{OUTSETA_DOMAIN}/api/v1/profile",
                                headers=headers,
                                timeout=5
                            )
                            
                            if user_resp.status_code == 200:
                                user_data = user_resp.json()
                                account = user_data.get('Account', {})
                                subscription = account.get('CurrentSubscription', {})
                                plan_name = subscription.get('Plan', {}).get('Name', '').upper()
                                
                                # Map plan to tier
                                tier_map = {"STARTER": 1, "BUILDER": 2, "MASTER": 3, "VIP": 4}
                                if plan_name in tier_map:
                                    st.session_state.tier = tier_map[plan_name]
                                    st.session_state.user_email = email
                                    st.success(f"✅ Welcome! {plan_name} access granted.")
                                    st.rerun()
                                else:
                                    st.warning("No active subscription. Please choose a plan above!")
                            else:
                                st.error("Could not get subscription info.")
                        else:
                            st.error("Invalid email or password.")
                    except Exception as e:
                        st.error("Login failed. Please try again.")
                else:
                    st.warning("Please enter email and password.")
    
    # Footer
    st.markdown(f'<div class="ft"><p style="color:#808495;font-size:0.85em;margin:0;">{NAME} | {EMAIL}</p><p style="color:#666;font-size:0.75em;margin:8px 0 0;">Educational tool only. Not financial advice.</p></div>', unsafe_allow_html=True)
    
    # Legal Disclaimer
    with st.expander("📜 Full Legal Disclaimer"):
        st.markdown("""
**IMPORTANT LEGAL DISCLAIMER**

I am **NOT** a financial advisor. I am not a licensed broker, investment advisor, or financial planner.

**Project Hope is an EDUCATIONAL tool only.** Nothing in this app constitutes financial advice.

**RISK WARNING:** Options trading involves substantial risk of loss. Past performance is not indicative of future results.

**By using Project Hope, you acknowledge that:**
1. You are solely responsible for your own trading decisions
2. You understand the risks involved in options trading
3. You will not hold Stephen Martinez or Project Hope liable for any losses

**Trade responsibly. Protect your capital.**
        """)

def trade():
    # Auto-refresh every 5 seconds - THIS VERSION MADE $105 TODAY
    st_autorefresh(interval=5000, key="trade_refresh")
    
    if st.session_state.tier == 0:
        st.warning("Enter code first")
        if st.button("Go Home"):
            st.session_state.page = 'home'
            st.rerun()
        return
    
    # RISK DISCLAIMER ACKNOWLEDGMENT - MUST ACCEPT BEFORE TRADING
    if not st.session_state.disclaimer_accepted:
        st.markdown('<div class="logo"><span>🌱</span><span>PROJECT HOPE</span></div>', unsafe_allow_html=True)
        st.markdown("## ⚠️ Risk Acknowledgment Required")
        
        st.markdown('''<div style="background:rgba(255,75,75,0.1);border:1px solid rgba(255,75,75,0.3);border-radius:12px;padding:20px;margin:15px 0;">
            <h4 style="color:#FF4B4B;margin:0 0 15px 0;">📜 IMPORTANT LEGAL DISCLAIMER</h4>
            <p style="color:#ccc;font-size:0.9em;line-height:1.6;">
            <strong>Project Hope is EDUCATIONAL SOFTWARE and a TRADE ASSISTANT TOOL.</strong><br><br>
            • Stephen Martinez is NOT a registered investment adviser with the SEC or any state securities authority<br>
            • This software does NOT provide personalized investment advice<br>
            • Past performance does NOT guarantee future results<br>
            • Trading options involves SUBSTANTIAL RISK OF LOSS<br>
            • You could lose some or ALL of your invested capital<br>
            • Only trade with money you can afford to lose
            </p>
        </div>''', unsafe_allow_html=True)
        
        st.markdown('''<div style="background:rgba(0,255,163,0.1);border:1px solid rgba(0,255,163,0.3);border-radius:12px;padding:20px;margin:15px 0;">
            <h4 style="color:#00FFA3;margin:0 0 15px 0;">🔒 AUTO-PILOT AUTHORIZATION</h4>
            <p style="color:#ccc;font-size:0.9em;line-height:1.6;">
            By enabling Auto-Pilot features, you acknowledge:<br><br>
            • You are connecting YOUR OWN brokerage account<br>
            • YOU authorize trades to be executed based on signals shown<br>
            • Project Hope does NOT have discretionary control of your account<br>
            • YOU can disable Auto-Pilot at ANY time<br>
            • YOU accept FULL responsibility for all trades executed
            </p>
        </div>''', unsafe_allow_html=True)
        
        st.markdown("### ✅ I Acknowledge and Accept:")
        
        ack1 = st.checkbox("I understand this is EDUCATIONAL SOFTWARE, not investment advice", key="ack1")
        ack2 = st.checkbox("I understand trading involves SUBSTANTIAL RISK and I could LOSE MONEY", key="ack2")
        ack3 = st.checkbox("I am trading with money I can AFFORD TO LOSE", key="ack3")
        ack4 = st.checkbox("I take FULL RESPONSIBILITY for all my trading decisions", key="ack4")
        ack5 = st.checkbox("I authorize Auto-Pilot to execute trades in MY OWN brokerage account", key="ack5")
        
        if ack1 and ack2 and ack3 and ack4 and ack5:
            if st.button("✅ I AGREE - START TRADING", type="primary", use_container_width=True):
                st.session_state.disclaimer_accepted = True
                st.rerun()
        else:
            st.warning("Please check all boxes to continue")
        
        return
    
    tier = TIERS[st.session_state.tier]
    
    # Update positions
    update()
    
    # Scan stocks
    stks = scan()
    
    # Auto-trade
    auto_trade(stks)
    
    # Header
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(f'<div style="display:flex;align-items:center;gap:8px;"><span style="font-size:1.3em;">🌱</span><span style="font-size:1.2em;font-weight:800;background:linear-gradient(135deg,#00FFA3,#00E5FF);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">PROJECT HOPE</span><span style="color:{tier["color"]};font-weight:600;background:rgba(255,255,255,0.1);padding:3px 8px;border-radius:6px;font-size:0.8em;">{tier["name"]}</span></div>', unsafe_allow_html=True)
    with c2:
        status, _, cd, _, in_window = mkt()
        window_color = "#00FFA3" if in_window else "#FF4B4B"
        st.markdown(f'<div class="clk {status}" style="padding:6px;"><span style="font-size:0.8em;font-weight:600;">{cd}</span><br><span style="font-size:0.7em;color:{window_color};">{"🟢 WINDOW" if in_window else "🔴 NO TRADE"}</span></div>', unsafe_allow_html=True)
    
    # Nav - BUTTONS WORK INSTANTLY (no autorefresh blocking)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Home", use_container_width=True, key="t1"):
            st.session_state.page = 'home'
            st.rerun()
    with c2:
        st.button("Trade", disabled=True, use_container_width=True)
    with c3:
        if st.button("History", use_container_width=True, key="t3"):
            st.session_state.page = 'history'
            st.rerun()
    with c4:
        if st.button("Learn", use_container_width=True, key="t4"):
            st.session_state.page = 'learn'
            st.rerun()
    
    # Stats
    eq = st.session_state.bal + sum(p.get('pnl', 0) for p in st.session_state.pos)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Equity", f"${eq:,.2f}")
    with c2:
        st.metric("Cash", f"${st.session_state.bal:,.2f}")
    with c3:
        st.metric("Today", f"${st.session_state.daily:+,.2f}")
    with c4:
        tot = st.session_state.wins + st.session_state.losses
        wr = (st.session_state.wins / tot * 100) if tot > 0 else 0
        st.metric("Win%", f"{wr:.0f}%")
    
    # Regime display
    regime = st.session_state.market_regime
    regime_class = "regime-trend" if regime == "TREND" else "regime-chop"
    st.markdown(f'<div style="text-align:center;margin:10px 0;"><span class="{regime_class}">Market: <strong>{regime}</strong> | VWAP Crosses: {st.session_state.vwap_crosses}</span></div>', unsafe_allow_html=True)
    
    # Status displays
    in_cooldown, cooldown_remaining = is_in_cooldown()
    
    if hit_limit():
        st.markdown('<div class="lck"><span style="color:#FF4B4B;font-weight:700;">🔒 DAILY LIMIT - Trading locked</span></div>', unsafe_allow_html=True)
    elif in_cooldown:
        st.markdown(f'<div class="cooldown"><span style="color:#FFA500;font-weight:700;">⏳ COOLDOWN: {cooldown_remaining}s remaining</span></div>', unsafe_allow_html=True)
    elif tier['auto'] == 'always':
        st.markdown('<div class="aon"><span style="color:#00FFA3;font-weight:700;">🤖 AUTOPILOT ALWAYS ON</span></div>', unsafe_allow_html=True)
    else:
        c1, c2 = st.columns([4, 1])
        with c1:
            status_class = "aon" if st.session_state.auto else "aoff"
            status_color = "#00FFA3" if st.session_state.auto else "#808495"
            st.markdown(f'<div class="{status_class}"><span style="color:{status_color};font-weight:700;">🤖 AUTO: {"ON" if st.session_state.auto else "OFF"}</span></div>', unsafe_allow_html=True)
        with c2:
            if st.button("Toggle", use_container_width=True):
                st.session_state.auto = not st.session_state.auto
                st.rerun()
    
    # Protection shield
    st.markdown(f'<div class="shld"><p style="font-weight:800;color:#00FFA3;margin:0;font-size:1em;">🛡️ PROFESSIONAL PROTECTION</p><p style="color:#808495;margin:4px 0 0;font-size:0.8em;">Partials @ +15%/+25% | Trail Stop | BE @ +10% | Max {tier["trades"]} | Cooldown 10m</p></div>', unsafe_allow_html=True)
    
    # POSITIONS DISPLAY FUNCTION - reusable for mobile top + desktop sidebar
    def show_positions():
        st.markdown(f"### 📈 Positions ({len(st.session_state.pos)}/{tier['trades']})")
        
        if st.session_state.pos:
            for i, p in enumerate(st.session_state.pos):
                pc = "#00FFA3" if p['pnl'] >= 0 else "#FF4B4B"
                
                # Position status indicators
                qty = p.get('qty', 100)
                p1 = "✅" if p.get('partial_1_taken') else "⬜"
                p2 = "✅" if p.get('partial_2_taken') else "⬜"
                be_status = "🔒BE" if p.get('stop_at_breakeven') else ""
                
                # Per-trade manual mode
                is_manual = p.get('manual_mode', False)
                mode_icon = "🖐️" if is_manual else "🤖"
                mode_text = "MANUAL" if is_manual else "AUTO"
                mode_color = "#FFA500" if is_manual else "#00FFA3"
                
                st.markdown(f'''<div class="pcard" style="border-left:3px solid {pc};">
                    <div style="display:flex;justify-content:space-between;">
                        <div>
                            <h4 style="color:white;margin:0;font-size:0.95em;">{p["sym"]} <span style="color:#808495;font-size:0.7em;">{qty}%</span></h4>
                            <p style="color:#808495;font-size:0.75em;">{p["dir"]} | {p.get("setup", "N/A")}</p>
                        </div>
                        <h4 style="color:{pc};margin:0;">${p["pnl"]:+.2f}</h4>
                    </div>
                    <div style="display:flex;justify-content:space-between;margin-top:5px;">
                        <span style="color:#808495;font-size:0.65em;">SL: ${p["sl"]:.2f} {be_status}</span>
                        <span style="color:#808495;font-size:0.65em;">{p1}T1 {p2}T2</span>
                    </div>
                    <div style="margin-top:5px;text-align:center;">
                        <span style="color:{mode_color};font-size:0.7em;font-weight:600;">{mode_icon} {mode_text}</span>
                    </div>
                </div>''', unsafe_allow_html=True)
                
                # Toggle and Close buttons
                col_a, col_b = st.columns(2)
                with col_a:
                    toggle_label = "🤖 Auto" if is_manual else "🖐️ Manual"
                    if st.button(toggle_label, key=f"toggle_{p['id']}_{i}", use_container_width=True):
                        st.session_state.pos[i]['manual_mode'] = not is_manual
                        st.rerun()
                with col_b:
                    if is_manual:
                        if st.button(f"🔴 Close", key=f"close_{p['id']}_{i}", use_container_width=True):
                            sell(i)
                            st.rerun()
                    else:
                        st.button("🔒 Protected", key=f"prot_{p['id']}_{i}", disabled=True, use_container_width=True)
        else:
            st.info("No positions")
    
    # MOBILE: Show positions FIRST (above scanner) when there are active positions
    # Uses CSS media query detection via markdown
    if st.session_state.pos:
        st.markdown('''<style>
            @media (min-width: 768px) { .mobile-positions { display: none !important; } }
            @media (max-width: 767px) { .desktop-positions { display: none !important; } }
        </style>''', unsafe_allow_html=True)
        
        # Mobile positions (shows only on small screens)
        st.markdown('<div class="mobile-positions">', unsafe_allow_html=True)
        show_positions()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main content - Scanner (left) and Positions (right on desktop)
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"### 📊 Scanner ({tier['stocks']} stocks)")
        st.markdown('<p style="color:#808495;font-size:0.8em;">Only CONFIRMED setups trigger trades</p>', unsafe_allow_html=True)
        
        for stk in stks[:tier['stocks']]:
            # Card style based on signal
            if stk['blk']:
                cc = 'blk'
            elif stk['signal'] == 'BUY':
                cc = 'buy'
            elif stk['signal'] == 'SELL':
                cc = 'sell'
            elif stk['signal'] == 'PENDING':
                cc = 'pending'
            else:
                cc = 'wait'
            
            chc = "#00FFA3" if stk['chg'] >= 0 else "#FF4B4B"
            
            # Signal color
            if stk['signal'] == 'BUY':
                sgc = "#00FFA3"
            elif stk['signal'] == 'SELL':
                sgc = "#FF4B4B"
            elif stk['signal'] == 'PENDING':
                sgc = "#FFD700"
            elif stk['signal'] == 'BLOCKED':
                sgc = "#FF0000"
            else:
                sgc = "#808495"
            
            # Setup type display
            setup_text = ""
            if stk['best_setup']:
                setup_text = f'<span class="setup-tag">{stk["best_setup"]["type"]}</span>'
            
            st.markdown(f'''<div class="stk {cc}">
                <div style="display:flex;justify-content:space-between;">
                    <div>
                        <h4 style="color:white;margin:0;font-size:1em;">{stk["sym"]} {setup_text}</h4>
                        <p style="color:#808495;margin:2px 0 0;font-size:0.8em;">{stk["name"]}</p>
                    </div>
                    <div style="text-align:right;">
                        <h4 style="color:#00E5FF;margin:0;font-size:1em;">${stk["pr"]:.2f}</h4>
                        <p style="color:{chc};margin:2px 0 0;font-weight:600;font-size:0.85em;">{stk["chg"]:+.2f}</p>
                    </div>
                </div>
                <div style="display:flex;justify-content:space-between;margin-top:8px;">
                    <span style="color:{sgc};font-weight:700;font-size:0.9em;">{stk["signal"]}</span>
                    <span style="color:#808495;font-size:0.8em;">HOT: {stk["hot_score"]} | RVOL: {stk["rvol"]}x</span>
                </div>
            </div>''', unsafe_allow_html=True)
            
            # Setup status
            if stk['setup_status']:
                st.markdown(f'<p style="color:#FFD700;font-size:0.8em;margin:-5px 0 5px 10px;">⏳ {stk["setup_status"]}</p>', unsafe_allow_html=True)
            
            # Indicators
            ih = "".join([f'<span class="ind {v[1]}">{k}</span>' for k, v in stk['sigs'].items()])
            st.markdown(f'<div style="margin:-3px 0 5px;">{ih}</div>', unsafe_allow_html=True)
            
            # News alerts
            if stk['news']['sent'] == 'DANGER':
                st.markdown(f'<div class="nb"><span style="color:#FF4B4B;">⚠️ {", ".join(stk["news"]["red"][:2])}</span></div>', unsafe_allow_html=True)
            elif stk['news']['sent'] == 'CAUTION':
                st.markdown(f'<div class="nw"><span style="color:#FFA500;">⚡ {", ".join(stk["news"]["red"][:1])}</span></div>', unsafe_allow_html=True)
            elif stk['news']['sent'] == 'BULLISH':
                st.markdown(f'<div class="ng"><span style="color:#00FFA3;">📈 {", ".join(stk["news"]["green"][:2])}</span></div>', unsafe_allow_html=True)
    
    # Desktop positions (right column - hidden on mobile via CSS)
    with col2:
        st.markdown('<div class="desktop-positions">', unsafe_allow_html=True)
        show_positions()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("### 📜 Ticker")
        for t in reversed(st.session_state.ticker[-5:]):
            tc = "b" if t['a'] == 'BUY' else "s"
            tcol = "#00FFA3" if t['a'] == 'BUY' else "#FF4B4B"
            st.markdown(f'<div class="tck {tc}"><span style="color:#808495;">{t["t"]}</span> <span style="color:{tcol};font-weight:600;">{t["a"]}</span> <span style="color:white;">{t["s"]}</span></div>', unsafe_allow_html=True)

def history():
    st.markdown('<div class="logo"><span>🌱</span><span>PROJECT HOPE</span></div>', unsafe_allow_html=True)
    
    # Random Bible verses for winning trades
    VICTORY_VERSES = [
        '"Trust in the LORD with all your heart" - Proverbs 3:5 ✝️',
        '"I can do all things through Christ who strengthens me" - Philippians 4:13 ✝️',
        '"The LORD is my shepherd, I shall not want" - Psalm 23:1 ✝️',
        '"For I know the plans I have for you" - Jeremiah 29:11 ✝️',
        '"Be strong and courageous" - Joshua 1:9 ✝️',
        '"God is our refuge and strength" - Psalm 46:1 ✝️',
        '"The blessing of the LORD makes rich" - Proverbs 10:22 ✝️',
        '"Commit your work to the LORD" - Proverbs 16:3 ✝️',
        '"With God all things are possible" - Matthew 19:26 ✝️',
        '"The LORD will fight for you" - Exodus 14:14 ✝️',
        '"Delight yourself in the LORD" - Psalm 37:4 ✝️',
        '"He gives strength to the weary" - Isaiah 40:29 ✝️',
    ]
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Home", use_container_width=True, key="hh1"):
            st.session_state.page = 'home'
            st.rerun()
    with c2:
        if st.button("Trade", use_container_width=True, key="hh2"):
            st.session_state.page = 'trade'
            st.rerun()
    with c3:
        st.button("History", disabled=True, use_container_width=True)
    with c4:
        if st.button("Learn", use_container_width=True, key="hh4"):
            st.session_state.page = 'learn'
            st.rerun()
    
    tot = st.session_state.wins + st.session_state.losses
    wr = (st.session_state.wins / tot * 100) if tot > 0 else 0
    pc = "#00FFA3" if st.session_state.total >= 0 else "#FF4B4B"
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="card stat"><p class="v" style="color:{pc};">${st.session_state.total:,.2f}</p><p class="l">Total P/L</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="card stat"><p class="v" style="color:#FFD700;">{wr:.0f}%</p><p class="l">Win Rate</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="card stat"><p class="v" style="color:#00FFA3;">{st.session_state.wins}</p><p class="l">Wins</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="card stat"><p class="v" style="color:#FF4B4B;">{st.session_state.losses}</p><p class="l">Losses</p></div>', unsafe_allow_html=True)
    
    # Setup Performance Stats
    st.markdown(get_setup_stats_display(), unsafe_allow_html=True)
    
    st.markdown("### 📜 Recent Trades")
    if st.session_state.trades:
        for i, t in enumerate(reversed(st.session_state.trades[-10:])):
            c = "#00FFA3" if t['pnl'] >= 0 else "#FF4B4B"
            entry_exit = f"${t.get('entry', 0):.2f} → ${t.get('exit', 0):.2f}" if 'entry' in t else ""
            
            # Random verse for this trade (seeded by trade time for consistency)
            verse_idx = hash(t.get("t", str(i))) % len(VICTORY_VERSES)
            verse = VICTORY_VERSES[verse_idx]
            
            st.markdown(f'''<div class="card" style="border-left:3px solid {c};padding:12px;">
                <div style="display:flex;justify-content:space-between;">
                    <div>
                        <p style="color:#808495;font-size:0.8em;margin:0;">{t.get("d", "")} {t["t"]}</p>
                        <h4 style="color:white;margin:6px 0 0;">{t["sym"]} {t.get("dir", "")} | {t.get("setup", "N/A")}</h4>
                        <p style="color:#808495;font-size:0.75em;margin:4px 0 0;">{entry_exit}</p>
                    </div>
                    <h3 style="color:{c};margin:0;">${t["pnl"]:+.2f}</h3>
                </div>
            </div>''', unsafe_allow_html=True)
            
            # Share button for winning trades
            if t['pnl'] > 0:
                share_text = f"🌱 PROJECT HOPE WIN 🌱\n\n{t['sym']} {t.get('dir', '')} +${t['pnl']:.2f}\n\n{verse}\n\n#ProjectHope #Trading #Blessed"
                with st.expander("📤 Share This Win"):
                    st.code(share_text, language=None)
                    st.markdown("👆 **Click the copy icon** in the top-right corner of the box above!")
    else:
        st.info("No trades yet")
    
    if st.button("🔄 Reset Stats", use_container_width=True):
        st.session_state.bal = st.session_state.start
        st.session_state.pos = []
        st.session_state.trades = []
        st.session_state.ticker = []
        st.session_state.data = {}
        st.session_state.daily = 0.0
        st.session_state.total = 0.0
        st.session_state.wins = 0
        st.session_state.losses = 0
        st.session_state.locked = False
        st.session_state.last_loss_time = None
        st.session_state.setups_pending = {}
        st.session_state.last_win_trade = None
        st.session_state.setup_stats = {
            'ORB': {'wins': 0, 'losses': 0, 'total_pnl': 0},
            'VWAP_RECLAIM': {'wins': 0, 'losses': 0, 'total_pnl': 0},
            'VWAP_REJECT': {'wins': 0, 'losses': 0, 'total_pnl': 0},
            'PULLBACK': {'wins': 0, 'losses': 0, 'total_pnl': 0},
            'BREAK_RETEST': {'wins': 0, 'losses': 0, 'total_pnl': 0},
        }
        st.rerun()

def learn():
    st.markdown('<div class="logo"><span>🌱</span><span>PROJECT HOPE</span></div>', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Home", use_container_width=True, key="ll1"):
            st.session_state.page = 'home'
            st.rerun()
    with c2:
        if st.button("Trade", use_container_width=True, key="ll2"):
            st.session_state.page = 'trade'
            st.rerun()
    with c3:
        if st.button("History", use_container_width=True, key="ll3"):
            st.session_state.page = 'history'
            st.rerun()
    with c4:
        st.button("Learn", disabled=True, use_container_width=True)
    
    st.markdown("### 🎯 The 4 A+ Setups")
    
    setups_info = [
        ("ORB", "Opening Range Breakout", "Price breaks above/below the first 5-15 minute range with volume confirmation", "#00FFA3"),
        ("VWAP", "VWAP Reclaim/Rejection", "Price reclaims VWAP and holds (long) or rejects VWAP and fails (short)", "#00E5FF"),
        ("PULLBACK", "Trend Pullback", "Strong trend pulls back to 9/20 EMA, then continues", "#FFD700"),
        ("RETEST", "Break & Retest", "Key level breaks, retests, and holds - then entry", "#A855F7")
    ]
    
    for name, title, desc, color in setups_info:
        st.markdown(f'''<div class="card" style="border-left:4px solid {color};padding:14px;">
            <h4 style="color:{color};margin:0 0 8px;">{name} - {title}</h4>
            <p style="color:#c0c0c0;margin:0;font-size:0.9em;">{desc}</p>
        </div>''', unsafe_allow_html=True)
    
    st.markdown("### ⏰ Trading Windows")
    st.markdown('''<div class="card">
        <p style="color:#00FFA3;font-weight:600;margin:0;">🟢 9:30 - 10:30 AM ET (Opening)</p>
        <p style="color:#FF4B4B;margin:8px 0;">🔴 10:30 - 3:00 PM ET (Chop Zone - NO TRADES)</p>
        <p style="color:#00FFA3;font-weight:600;margin:0;">🟢 3:00 - 3:55 PM ET (Power Hour)</p>
    </div>''', unsafe_allow_html=True)
    
    st.markdown("### 📊 Confirmation Required")
    st.markdown('''<div class="card">
        <p style="color:white;margin:0;">Every trade must be <strong>confirmed</strong> before entry:</p>
        <p style="color:#808495;margin:8px 0 0;">1. Setup detected → Wait</p>
        <p style="color:#808495;margin:4px 0 0;">2. Price must hold level for 3 checks (15 seconds)</p>
        <p style="color:#808495;margin:4px 0 0;">3. Volume must confirm (RVOL ≥ 1.5x)</p>
        <p style="color:#00FFA3;margin:4px 0 0;font-weight:600;">4. THEN execute</p>
    </div>''', unsafe_allow_html=True)
    
    st.markdown("### 🛡️ Protection Rules")
    protections = [
        ("Stop Loss -25%", "Auto-exits if trade drops 25%"),
        ("Take Profit +30%", "Auto-exits if trade gains 30%"),
        ("Daily Max -15%", "Locks trading if down 15% for day"),
        ("10min Cooldown", "After every loss, 10 minute cooldown"),
        ("HOT Score 70+", "Only trades stocks with high quality score"),
        ("No CHOP", "Won't trade in choppy markets")
    ]
    
    for name, desc in protections:
        st.markdown(f'''<div class="card" style="padding:10px;">
            <strong style="color:#00FFA3;">{name}</strong>
            <span style="color:#808495;"> - {desc}</span>
        </div>''', unsafe_allow_html=True)
    
    # FULL LEGAL DISCLAIMER SECTION
    st.markdown("### ⚠️ Important Disclaimers")
    
    with st.expander("📜 Read Full Legal Disclaimer"):
        st.markdown('''
**EDUCATIONAL PURPOSE ONLY**

Project Hope is educational software designed to assist users in learning trading strategies. It is NOT investment advice and should not be construed as such.

**NOT AN INVESTMENT ADVISER**

Stephen Martinez and Project Hope are NOT registered investment advisers with the U.S. Securities and Exchange Commission (SEC) or any state securities authority. We do not provide personalized investment advice.

Project Hope relies upon the "publisher's exclusion" from the definition of "investment adviser" as provided under Section 202(a)(11)(D) of the Investment Advisers Act of 1940. The information provided is impersonal and not tailored to the investment needs of any specific person.

**USER RESPONSIBILITY**

YOU are solely responsible for all trading decisions made using this software. YOU authorize all trades executed through YOUR brokerage account. Project Hope does not have discretionary control over your account.

**RISK DISCLOSURE**

Trading options involves substantial risk of loss. You could lose some or all of your invested capital. Past performance does not guarantee future results.

The high degree of leverage available in options trading can work against you as well as for you. The use of leverage can lead to large losses as well as gains.

**NO GUARANTEES**

We make NO guarantees of profit. Hypothetical or simulated performance results have inherent limitations. Unlike an actual performance record, simulated results do not represent actual trading.

**CONSULT PROFESSIONALS**

We recommend that you consult with a qualified financial advisor, attorney, and/or tax professional before making any investment decisions.

**TERMS OF USE**

By using Project Hope, you acknowledge that you have read, understood, and agree to these terms. You accept full responsibility for your trading decisions and results.
        ''')
    
    st.markdown('''<div style="background:rgba(255,165,0,0.1);border:1px solid rgba(255,165,0,0.3);border-radius:10px;padding:12px;margin:15px 0;">
        <p style="color:#FFA500;font-size:0.75em;margin:0;text-align:center;">
        ⚠️ Trading involves substantial risk. Past performance does not guarantee future results. Only trade with money you can afford to lose.
        </p>
    </div>''', unsafe_allow_html=True)

# =============================================================================
# MAIN
# =============================================================================
def main():
    p = st.session_state.page
    if p == 'home':
        home()
    elif p == 'trade':
        trade()
    elif p == 'history':
        history()
    elif p == 'learn':
        learn()
    else:
        home()

if __name__ == "__main__":
    main()
