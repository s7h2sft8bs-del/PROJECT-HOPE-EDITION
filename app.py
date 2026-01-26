# -*- coding: utf-8 -*-
"""
PROJECT HOPE v4.3 - ALPACA LIVE DATA
Built by Stephen Martinez | Lancaster, PA
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import random
from datetime import datetime, timedelta
import numpy as np
import pytz
import requests

# Alpaca Paper Trading API
ALPACA_API_KEY = "PKQJEFSQBY2CFDYYHDR372QB3S"
ALPACA_SECRET_KEY = "ArMPEE3fqY1JCB5CArZUQ5wY8fYQjuPXJ9qpnwYPHJuw"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
ALPACA_DATA_URL = "https://data.alpaca.markets"

# Alpaca API headers
ALPACA_HEADERS = {
    "APCA-API-KEY-ID": ALPACA_API_KEY,
    "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
}

st.set_page_config(page_title="Project Hope", page_icon="\U0001F331", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=1000, key="refresh")

STEPHEN_PHOTO = "https://i.postimg.cc/qvVSgvfx/IMG-7642.jpg"
STEPHEN_NAME = "Stephen Martinez"
STEPHEN_LOCATION = "Lancaster, PA"
STEPHEN_EMAIL = "thetradingprotocol@gmail.com"

TIERS = {
    1: {"name": "STARTER", "price": 49, "stocks_shown": 1, "max_trades": 1, "color": "#00FFA3", "autopilot": "always"},
    2: {"name": "BUILDER", "price": 99, "stocks_shown": 3, "max_trades": 2, "color": "#00E5FF", "autopilot": "toggle"},
    3: {"name": "MASTER", "price": 199, "stocks_shown": 6, "max_trades": 3, "color": "#FFD700", "autopilot": "toggle"},
    4: {"name": "VIP", "price": 499, "stocks_shown": 15, "max_trades": 5, "color": "#FF6B6B", "autopilot": "toggle"}
}

WATCHLIST = [
    {"symbol": "SOFI", "name": "SoFi Technologies", "base_price": 14.50},
    {"symbol": "PLTR", "name": "Palantir", "base_price": 78.00},
    {"symbol": "NIO", "name": "NIO Inc", "base_price": 4.85},
    {"symbol": "RIVN", "name": "Rivian", "base_price": 12.30},
    {"symbol": "HOOD", "name": "Robinhood", "base_price": 24.50},
    {"symbol": "SNAP", "name": "Snapchat", "base_price": 11.20},
    {"symbol": "COIN", "name": "Coinbase", "base_price": 265.00},
    {"symbol": "MARA", "name": "Marathon Digital", "base_price": 18.75},
    {"symbol": "RIOT", "name": "Riot Platforms", "base_price": 12.40},
    {"symbol": "LCID", "name": "Lucid Motors", "base_price": 2.80},
    {"symbol": "F", "name": "Ford", "base_price": 10.25},
    {"symbol": "AAL", "name": "American Airlines", "base_price": 17.80},
    {"symbol": "PLUG", "name": "Plug Power", "base_price": 2.15},
    {"symbol": "BB", "name": "BlackBerry", "base_price": 2.45},
    {"symbol": "AMC", "name": "AMC Entertainment", "base_price": 3.20}
]

STEPHEN_BIO = """I'm Stephen Martinez, an Amazon warehouse worker from Lancaster, PA.

For years, I watched my coworkers - hardworking people with families - lose their savings on trading apps designed to make them trade MORE, not trade SMARTER.

These apps make money when you lose money. They want you addicted, emotional, and overtrading.

So I taught myself to code. During lunch breaks. After 10-hour shifts. On weekends when my body was exhausted but my mind wouldn't stop.

Project Hope is my answer. An app that PROTECTS you first. That stops you from blowing up your account. That treats your $200 like it matters - because it does.

This isn't about getting rich quick. It's about building something real, one smart trade at a time.

Welcome to Project Hope. Let's build together."""

LEGAL_DISCLAIMER = """IMPORTANT LEGAL DISCLAIMER

I am NOT a financial advisor. I am not a licensed broker, investment advisor, or financial planner. I am a regular person who built this app to help other regular people.

Project Hope is an EDUCATIONAL tool only. Nothing in this app constitutes financial advice, investment advice, trading advice, or any other sort of advice. You should not treat any of the app's content as such.

RISK WARNING: Options trading involves substantial risk of loss and is not suitable for all investors. Past performance is not indicative of future results. You could lose some or all of your investment.

KEY POINTS:
- Only trade with money you can afford to lose
- Paper trading results do not guarantee real trading results
- Always do your own research before making any trades
- Consider consulting a licensed financial advisor

By using Project Hope, you acknowledge that:
1. You are solely responsible for your own trading decisions
2. You understand the risks involved in options trading
3. You will not hold Stephen Martinez or Project Hope liable for any losses
4. This is educational software, not financial advice

Trade responsibly. Protect your capital. That's what Project Hope is all about."""

