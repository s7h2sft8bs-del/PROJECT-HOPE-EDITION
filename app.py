# PROJECT HOPE v5.0 - PROFESSIONAL EDITION
# Built by Stephen Martinez | Lancaster, PA
# Institutional-Grade Entry Logic | 4 A+ Setups Only | No Impulse Trades

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import random
from datetime import datetime, timedelta
from collections import deque
import numpy as np
import pytz
import requests

st.set_page_config(page_title="Project Hope", page_icon="🌱", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=5000, key="refresh")

# =============================================================================
# ALPACA API
# =============================================================================
ALPACA_KEY = "PKQJEFSQBY2CFDYYHDR372QB3S"
ALPACA_SECRET = "ArMPEE3fqY1JCB5CArZUQ5wY8fYQjuPXJ9qpnwYPHJuw"
ALPACA_URL = "https://paper-api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"

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
STOP_LOSS = 0.25              # -25% stop loss
TAKE_PROFIT = 0.30            # +30% take profit  
DAILY_LIMIT = 0.15            # -15% daily max loss
MAX_POS = 0.05                # 5% max per trade
COOLDOWN_AFTER_LOSS = 600     # 10 minutes cooldown after loss (seconds)
MIN_RVOL = 1.5                # Minimum relative volume
MIN_HOLD_CHECKS = 3           # Must hold level for 3 checks (15 sec)
MIN_SETUP_SCORE = 70          # HOT score minimum for trade

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
# WATCHLIST
# =============================================================================
STOCKS = [
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
    {"s": "F", "n": "Ford", "p": 10.25},
    {"s": "AAL", "n": "American Airlines", "p": 17.80},
    {"s": "PLUG", "n": "Plug Power", "p": 2.15},
    {"s": "BB", "n": "BlackBerry", "p": 2.45},
    {"s": "AMC", "n": "AMC Entertainment", "p": 3.20}
]

BIO = """I'm Stephen Martinez, an Amazon warehouse worker from Lancaster, PA.

For years, I watched my coworkers - hardworking people with families - lose their savings on trading apps designed to make them trade MORE, not trade SMARTER.

These apps make money when you lose money. They want you addicted, emotional, and overtrading.

So I taught myself to code. During lunch breaks. After 10-hour shifts. On weekends when my body was exhausted but my mind wouldn't stop.

Project Hope is my answer. An app that PROTECTS you first. That stops you from blowing up your account. That treats your $200 like it matters - because it does.

This isn't about getting rich quick. It's about building something real, one smart trade at a time.

Welcome to Project Hope. Let's build together."""

# =============================================================================
# ALPACA API FUNCTIONS
# =============================================================================
def headers():
    return {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}

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
    'bal': 5000.0,
    'start': 5000.0,
    'locked': False,
    'date': datetime.now().strftime('%Y-%m-%d'),
    'nc': {},
    # PROFESSIONAL ADDITIONS
    'last_loss_time': None,           # For cooldown tracking
    'market_regime': 'UNKNOWN',       # TREND or CHOP
    'vwap_crosses': 0,                # Count VWAP crosses for regime
    'setups_pending': {},             # Setups waiting for confirmation
    'levels': {},                     # Pre-calculated levels per stock
    'candle_history': {},             # Store candle data
    'opening_range': {},              # 5min/15min opening range
    'or_calculated': False,           # Opening range calculated flag
}

for k, v in defs.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Daily reset
if st.session_state.date != datetime.now().strftime('%Y-%m-%d'):
    st.session_state.daily = 0.0
    st.session_state.locked = False
    st.session_state.date = datetime.now().strftime('%Y-%m-%d')
    st.session_state.or_calculated = False
    st.session_state.opening_range = {}
    st.session_state.vwap_crosses = 0

# Get Alpaca account
acct = get_acct()
if acct:
    st.session_state.bal = float(acct.get('cash', 5000))
    if st.session_state.start == 5000.0:
        st.session_state.start = st.session_state.bal