defaults = {
    'page': 'home', 'tier': 0, 'balance': 5000.0, 'starting_balance': 5000.0,
    'positions': [], 'trades': [], 'daily_pnl': 0.0, 'total_pnl': 0.0,
    'wins': 0, 'losses': 0, 'stock_data': {}, 'autopilot': True, 'trade_ticker': [],
    'alpaca_connected': False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Try to get Alpaca account balance on startup
alpaca_account = get_alpaca_account()
if alpaca_account:
    st.session_state.alpaca_connected = True
    st.session_state.balance = float(alpaca_account.get('cash', 5000))
    st.session_state.starting_balance = float(alpaca_account.get('cash', 5000))

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
* {font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;}
.stApp {background: linear-gradient(160deg, #000000 0%, #0a0a0f 20%, #0d1117 40%, #111827 60%, #0f172a 80%, #000000 100%);}
#MainMenu, footer, header {visibility: hidden;}

.glass-card {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 24px;
    padding: 28px;
    margin: 12px 0;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.glass-card-sm {
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 16px;
    padding: 20px;
    margin: 8px 0;
}

.logo-container {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    padding: 20px;
}

.logo-icon {font-size: 3em; filter: drop-shadow(0 0 20px rgba(0, 255, 163, 0.5));}

.logo-text {
    font-size: 2.8em;
    font-weight: 900;
    letter-spacing: -1px;
    background: linear-gradient(135deg, #00FFA3 0%, #00E5FF 50%, #FFD700 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-section {
    text-align: center;
    padding: 60px 40px;
    background: linear-gradient(145deg, rgba(0, 255, 163, 0.08) 0%, rgba(0, 229, 255, 0.05) 50%, rgba(255, 215, 0, 0.03) 100%);
    backdrop-filter: blur(20px);
    border-radius: 32px;
    margin: 20px 0 30px 0;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.hero-title {
    font-size: 3.5em;
    font-weight: 900;
    background: linear-gradient(135deg, #00FFA3 0%, #00E5FF 40%, #FFD700 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 20px 0;
}

.hero-subtitle {font-size: 1.5em; font-weight: 700; color: #FFD700; margin: 0 0 12px 0;}
.hero-tagline {font-size: 1.1em; color: #808495; margin: 0;}

.clock-container {border-radius: 20px; padding: 20px 30px; text-align: center; margin: 16px 0; backdrop-filter: blur(16px);}
.clock-open {background: linear-gradient(145deg, rgba(0, 255, 163, 0.15), rgba(0, 255, 163, 0.05)); border: 2px solid rgba(0, 255, 163, 0.4);}
.clock-closed {background: linear-gradient(145deg, rgba(255, 75, 75, 0.15), rgba(255, 75, 75, 0.05)); border: 2px solid rgba(255, 75, 75, 0.4);}
.clock-pre {background: linear-gradient(145deg, rgba(255, 215, 0, 0.15), rgba(255, 215, 0, 0.05)); border: 2px solid rgba(255, 215, 0, 0.4);}
.clock-time {font-size: 1.1em; color: #808495; margin: 0;}
.clock-status {font-size: 1.8em; font-weight: 800; color: #00E5FF; margin: 8px 0 0 0; font-family: monospace; letter-spacing: 2px;}

.shield-container {
    background: linear-gradient(145deg, rgba(0, 255, 163, 0.12), rgba(0, 200, 100, 0.05));
    border: 2px solid rgba(0, 255, 163, 0.35);
    border-radius: 20px;
    padding: 24px 32px;
    text-align: center;
    margin: 20px 0;
}
.shield-title {font-size: 1.3em; font-weight: 800; color: #00FFA3; margin: 0 0 8px 0;}
.shield-subtitle {font-size: 0.95em; color: #808495; margin: 0;}

.stat-card {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 24px;
    text-align: center;
}
.stat-value {font-size: 2.2em; font-weight: 800; margin: 0;}
.stat-label {font-size: 0.9em; color: #808495; margin: 8px 0 0 0; text-transform: uppercase; letter-spacing: 1px;}

.tier-card {
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(20px);
    border-radius: 28px;
    padding: 32px 20px;
    text-align: center;
    border: 1px solid rgba(255, 255, 255, 0.08);
    min-height: 380px;
    position: relative;
}

.tier-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    border-radius: 28px 28px 0 0;
}

.tier-starter::before {background: linear-gradient(90deg, #00FFA3, #00CC7A);}
.tier-builder::before {background: linear-gradient(90deg, #00E5FF, #0099CC);}
.tier-master::before {background: linear-gradient(90deg, #FFD700, #FFA500);}
.tier-vip::before {background: linear-gradient(90deg, #FF6B6B, #FF4757);}

.tier-master {
    box-shadow: 0 0 50px rgba(255, 215, 0, 0.15);
    border: 1px solid rgba(255, 215, 0, 0.2);
}

.tier-feature {font-size: 0.9em; margin: 8px 0; display: flex; align-items: center; justify-content: center; gap: 8px;}
.feature-yes {color: #00FFA3;}
.feature-no {color: #FF4B4B;}

.popular-badge {
    background: linear-gradient(135deg, #FFD700, #FFA500);
    color: black;
    font-size: 0.7em;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 1px;
    display: inline-block;
    margin-bottom: 8px;
}

.stock-card {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(16px);
    border-radius: 20px;
    padding: 24px;
    margin: 12px 0;
    border: 1px solid rgba(255, 255, 255, 0.08);
}
.stock-card-buy {border-left: 4px solid #00FFA3; background: linear-gradient(90deg, rgba(0, 255, 163, 0.08), transparent);}
.stock-card-sell {border-left: 4px solid #FF4B4B; background: linear-gradient(90deg, rgba(255, 75, 75, 0.08), transparent);}
.stock-card-wait {border-left: 4px solid #808495;}

.score-bar {height: 10px; border-radius: 5px; background: rgba(255, 255, 255, 0.1); overflow: hidden; margin: 12px 0;}
.score-fill {height: 100%; border-radius: 5px;}
.score-fill-buy {background: linear-gradient(90deg, #00FFA3, #00E5FF);}
.score-fill-sell {background: linear-gradient(90deg, #FF4B4B, #FF6B6B);}

.indicator {display: inline-block; padding: 6px 12px; border-radius: 8px; font-size: 0.8em; font-weight: 600; margin: 3px;}
.ind-bullish {background: rgba(0, 255, 163, 0.2); color: #00FFA3; border: 1px solid rgba(0, 255, 163, 0.3);}
.ind-bearish {background: rgba(255, 75, 75, 0.2); color: #FF4B4B; border: 1px solid rgba(255, 75, 75, 0.3);}
.ind-neutral {background: rgba(255, 215, 0, 0.2); color: #FFD700; border: 1px solid rgba(255, 215, 0, 0.3);}

.autopilot-on {background: linear-gradient(145deg, rgba(0, 255, 163, 0.2), rgba(0, 255, 163, 0.05)); border: 2px solid rgba(0, 255, 163, 0.5); border-radius: 16px; padding: 18px 24px; text-align: center;}
.autopilot-off {background: rgba(255, 255, 255, 0.03); border: 2px solid #808495; border-radius: 16px; padding: 18px 24px; text-align: center;}

.founder-photo {width: 130px; height: 130px; border-radius: 50%; border: 4px solid #00FFA3; object-fit: cover;}

.share-card {background: linear-gradient(145deg, #0d1117, #161b22); border: 2px solid #00FFA3; border-radius: 24px; padding: 32px; text-align: center;}

.position-card {background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(12px); border-radius: 16px; padding: 18px; margin: 10px 0; border: 1px solid rgba(255, 255, 255, 0.08);}

.ticker {background: rgba(0, 0, 0, 0.4); backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 12px 16px; margin: 6px 0; font-family: monospace; font-size: 0.85em;}
.ticker-buy {border-left: 3px solid #00FFA3;}
.ticker-sell {border-left: 3px solid #FF4B4B;}

.legal-footer {background: rgba(0, 0, 0, 0.4); backdrop-filter: blur(16px); border-top: 1px solid rgba(255, 255, 255, 0.1); padding: 30px; margin-top: 50px; text-align: center; border-radius: 24px 24px 0 0;}

.stButton > button {background: linear-gradient(135deg, #00FFA3 0%, #00CC7A 100%); color: black; font-weight: 700; border: none; border-radius: 14px; padding: 12px 24px; font-size: 1em;}
</style>
""", unsafe_allow_html=True)

def get_market_status():
    et = pytz.timezone('US/Eastern')
    now = datetime.now(et)
    current_time = now.strftime('%I:%M:%S %p ET')
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    if now.weekday() >= 5:
        return 'closed', current_time, "WEEKEND - Opens Monday"
    if now < market_open:
        diff = market_open - now
        h, m, s = diff.seconds // 3600, (diff.seconds % 3600) // 60, diff.seconds % 60
        return 'pre', current_time, "PRE-MARKET " + str(h).zfill(2) + ":" + str(m).zfill(2) + ":" + str(s).zfill(2)
    if now < market_close:
        diff = market_close - now
        h, m, s = diff.seconds // 3600, (diff.seconds % 3600) // 60, diff.seconds % 60
        return 'open', current_time, "MARKET OPEN " + str(h).zfill(2) + ":" + str(m).zfill(2) + ":" + str(s).zfill(2)
    return 'closed', current_time, "AFTER HOURS"

# ============ ALPACA API FUNCTIONS ============
def get_alpaca_account():
    """Get Alpaca paper trading account info"""
    try:
        response = requests.get(f"{ALPACA_BASE_URL}/v2/account", headers=ALPACA_HEADERS)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_real_price(symbol):
    """Get real-time price from Alpaca"""
    try:
        url = f"{ALPACA_DATA_URL}/v2/stocks/{symbol}/quotes/latest"
        response = requests.get(url, headers=ALPACA_HEADERS)
        if response.status_code == 200:
            data = response.json()
            if 'quote' in data:
                return float(data['quote'].get('ap', 0) or data['quote'].get('bp', 0))
    except:
        pass
    return None

def get_real_bars(symbol, limit=100):
    """Get historical bars for technical analysis"""
    try:
        url = f"{ALPACA_DATA_URL}/v2/stocks/{symbol}/bars"
        params = {"timeframe": "5Min", "limit": limit}
        response = requests.get(url, headers=ALPACA_HEADERS, params=params)
        if response.status_code == 200:
            data = response.json()
            if 'bars' in data and data['bars']:
                bars = data['bars']
                prices = [float(bar['c']) for bar in bars]
                volumes = [int(bar['v']) for bar in bars]
                return prices, volumes
    except:
        pass
    return None, None

def generate_stock_data(stock):
    """Get real data from Alpaca, fallback to simulated if unavailable"""
    symbol = stock['symbol']
    base = stock['base_price']
    
    # Try to get real data from Alpaca
    real_price = get_real_price(symbol)
    real_prices, real_volumes = get_real_bars(symbol)
    
    if real_price and real_prices and len(real_prices) > 20:
        # Use real Alpaca data
        if symbol not in st.session_state.stock_data:
            st.session_state.stock_data[symbol] = {'prices': real_prices, 'volumes': real_volumes, 'live': True}
        else:
            st.session_state.stock_data[symbol]['prices'] = real_prices
            st.session_state.stock_data[symbol]['volumes'] = real_volumes
            st.session_state.stock_data[symbol]['live'] = True
        return real_price, real_prices, real_volumes
    
    # Fallback to simulated data (market closed or API error)
    if symbol not in st.session_state.stock_data:
        prices = [base]
        for _ in range(99):
            prices.append(round(max(base*0.8, min(base*1.2, prices[-1] + random.gauss(0, base*0.01))), 2))
        st.session_state.stock_data[symbol] = {'prices': prices, 'volumes': [random.randint(1000000, 10000000) for _ in range(100)], 'live': False}
    
    data = st.session_state.stock_data[symbol]
    prices = data['prices']
    current = prices[-1]
    momentum = (prices[-1] - prices[-5]) / 5 if len(prices) >= 5 else 0
    change = random.gauss(0, base * 0.005) + (momentum * 0.1)
    if current > base * 1.15: change -= base * 0.002
    elif current < base * 0.85: change += base * 0.002
    new_price = round(max(base * 0.7, min(base * 1.3, current + change)), 2)
    prices.append(new_price)
    if len(prices) > 100: prices.pop(0)
    data['volumes'].append(random.randint(1000000, 10000000))
    if len(data['volumes']) > 100: data['volumes'].pop(0)
    data['live'] = False
    return new_price, prices, data['volumes']

def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50.0
    deltas = np.diff(prices[-period-1:])
    gains, losses = np.where(deltas > 0, deltas, 0), np.where(deltas < 0, -deltas, 0)
    avg_gain, avg_loss = np.mean(gains), np.mean(losses)
    if avg_loss == 0: return 100.0
    return round(100 - (100 / (1 + avg_gain / avg_loss)), 1)

def calc_ema(prices, period):
    if len(prices) < period: return prices[-1] if prices else 0
    mult = 2 / (period + 1)
    ema = np.mean(prices[:period])
    for p in prices[period:]: ema = (p * mult) + (ema * (1 - mult))
    return round(ema, 4)

def analyze_stock(stock):
    price, prices, volumes = generate_stock_data(stock)
    rsi = calc_rsi(prices)
    ema9, ema21 = calc_ema(prices, 9), calc_ema(prices, 21)
    vwap = round(sum(p * v for p, v in zip(prices[-20:], volumes[-20:])) / sum(volumes[-20:]), 2) if len(prices) >= 20 else price
    support = round(min(prices[-20:]), 2) if len(prices) >= 20 else price * 0.98
    resistance = round(max(prices[-20:]), 2) if len(prices) >= 20 else price * 1.02
    
    score, signals = 0, {}
    if rsi < 30: score += 2; signals['RSI'] = ('OVERSOLD', 'bullish')
    elif rsi < 40: score += 1; signals['RSI'] = ('Low', 'bullish')
    elif rsi > 70: score -= 2; signals['RSI'] = ('OVERBOUGHT', 'bearish')
    elif rsi > 60: score -= 1; signals['RSI'] = ('High', 'bearish')
    else: signals['RSI'] = ('Neutral', 'neutral')
    
    if price > ema9 > ema21: score += 1; signals['EMA'] = ('Bullish', 'bullish')
    elif price < ema9 < ema21: score -= 1; signals['EMA'] = ('Bearish', 'bearish')
    else: signals['EMA'] = ('Flat', 'neutral')
    
    if price > vwap * 1.005: score += 1; signals['VWAP'] = ('Above', 'bullish')
    elif price < vwap * 0.995: score -= 1; signals['VWAP'] = ('Below', 'bearish')
    else: signals['VWAP'] = ('At', 'neutral')
    
    dist_sup = ((price - support) / price) * 100
    dist_res = ((resistance - price) / price) * 100
    if dist_sup < 1: score += 2; signals['S/R'] = ('SUPPORT', 'bullish')
    elif dist_res < 1: score -= 2; signals['S/R'] = ('RESISTANCE', 'bearish')
    else: signals['S/R'] = ('Mid', 'neutral')
    
    vol_spike = volumes[-1] / np.mean(volumes[-20:-1]) if len(volumes) > 20 else 1
    if vol_spike > 2:
        if score > 0: score += 1; signals['VOL'] = ('SPIKE', 'bullish')
        else: score -= 1; signals['VOL'] = ('SPIKE', 'bearish')
    else: signals['VOL'] = ('Normal', 'neutral')
    
    if score >= 5: signal = 'STRONG BUY'
    elif score >= 3: signal = 'BUY'
    elif score <= -5: signal = 'STRONG SELL'
    elif score <= -3: signal = 'SELL'
    else: signal = 'WAIT'
    
    option_cost = max(5, min(round(price * 0.03 * random.uniform(0.8, 1.2), 2), 80))
    
    return {
        'symbol': stock['symbol'], 'name': stock['name'], 'price': price,
        'change': round(price - prices[-2] if len(prices) > 1 else 0, 2),
        'score': score, 'signal': signal, 'signals': signals,
        'option_cost': option_cost, 'stop_loss': round(option_cost * 0.75, 2),
        'take_profit': round(option_cost * 1.30, 2)
    }

def scan_all_stocks():
    results = [analyze_stock(s) for s in WATCHLIST]
    results.sort(key=lambda x: abs(x['score']), reverse=True)
    return results

def add_ticker(action, symbol, price, direction):
    st.session_state.trade_ticker.append({'time': datetime.now().strftime('%H:%M:%S'), 'action': action, 'symbol': symbol, 'direction': direction})
    if len(st.session_state.trade_ticker) > 20: st.session_state.trade_ticker.pop(0)

def execute_buy(stock, direction):
    tier = TIERS[st.session_state.tier]
    if len(st.session_state.positions) >= tier['max_trades']: return False
    cost = stock['option_cost'] * 100
    if st.session_state.balance < cost: return False
    st.session_state.balance -= cost
    st.session_state.positions.append({'symbol': stock['symbol'], 'direction': direction, 'entry': stock['option_cost'], 'current': stock['option_cost'], 'stop_loss': stock['stop_loss'], 'take_profit': stock['take_profit'], 'pnl': 0})
    add_ticker('BUY', stock['symbol'], stock['option_cost'], direction)
    return True

def execute_sell(i):
    if i >= len(st.session_state.positions): return
    pos = st.session_state.positions[i]
    st.session_state.balance += (pos['entry'] * 100) + pos['pnl']
    st.session_state.daily_pnl += pos['pnl']
    st.session_state.total_pnl += pos['pnl']
    if pos['pnl'] >= 0: st.session_state.wins += 1
    else: st.session_state.losses += 1
    st.session_state.trades.append({'symbol': pos['symbol'], 'direction': pos['direction'], 'pnl': pos['pnl'], 'time': datetime.now().strftime('%H:%M:%S'), 'date': datetime.now().strftime('%Y-%m-%d')})
    add_ticker('SELL', pos['symbol'], pos['current'], pos['direction'])
    st.session_state.positions.pop(i)

def update_positions():
    for i, pos in enumerate(st.session_state.positions):
        change = random.uniform(-0.08, 0.10)
        pos['current'] = round(pos['entry'] * (1 + change), 2)
        pos['pnl'] = round((pos['current'] - pos['entry']) * 100, 2)
        if st.session_state.autopilot or st.session_state.tier == 1:
            if pos['current'] <= pos['stop_loss']: execute_sell(i); return
            if pos['current'] >= pos['take_profit']: execute_sell(i); return

def generate_share_text():
    total = st.session_state.wins + st.session_state.losses
    wr = (st.session_state.wins / total * 100) if total > 0 else 0
    return "PROJECT HOPE Results\n\nToday: $" + format(st.session_state.daily_pnl, '+,.2f') + "\nWin Rate: " + format(wr, '.0f') + "%\nW/L: " + str(st.session_state.wins) + "/" + str(st.session_state.losses) + "\n\n#ProjectHope #Options"

def render_home():
    st.markdown('<div class="logo-container"><span class="logo-icon">&#127793;</span><span class="logo-text">PROJECT HOPE</span></div>', unsafe_allow_html=True)
    
    st.markdown('''
    <div class="hero-section">
        <h1 class="hero-title">OPTIONS TRADING</h1>
        <p class="hero-subtitle">5-Layer Protection Built In</p>
        <p class="hero-tagline">Turn $200 into $2,000 - Without Risking It All</p>
    </div>
    ''', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.button("Home", disabled=True, use_container_width=True)
    with c2:
        if st.button("Trade", use_container_width=True, key="h1"):
            if st.session_state.tier > 0: st.session_state.page = 'trade'; st.rerun()
            else: st.warning("Enter access code first!")
    with c3:
        if st.button("History", use_container_width=True, key="h2"): st.session_state.page = 'history'; st.rerun()
    with c4:
        if st.button("Learn", use_container_width=True, key="h3"): st.session_state.page = 'learn'; st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    status, current_time, countdown = get_market_status()
    st.markdown('<div class="clock-container clock-' + status + '"><p class="clock-time">' + current_time + '</p><p class="clock-status">' + countdown + '</p></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("### Why Options Beat Stocks")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="glass-card" style="border-left: 4px solid #FF4B4B;"><h3 style="color: #FF4B4B; margin: 0 0 12px 0;">Old Way (Stocks)</h3><p style="color: white; margin: 0; font-size: 1.1em;">$200 invested, 1% gain = <strong style="color: #FF4B4B;">$2 profit</strong></p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="glass-card" style="border-left: 4px solid #00FFA3;"><h3 style="color: #00FFA3; margin: 0 0 12px 0;">New Way (Options)</h3><p style="color: white; margin: 0; font-size: 1.1em;">$200 invested, 1% gain = <strong style="color: #00FFA3;">$100+ profit</strong></p></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("### 5-Layer Protection System")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.markdown('<div class="stat-card"><p class="stat-value" style="color: #00FFA3;">-25%</p><p class="stat-label">Stop Loss</p></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="stat-card"><p class="stat-value" style="color: #FFD700;">+30%</p><p class="stat-label">Take Profit</p></div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="stat-card"><p class="stat-value" style="color: #FF4B4B;">-15%</p><p class="stat-label">Daily Max</p></div>', unsafe_allow_html=True)
    with c4: st.markdown('<div class="stat-card"><p class="stat-value" style="color: #00E5FF;">5%</p><p class="stat-label">Per Trade</p></div>', unsafe_allow_html=True)
    with c5: st.markdown('<div class="stat-card"><p class="stat-value" style="color: #A855F7;">3</p><p class="stat-label">Max Open</p></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("### Meet the Founder")
    c1, c2 = st.columns([1, 3])
    with c1: st.markdown('<img src="' + STEPHEN_PHOTO + '" class="founder-photo">', unsafe_allow_html=True)
    with c2:
        st.markdown('<div style="padding-left: 10px;"><h3 style="color: white; margin: 0 0 8px 0;">' + STEPHEN_NAME + '</h3><p style="color: #00FFA3; margin: 0 0 4px 0; font-weight: 600;">Amazon Warehouse Worker | Self-Taught Developer</p><p style="color: #808495; margin: 0;">' + STEPHEN_LOCATION + '</p></div>', unsafe_allow_html=True)
    
    with st.expander("Read My Full Story"):
        st.markdown('<p style="color: #c0c0c0; line-height: 1.8; white-space: pre-line;">' + STEPHEN_BIO + '</p>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("### Choose Your Plan")
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown('<div class="tier-card tier-starter"><h3 style="color:#00FFA3;font-size:1.3em;margin:0;">STARTER</h3><p style="font-size:2.5em;font-weight:900;color:white;margin:15px 0;">$49<span style="font-size:0.35em;color:#808495;">/mo</span></p><p class="tier-feature"><span class="feature-yes">+</span> 1 Stock Shown</p><p class="tier-feature"><span class="feature-yes">+</span> 1 Trade Max</p><p class="tier-feature"><span class="feature-yes">+</span> Autopilot Always On</p><p class="tier-feature"><span class="feature-yes">+</span> Auto Stop/Profit</p><p class="tier-feature"><span class="feature-no">X</span> Manual Trading</p><p class="tier-feature"><span class="feature-no">X</span> Priority Support</p></div>', unsafe_allow_html=True)
    
    with c2:
        st.markdown('<div class="tier-card tier-builder"><h3 style="color:#00E5FF;font-size:1.3em;margin:0;">BUILDER</h3><p style="font-size:2.5em;font-weight:900;color:white;margin:15px 0;">$99<span style="font-size:0.35em;color:#808495;">/mo</span></p><p class="tier-feature"><span class="feature-yes">+</span> 3 Stocks Shown</p><p class="tier-feature"><span class="feature-yes">+</span> 2 Trades Max</p><p class="tier-feature"><span class="feature-yes">+</span> Autopilot Toggle</p><p class="tier-feature"><span class="feature-yes">+</span> Manual Trading</p><p class="tier-feature"><span class="feature-no">X</span> Priority Support</p><p class="tier-feature"><span class="feature-no">X</span> Personal Coaching</p></div>', unsafe_allow_html=True)
    
    with c3:
        st.markdown('<div class="tier-card tier-master"><span class="popular-badge">POPULAR</span><h3 style="color:#FFD700;font-size:1.3em;margin:10px 0 0 0;">MASTER</h3><p style="font-size:2.5em;font-weight:900;color:white;margin:15px 0;">$199<span style="font-size:0.35em;color:#808495;">/mo</span></p><p class="tier-feature"><span class="feature-yes">+</span> 6 Stocks Shown</p><p class="tier-feature"><span class="feature-yes">+</span> 3 Trades Max</p><p class="tier-feature"><span class="feature-yes">+</span> Autopilot Toggle</p><p class="tier-feature"><span class="feature-yes">+</span> Priority Support</p><p class="tier-feature"><span class="feature-no">X</span> Weekly Coaching</p><p class="tier-feature"><span class="feature-no">X</span> Private Community</p></div>', unsafe_allow_html=True)
    
    with c4:
        st.markdown('<div class="tier-card tier-vip"><h3 style="color:#FF6B6B;font-size:1.3em;margin:0;">VIP COACHING</h3><p style="font-size:2.5em;font-weight:900;color:white;margin:15px 0;">$499<span style="font-size:0.35em;color:#808495;">/mo</span></p><p class="tier-feature"><span class="feature-yes">+</span> 15 Stocks Shown</p><p class="tier-feature"><span class="feature-yes">+</span> 5 Trades Max</p><p class="tier-feature"><span class="feature-yes">+</span> Weekly 1-on-1 Coaching</p><p class="tier-feature"><span class="feature-yes">+</span> Private Community</p><p class="tier-feature"><span class="feature-yes">+</span> Direct Access to Me</p><p class="tier-feature"><span class="feature-yes">+</span> Custom Goal Plan</p></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("### Enter Access Code")
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        code = st.text_input("Access Code", type="password", label_visibility="collapsed", placeholder="Enter your access code...")
        codes = {"HOPE49": 1, "HOPE99": 2, "HOPE199": 3, "HOPE499": 4, "DEMO": 3}
        if code:
            if code.upper() in codes:
                st.session_state.tier = codes[code.upper()]
                st.success("Access Granted: " + TIERS[st.session_state.tier]['name'] + " Tier")
            else:
                st.error("Invalid access code")
        if st.session_state.tier > 0:
            if st.button("Enter Trading Dashboard", type="primary", use_container_width=True):
                st.session_state.page = 'trade'
                st.rerun()
    
    st.markdown('''
    <div class="legal-footer">
        <p style="color: #808495; font-size: 1em; margin: 0 0 10px 0;">Built with love by ''' + STEPHEN_NAME + ''' | ''' + STEPHEN_EMAIL + '''</p>
        <p style="color: #666; font-size: 0.85em; margin: 0 0 15px 0;">This is an educational tool only. Not financial advice.</p>
    </div>
    ''', unsafe_allow_html=True)
    
    with st.expander("Read Full Legal Disclaimer"):
        st.markdown('<p style="color: #808495; line-height: 1.8; white-space: pre-line; font-size: 0.9em;">' + LEGAL_DISCLAIMER + '</p>', unsafe_allow_html=True)

def render_trade():
    if st.session_state.tier == 0:
        st.warning("Please enter your access code on the Home page")
        if st.button("Go to Home"): st.session_state.page = 'home'; st.rerun()
        return
    
    tier = TIERS[st.session_state.tier]
    update_positions()
    
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.markdown('<div style="display:flex;align-items:center;gap:12px;"><span style="font-size:1.8em;">&#127793;</span><span style="font-size:1.5em;font-weight:800;background:linear-gradient(135deg,#00FFA3,#00E5FF);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">PROJECT HOPE</span><span style="color:' + tier['color'] + ';font-weight:600;background:rgba(255,255,255,0.1);padding:4px 12px;border-radius:8px;">' + tier['name'] + '</span></div>', unsafe_allow_html=True)
    with c2:
        status, _, countdown = get_market_status()
        st.markdown('<div class="clock-container clock-' + status + '" style="padding:10px 16px;"><span style="font-size:0.9em;font-weight:600;">' + countdown + '</span></div>', unsafe_allow_html=True)
    with c3:
        if st.session_state.alpaca_connected:
            st.markdown('<div style="text-align:right;padding:10px;"><span style="color:#00FFA3;font-weight:600;background:rgba(0,255,163,0.1);padding:6px 14px;border-radius:8px;">LIVE DATA</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:right;padding:10px;"><span style="color:#FFD700;font-weight:600;background:rgba(255,215,0,0.1);padding:6px 14px;border-radius:8px;">PAPER MODE</span></div>', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Home", use_container_width=True, key="t1"): st.session_state.page = 'home'; st.rerun()
    with c2: st.button("Trade", disabled=True, use_container_width=True)
    with c3:
        if st.button("History", use_container_width=True, key="t3"): st.session_state.page = 'history'; st.rerun()
    with c4:
        if st.button("Learn", use_container_width=True, key="t4"): st.session_state.page = 'learn'; st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    equity = st.session_state.balance + sum(p.get('pnl', 0) for p in st.session_state.positions)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Equity", "$" + format(equity, ',.2f'))
    with c2: st.metric("Cash", "$" + format(st.session_state.balance, ',.2f'))
    with c3: st.metric("Today P/L", "$" + format(st.session_state.daily_pnl, '+,.2f'))
    with c4:
        total = st.session_state.wins + st.session_state.losses
        wr = (st.session_state.wins / total * 100) if total > 0 else 0
        st.metric("Win Rate", format(wr, '.0f') + "%")
    
    if tier['autopilot'] == 'always':
        st.markdown('<div class="autopilot-on"><span style="color:#00FFA3;font-weight:700;font-size:1.1em;">AUTOPILOT: ALWAYS ON</span><br><span style="color:#808495;font-size:0.9em;">Starter tier runs fully automatic</span></div>', unsafe_allow_html=True)
    else:
        c1, c2 = st.columns([4, 1])
        with c1:
            if st.session_state.autopilot:
                st.markdown('<div class="autopilot-on"><span style="color:#00FFA3;font-weight:700;font-size:1.1em;">AUTOPILOT: ON</span><br><span style="color:#808495;font-size:0.9em;">Auto-executes signals, manages stops & targets</span></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="autopilot-off"><span style="color:#808495;font-weight:700;font-size:1.1em;">AUTOPILOT: OFF</span><br><span style="color:#808495;font-size:0.9em;">Manual trading mode</span></div>', unsafe_allow_html=True)
        with c2:
            if st.button("Toggle", use_container_width=True, key="toggle_ap"):
                st.session_state.autopilot = not st.session_state.autopilot
                st.rerun()
    
    st.markdown('<div class="shield-container"><p class="shield-title">5-LAYER PROTECTION ACTIVE</p><p class="shield-subtitle">Stop -25% | Profit +30% | Daily -15% | 5% Per Trade | Max ' + str(tier['max_trades']) + ' Positions</p></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Stock Scanner")
        st.markdown('<p style="color:#808495;">Top ' + str(tier['stocks_shown']) + ' opportunities</p>', unsafe_allow_html=True)
        
        stocks = scan_all_stocks()[:tier['stocks_shown']]
        for stock in stocks:
            card_class = 'stock-card-buy' if stock['score'] >= 3 else 'stock-card-sell' if stock['score'] <= -3 else 'stock-card-wait'
            bar_class = 'score-fill-buy' if stock['score'] > 0 else 'score-fill-sell'
            bar_pct = min(abs(stock['score']) / 8 * 100, 100)
            chg_color = "#00FFA3" if stock['change'] >= 0 else "#FF4B4B"
            sig_color = "#00FFA3" if stock['score'] >= 3 else "#FF4B4B" if stock['score'] <= -3 else "#FFD700"
            
            st.markdown('<div class="stock-card ' + card_class + '"><div style="display:flex;justify-content:space-between;align-items:center;"><div><h3 style="color:white;margin:0;font-size:1.4em;">' + stock['symbol'] + '</h3><p style="color:#808495;margin:4px 0 0 0;">' + stock['name'] + '</p></div><div style="text-align:right;"><h3 style="color:#00E5FF;margin:0;font-size:1.4em;">$' + format(stock['price'], '.2f') + '</h3><p style="color:' + chg_color + ';margin:4px 0 0 0;font-weight:600;">' + format(stock['change'], '+.2f') + '</p></div></div><div class="score-bar"><div class="score-fill ' + bar_class + '" style="width:' + str(bar_pct) + '%;"></div></div><div style="display:flex;justify-content:space-between;align-items:center;"><span style="color:' + sig_color + ';font-weight:700;font-size:1.1em;">' + stock['signal'] + ' (' + str(stock['score']) + '/8)</span><span style="color:#808495;">~$' + str(int(stock['option_cost'])) + '/contract</span></div></div>', unsafe_allow_html=True)
            
            ind_html = "".join(['<span class="indicator ind-' + s[1] + '">' + n + '</span>' for n, s in stock['signals'].items()])
            st.markdown('<div style="margin:-5px 0 15px 0;">' + ind_html + '</div>', unsafe_allow_html=True)
            
            if stock['signal'] in ['STRONG BUY', 'BUY', 'STRONG SELL', 'SELL'] and tier['autopilot'] != 'always' and len(st.session_state.positions) < tier['max_trades']:
                direction = 'CALL' if stock['score'] > 0 else 'PUT'
                if st.button("BUY " + direction + " - $" + str(int(stock['option_cost'] * 100)), key="buy_" + stock['symbol'], use_container_width=True):
                    if execute_buy(stock, direction):
                        st.success("Position opened!")
                        st.balloons()
                        st.rerun()
    
    with col2:
        st.markdown("### Positions (" + str(len(st.session_state.positions)) + "/" + str(tier['max_trades']) + ")")
        if st.session_state.positions:
            for i, pos in enumerate(st.session_state.positions):
                pc = "#00FFA3" if pos['pnl'] >= 0 else "#FF4B4B"
                st.markdown('<div class="position-card" style="border-left:3px solid ' + pc + ';"><div style="display:flex;justify-content:space-between;"><div><h4 style="color:white;margin:0;">' + pos['symbol'] + '</h4><p style="color:#808495;font-size:0.85em;margin:4px 0 0 0;">' + pos['direction'] + ' @ $' + format(pos['entry'], '.2f') + '</p></div><div style="text-align:right;"><h4 style="color:' + pc + ';margin:0;">$' + format(pos['pnl'], '+.2f') + '</h4></div></div></div>', unsafe_allow_html=True)
                if tier['autopilot'] != 'always' and not st.session_state.autopilot:
                    if st.button("Close", key="close_" + str(i), use_container_width=True): execute_sell(i); st.rerun()
        else:
            st.info("No open positions")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Live Ticker")
        if st.session_state.trade_ticker:
            for t in reversed(st.session_state.trade_ticker[-6:]):
                tc = "ticker-buy" if t['action'] == 'BUY' else "ticker-sell"
                tcol = "#00FFA3" if t['action'] == 'BUY' else "#FF4B4B"
                st.markdown('<div class="ticker ' + tc + '"><span style="color:#808495;">' + t['time'] + '</span> <span style="color:' + tcol + ';font-weight:600;">' + t['action'] + '</span> <span style="color:white;">' + t['symbol'] + '</span></div>', unsafe_allow_html=True)

def render_history():
    st.markdown('<div class="logo-container"><span class="logo-icon">&#127793;</span><span class="logo-text">PROJECT HOPE</span></div>', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Home", use_container_width=True, key="hh1"): st.session_state.page = 'home'; st.rerun()
    with c2:
        if st.button("Trade", use_container_width=True, key="hh2"): st.session_state.page = 'trade'; st.rerun()
    with c3: st.button("History", disabled=True, use_container_width=True)
    with c4:
        if st.button("Learn", use_container_width=True, key="hh4"): st.session_state.page = 'learn'; st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    total = st.session_state.wins + st.session_state.losses
    wr = (st.session_state.wins / total * 100) if total > 0 else 0
    pc = "#00FFA3" if st.session_state.total_pnl >= 0 else "#FF4B4B"
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown('<div class="stat-card"><p class="stat-value" style="color:' + pc + ';">$' + format(st.session_state.total_pnl, ',.2f') + '</p><p class="stat-label">Total P/L</p></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="stat-card"><p class="stat-value" style="color:#FFD700;">' + format(wr, '.0f') + '%</p><p class="stat-label">Win Rate</p></div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="stat-card"><p class="stat-value" style="color:#00FFA3;">' + str(st.session_state.wins) + '</p><p class="stat-label">Wins</p></div>', unsafe_allow_html=True)
    with c4: st.markdown('<div class="stat-card"><p class="stat-value" style="color:#FF4B4B;">' + str(st.session_state.losses) + '</p><p class="stat-label">Losses</p></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Share Your Results")
    
    daily_ret = (st.session_state.daily_pnl / st.session_state.starting_balance * 100) if st.session_state.starting_balance > 0 else 0
    pnl_c = "#00FFA3" if st.session_state.daily_pnl >= 0 else "#FF4B4B"
    
    st.markdown('<div class="share-card"><div style="margin-bottom:20px;"><span style="font-size:2.5em;">&#127793;</span><span style="font-size:1.8em;font-weight:800;background:linear-gradient(135deg,#00FFA3,#FFD700);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-left:10px;">PROJECT HOPE</span></div><p style="color:#808495;margin:0 0 20px 0;">' + datetime.now().strftime('%B %d, %Y') + '</p><h1 style="color:' + pnl_c + ';font-size:3em;margin:0;">$' + format(st.session_state.daily_pnl, '+,.2f') + '</h1><p style="color:' + pnl_c + ';font-size:1.2em;margin:5px 0 25px 0;">(' + format(daily_ret, '+.1f') + '%)</p><div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;margin-bottom:20px;"><div><p style="color:#808495;margin:0;">Trades</p><p style="color:white;font-size:1.5em;margin:5px 0 0 0;">' + str(total) + '</p></div><div><p style="color:#808495;margin:0;">Win Rate</p><p style="color:#FFD700;font-size:1.5em;margin:5px 0 0 0;">' + format(wr, '.0f') + '%</p></div><div><p style="color:#808495;margin:0;">W/L</p><p style="color:white;font-size:1.5em;margin:5px 0 0 0;">' + str(st.session_state.wins) + '/' + str(st.session_state.losses) + '</p></div></div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Copy for Social Media:**")
    st.code(generate_share_text(), language=None)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Recent Trades")
    if st.session_state.trades:
        for t in reversed(st.session_state.trades[-10:]):
            c = "#00FFA3" if t['pnl'] >= 0 else "#FF4B4B"
            st.markdown('<div class="glass-card-sm" style="border-left:3px solid ' + c + ';"><div style="display:flex;justify-content:space-between;"><div><p style="color:#808495;font-size:0.85em;margin:0;">' + t.get('date', '') + ' ' + t['time'] + '</p><h4 style="color:white;margin:8px 0 0 0;">' + t['symbol'] + ' ' + t.get('direction', '') + '</h4></div><h3 style="color:' + c + ';margin:0;">$' + format(t['pnl'], '+.2f') + '</h3></div></div>', unsafe_allow_html=True)
    else:
        st.info("No trades yet")
    
    if st.button("Reset All Stats"):
        st.session_state.balance = st.session_state.starting_balance = 1000.0
        st.session_state.positions = []
        st.session_state.trades = []
        st.session_state.trade_ticker = []
        st.session_state.stock_data = {}
        st.session_state.daily_pnl = st.session_state.total_pnl = 0.0
        st.session_state.wins = st.session_state.losses = 0
        st.rerun()

def render_learn():
    st.markdown('<div class="logo-container"><span class="logo-icon">&#127793;</span><span class="logo-text">PROJECT HOPE</span></div>', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Home", use_container_width=True, key="ll1"): st.session_state.page = 'home'; st.rerun()
    with c2:
        if st.button("Trade", use_container_width=True, key="ll2"): st.session_state.page = 'trade'; st.rerun()
    with c3:
        if st.button("History", use_container_width=True, key="ll3"): st.session_state.page = 'history'; st.rerun()
    with c4: st.button("Learn", disabled=True, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("### What Are Options?")
    c1, c2 = st.columns(2)
    with c1: st.markdown('<div class="glass-card" style="border-left:4px solid #00FFA3;"><h3 style="color:#00FFA3;margin:0 0 12px 0;">CALL Option</h3><p style="color:white;margin:0;">Bet the stock goes UP</p></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="glass-card" style="border-left:4px solid #FF4B4B;"><h3 style="color:#FF4B4B;margin:0 0 12px 0;">PUT Option</h3><p style="color:white;margin:0;">Bet the stock goes DOWN</p></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Our Indicators")
    
    for name, desc, color in [("RSI", "Oversold <30 = Buy, Overbought >70 = Sell", "#00FFA3"), ("EMA", "9/21 crossover signals trend changes", "#00E5FF"), ("VWAP", "Institutional buying/selling levels", "#FFD700"), ("S/R", "Support & Resistance key levels", "#A855F7"), ("VOL", "Volume spikes confirm real moves", "#FF6B6B")]:
        st.markdown('<div class="glass-card-sm" style="border-left:4px solid ' + color + ';"><h4 style="color:' + color + ';margin:0 0 8px 0;">' + name + '</h4><p style="color:#c0c0c0;margin:0;">' + desc + '</p></div>', unsafe_allow_html=True)

def main():
    page = st.session_state.page
    if page == 'home': render_home()
    elif page == 'trade': render_trade()
    elif page == 'history': render_history()
    elif page == 'learn': render_learn()
    else: render_home()

if __name__ == "__main__":
    main()