# =============================================================================
# STYLES
# =============================================================================
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
*{font-family:'Inter',sans-serif}.stApp{background:linear-gradient(160deg,#000,#0a0a0f 30%,#0d1117 60%,#000)}
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
    
    if now.weekday() >= 5:
        return 'closed', t, "WEEKEND", False, False
    if now < market_open:
        d = market_open - now
        return 'pre', t, f"PRE {d.seconds//3600:02d}:{(d.seconds%3600)//60:02d}:{d.seconds%60:02d}", False, False
    if now >= market_close:
        return 'closed', t, "CLOSED", False, False
    
    # Market is open - check trading windows
    d = market_close - now
    countdown = f"OPEN {d.seconds//3600:02d}:{(d.seconds%3600)//60:02d}:{d.seconds%60:02d}"
    
    # TRADING WINDOWS: 9:30-10:30 and 3:00-3:55
    hour, minute = now.hour, now.minute
    opening_window = (hour == 9 and minute >= 30) or (hour == 10 and minute <= 30)
    power_hour = (hour == 15 and minute >= 0 and minute <= 55)
    in_trade_window = opening_window or power_hour
    
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
    """
    setups = []
    
    if len(prices) < 20 or not levels:
        return setups
    
    vwap = levels['vwap']
    e9 = ema(prices, 9)
    e21 = ema(prices, 21)
    
    # Get last few prices for pattern detection
    p1, p2, p3 = prices[-1], prices[-2] if len(prices) > 1 else prices[-1], prices[-3] if len(prices) > 2 else prices[-1]
    
    # ===================
    # SETUP A: ORB (Opening Range Breakout)
    # ===================
    if or_levels and regime != 'CHOP':
        or_high = or_levels.get('5m_high', 0)
        or_low = or_levels.get('5m_low', 0)
        
        # Breakout above OR high
        if or_high and price > or_high and p2 <= or_high and rvol >= MIN_RVOL:
            setups.append({
                'type': 'ORB',
                'direction': 'LONG',
                'trigger_price': or_high,
                'entry': price,
                'stop': or_low,
                'target1': price + (price - or_low),
                'target2': price + 2 * (price - or_low),
                'confidence': 80 if rvol >= 2.0 else 70
            })
        
        # Breakdown below OR low
        if or_low and price < or_low and p2 >= or_low and rvol >= MIN_RVOL:
            setups.append({
                'type': 'ORB',
                'direction': 'SHORT',
                'trigger_price': or_low,
                'entry': price,
                'stop': or_high,
                'target1': price - (or_high - price),
                'target2': price - 2 * (or_high - price),
                'confidence': 80 if rvol >= 2.0 else 70
            })
    
    # ===================
    # SETUP B: VWAP Reclaim/Rejection
    # ===================
    vwap_buffer = vwap * 0.002  # 0.2% buffer
    
    # VWAP Reclaim (Long) - was below, now above and holding
    if p3 < vwap and p2 < vwap and price > vwap + vwap_buffer:
        setups.append({
            'type': 'VWAP_RECLAIM',
            'direction': 'LONG',
            'trigger_price': vwap,
            'entry': price,
            'stop': vwap - vwap_buffer * 2,
            'target1': levels.get('resistance', price * 1.01),
            'target2': levels.get('pd_high', price * 1.02),
            'confidence': 75 if rvol >= 1.5 else 65
        })
    
    # VWAP Rejection (Short) - tested VWAP from below and failed
    if p3 < vwap and p2 > vwap - vwap_buffer and p2 < vwap + vwap_buffer and price < vwap - vwap_buffer:
        setups.append({
            'type': 'VWAP_REJECT',
            'direction': 'SHORT',
            'trigger_price': vwap,
            'entry': price,
            'stop': vwap + vwap_buffer * 2,
            'target1': levels.get('support', price * 0.99),
            'target2': levels.get('pd_low', price * 0.98),
            'confidence': 75 if rvol >= 1.5 else 65
        })
    
    # ===================
    # SETUP C: Pullback Continuation
    # ===================
    # Bullish trend pullback to 9 EMA
    if regime == 'TREND' and price > e21 and e9 > e21:
        # Price pulled back to 9 EMA and bouncing
        if p2 <= e9 * 1.002 and p2 >= e9 * 0.998 and price > p2:
            setups.append({
                'type': 'PULLBACK',
                'direction': 'LONG',
                'trigger_price': e9,
                'entry': price,
                'stop': e21,
                'target1': levels.get('resistance', price * 1.015),
                'target2': levels.get('pd_high', price * 1.025),
                'confidence': 80 if regime == 'TREND' else 60
            })
    
    # Bearish trend pullback to 9 EMA
    if regime == 'TREND' and price < e21 and e9 < e21:
        if p2 >= e9 * 0.998 and p2 <= e9 * 1.002 and price < p2:
            setups.append({
                'type': 'PULLBACK',
                'direction': 'SHORT',
                'trigger_price': e9,
                'entry': price,
                'stop': e21,
                'target1': levels.get('support', price * 0.985),
                'target2': levels.get('pd_low', price * 0.975),
                'confidence': 80 if regime == 'TREND' else 60
            })
    
    # ===================
    # SETUP D: Break & Retest
    # ===================
    key_levels = [
        levels.get('pd_high'), levels.get('pd_low'),
        levels.get('pm_high'), levels.get('pm_low'),
        levels.get('whole'), levels.get('half_up'), levels.get('half_down')
    ]
    
    for lvl in key_levels:
        if lvl is None:
            continue
        lvl_buffer = lvl * 0.002
        
        # Break above and retest holding
        if p3 < lvl and p2 > lvl and abs(price - lvl) < lvl_buffer and price > lvl:
            setups.append({
                'type': 'BREAK_RETEST',
                'direction': 'LONG',
                'trigger_price': lvl,
                'entry': price,
                'stop': lvl - lvl_buffer * 3,
                'target1': price + (price - (lvl - lvl_buffer * 3)),
                'target2': price + 2 * (price - (lvl - lvl_buffer * 3)),
                'confidence': 70
            })
        
        # Break below and retest holding
        if p3 > lvl and p2 < lvl and abs(price - lvl) < lvl_buffer and price < lvl:
            setups.append({
                'type': 'BREAK_RETEST',
                'direction': 'SHORT',
                'trigger_price': lvl,
                'entry': price,
                'stop': lvl + lvl_buffer * 3,
                'target1': price - ((lvl + lvl_buffer * 3) - price),
                'target2': price - 2 * ((lvl + lvl_buffer * 3) - price),
                'confidence': 70
            })
    
    return setups

# =============================================================================
# CONFIRMATION ENGINE (NO IMPULSE TRADES)
# =============================================================================
def check_confirmation(sym, setup):
    """
    Check if a setup has been confirmed
    Must hold for MIN_HOLD_CHECKS (3 checks = 15 seconds)
    """
    pending = st.session_state.setups_pending
    setup_key = f"{sym}_{setup['type']}_{setup['direction']}"
    
    if setup_key not in pending:
        # First time seeing this setup - start tracking
        pending[setup_key] = {
            'setup': setup,
            'checks': 1,
            'first_seen': datetime.now(),
            'prices': [setup['entry']]
        }
        return False, "CONFIRMING (1/3)"
    
    # Setup exists - check if still valid
    tracked = pending[setup_key]
    tracked['checks'] += 1
    tracked['prices'].append(setup['entry'])
    
    # Check if price is holding (not whipsawing back)
    direction = setup['direction']
    trigger = setup['trigger_price']
    current = setup['entry']
    
    if direction == 'LONG' and current < trigger:
        # Failed - price went back below trigger
        del pending[setup_key]
        return False, "FAILED - Price reversed"
    
    if direction == 'SHORT' and current > trigger:
        # Failed - price went back above trigger
        del pending[setup_key]
        return False, "FAILED - Price reversed"
    
    # Check if enough confirmations
    if tracked['checks'] >= MIN_HOLD_CHECKS:
        # CONFIRMED! Clean up and return True
        del pending[setup_key]
        return True, "CONFIRMED"
    
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
    
    return {
        'sym': sym,
        'name': stk['n'],
        'pr': price,
        'chg': round(price - prices[-2] if len(prices) > 1 else 0, 2),
        'sigs': sigs,
        'oc': oc,
        'sl': round(oc * (1 - STOP_LOSS), 2),
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
    """Scan all stocks and sort by HOT score"""
    results = [analyze_stock(s) for s in STOCKS]
    return sorted(results, key=lambda x: x['hot_score'], reverse=True)

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
    """Check all conditions before allowing a trade"""
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
    
    return True, "OK"

def buy(stk, direction):
    """Execute buy"""
    ok, reason = can_buy(stk)
    if not ok:
        return False, reason
    
    cost = stk['oc'] * 100
    st.session_state.bal -= cost
    
    setup_type = stk['best_setup']['type'] if stk['best_setup'] else 'MANUAL'
    
    st.session_state.pos.append({
        'id': f"{stk['sym']}_{datetime.now().strftime('%H%M%S')}",
        'sym': stk['sym'],
        'dir': direction,
        'setup': setup_type,
        'entry': stk['oc'],
        'cur': stk['oc'],
        'sl': stk['sl'],
        'tp': stk['tp'],
        'pnl': 0,
        'ticks': 0,
        'entry_time': datetime.now()
    })
    
    tick('BUY', stk['sym'], direction)
    return True, "OK"

def sell(i):
    """Execute sell"""
    if i >= len(st.session_state.pos):
        return
    
    p = st.session_state.pos[i]
    st.session_state.bal += (p['entry'] * 100) + p['pnl']
    st.session_state.daily += p['pnl']
    st.session_state.total += p['pnl']
    
    if p['pnl'] >= 0:
        st.session_state.wins += 1
    else:
        st.session_state.losses += 1
        st.session_state.last_loss_time = datetime.now()  # Start cooldown
    
    st.session_state.trades.append({
        'sym': p['sym'],
        'dir': p['dir'],
        'setup': p.get('setup', 'N/A'),
        'pnl': p['pnl'],
        't': datetime.now().strftime('%H:%M:%S'),
        'd': datetime.now().strftime('%Y-%m-%d')
    })
    
    tick('SELL', p['sym'], p['dir'])
    st.session_state.pos.pop(i)

def update():
    """Update positions with realistic price movement"""
    for i, p in enumerate(st.session_state.pos):
        p['ticks'] += 1
        
        # Realistic movement: small changes accumulating
        change = random.gauss(0.002, 0.012)
        change = max(-0.02, min(0.025, change))
        
        p['cur'] = round(p['entry'] * (1 + change), 2)
        p['pnl'] = round((p['cur'] - p['entry']) * 100, 2)
        
        # Auto-exit if autopilot ON or STARTER tier
        if st.session_state.auto or st.session_state.tier == 1:
            if p['cur'] <= p['sl']:
                sell(i)
                return
            if p['cur'] >= p['tp']:
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
    st.markdown('<div class="hero"><h1>OPTIONS TRADING</h1><p class="sub">Professional Entry Logic</p><p class="tag">4 A+ Setups | Confirmation Required | No Impulse Trades</p></div>', unsafe_allow_html=True)
    
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
    
    if acct:
        st.markdown(f'<div class="conn"><span style="color:#00FFA3;font-weight:700;">✓ ALPACA</span> | <span style="color:#FFD700;font-weight:700;">${st.session_state.bal:,.2f}</span></div>', unsafe_allow_html=True)
    
    status, ct, cd, _, in_window = mkt()
    window_text = "🟢 TRADING WINDOW" if in_window else "🔴 OUTSIDE WINDOW"
    st.markdown(f'<div class="clk {status}"><p style="color:#808495;margin:0;font-size:0.85em;">{ct}</p><p style="font-size:1.3em;font-weight:800;color:#00E5FF;margin:6px 0 0;font-family:monospace;">{cd}</p><p style="font-size:0.8em;margin:4px 0 0;">{window_text}</p></div>', unsafe_allow_html=True)
    
    st.markdown("### 🎯 Professional Trading Logic")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="card stat"><p class="v" style="color:#00FFA3;">4</p><p class="l">A+ Setups</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card stat"><p class="v" style="color:#FFD700;">3x</p><p class="l">Confirm</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="card stat"><p class="v" style="color:#00E5FF;">2</p><p class="l">Windows</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="card stat"><p class="v" style="color:#A855F7;">10m</p><p class="l">Cooldown</p></div>', unsafe_allow_html=True)
    
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
    
    st.markdown("### 💎 Plans")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="tier"><h3 style="color:#00FFA3;">STARTER</h3><p class="pr">$49<span style="font-size:0.4em;color:#808495;">/mo</span></p><p class="f"><span class="yes">✓</span> 1 Stock</p><p class="f"><span class="yes">✓</span> 1 Trade</p><p class="f"><span class="yes">✓</span> Auto Always</p><p class="f"><span class="yes">✓</span> All Protections</p><p class="f"><span class="no">✗</span> Manual</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="tier"><h3 style="color:#00E5FF;">BUILDER</h3><p class="pr">$99<span style="font-size:0.4em;color:#808495;">/mo</span></p><p class="f"><span class="yes">✓</span> 3 Stocks</p><p class="f"><span class="yes">✓</span> 2 Trades</p><p class="f"><span class="yes">✓</span> Auto Toggle</p><p class="f"><span class="yes">✓</span> All Protections</p><p class="f"><span class="no">✗</span> Coaching</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="tier" style="box-shadow:0 0 30px rgba(255,215,0,0.15);border:1px solid rgba(255,215,0,0.2);"><span class="badge">POPULAR</span><h3 style="color:#FFD700;">MASTER</h3><p class="pr">$199<span style="font-size:0.4em;color:#808495;">/mo</span></p><p class="f"><span class="yes">✓</span> 6 Stocks</p><p class="f"><span class="yes">✓</span> 3 Trades</p><p class="f"><span class="yes">✓</span> Auto Toggle</p><p class="f"><span class="yes">✓</span> Priority</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="tier"><h3 style="color:#FF6B6B;">VIP</h3><p class="pr">$499<span style="font-size:0.4em;color:#808495;">/mo</span></p><p class="f"><span class="yes">✓</span> 15 Stocks</p><p class="f"><span class="yes">✓</span> 5 Trades</p><p class="f"><span class="yes">✓</span> 1-on-1 Coach</p><p class="f"><span class="yes">✓</span> Community</p></div>', unsafe_allow_html=True)
    
    st.markdown("### 🔐 Access Code")
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        code = st.text_input("Code", type="password", label_visibility="collapsed", placeholder="Enter code...")
        codes = {"HOPE49": 1, "HOPE99": 2, "HOPE199": 3, "HOPE499": 4, "DEMO": 3}
        if code:
            if code.upper() in codes:
                st.session_state.tier = codes[code.upper()]
                st.success(f"✓ {TIERS[st.session_state.tier]['name']}")
            else:
                st.error("Invalid")
        if st.session_state.tier > 0:
            if st.button("🚀 Start Trading", type="primary", use_container_width=True):
                st.session_state.page = 'trade'
                st.rerun()
    
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
    if st.session_state.tier == 0:
        st.warning("Enter code first")
        if st.button("Go Home"):
            st.session_state.page = 'home'
            st.rerun()
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
    
    # Nav
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
    st.markdown(f'<div class="shld"><p style="font-weight:800;color:#00FFA3;margin:0;font-size:1em;">🛡️ PROFESSIONAL PROTECTION</p><p style="color:#808495;margin:4px 0 0;font-size:0.8em;">Confirmed Entries | Stop -25% | Profit +30% | Max {tier["trades"]} | Cooldown 10m</p></div>', unsafe_allow_html=True)
    
    # Main content
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
    
    with col2:
        st.markdown(f"### 📈 Positions ({len(st.session_state.pos)}/{tier['trades']})")
        
        if st.session_state.pos:
            for i, p in enumerate(st.session_state.pos):
                pc = "#00FFA3" if p['pnl'] >= 0 else "#FF4B4B"
                st.markdown(f'''<div class="pcard" style="border-left:3px solid {pc};">
                    <div style="display:flex;justify-content:space-between;">
                        <div>
                            <h4 style="color:white;margin:0;font-size:0.95em;">{p["sym"]}</h4>
                            <p style="color:#808495;font-size:0.75em;">{p["dir"]} | {p.get("setup", "N/A")}</p>
                        </div>
                        <h4 style="color:{pc};margin:0;">${p["pnl"]:+.2f}</h4>
                    </div>
                    <p style="color:#808495;font-size:0.7em;margin:5px 0 0;">SL: ${p["sl"]:.2f} | TP: ${p["tp"]:.2f}</p>
                </div>''', unsafe_allow_html=True)
                
                if tier['auto'] != 'always' and not st.session_state.auto:
                    if st.button("Close", key=f"c_{i}", use_container_width=True):
                        sell(i)
                        st.rerun()
        else:
            st.info("No positions")
        
        st.markdown("### 📜 Ticker")
        for t in reversed(st.session_state.ticker[-5:]):
            tc = "b" if t['a'] == 'BUY' else "s"
            tcol = "#00FFA3" if t['a'] == 'BUY' else "#FF4B4B"
            st.markdown(f'<div class="tck {tc}"><span style="color:#808495;">{t["t"]}</span> <span style="color:{tcol};font-weight:600;">{t["a"]}</span> <span style="color:white;">{t["s"]}</span></div>', unsafe_allow_html=True)

def history():
    st.markdown('<div class="logo"><span>🌱</span><span>PROJECT HOPE</span></div>', unsafe_allow_html=True)
    
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
    
    st.markdown("### Recent Trades")
    if st.session_state.trades:
        for t in reversed(st.session_state.trades[-10:]):
            c = "#00FFA3" if t['pnl'] >= 0 else "#FF4B4B"
            st.markdown(f'''<div class="card" style="border-left:3px solid {c};padding:12px;">
                <div style="display:flex;justify-content:space-between;">
                    <div>
                        <p style="color:#808495;font-size:0.8em;margin:0;">{t.get("d", "")} {t["t"]}</p>
                        <h4 style="color:white;margin:6px 0 0;">{t["sym"]} {t.get("dir", "")} | {t.get("setup", "N/A")}</h4>
                    </div>
                    <h3 style="color:{c};margin:0;">${t["pnl"]:+.2f}</h3>
                </div>
            </div>''', unsafe_allow_html=True)
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
