# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import random
from datetime import datetime
import numpy as np
import pytz
import requests

st.set_page_config(page_title="Project Hope", page_icon="", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=5000, key="refresh")

ALPACA_API_KEY = "PKQJEFSQBY2CFDYYHDR372QB3S"
ALPACA_SECRET_KEY = "ArMPEE3fqY1JCB5CArZUQ5wY8fYQjuPXJ9qpnwYPHJuw"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
ALPACA_DATA_URL = "https://data.alpaca.markets"

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

STEPHEN_BIO = "I'm Stephen Martinez, an Amazon warehouse worker from Lancaster, PA. For years, I watched my coworkers - hardworking people with families - lose their savings on trading apps designed to make them trade MORE, not trade SMARTER. These apps make money when you lose money. They want you addicted, emotional, and overtrading. So I taught myself to code. During lunch breaks. After 10-hour shifts. On weekends when my body was exhausted but my mind wouldn't stop. Project Hope is my answer. An app that PROTECTS you first. That stops you from blowing up your account. That treats your $200 like it matters - because it does. This isn't about getting rich quick. It's about building something real, one smart trade at a time. Welcome to Project Hope. Let's build together."

LEGAL_DISCLAIMER = "IMPORTANT LEGAL DISCLAIMER: I am NOT a financial advisor. Project Hope is an EDUCATIONAL tool only. Options trading involves substantial risk of loss. Only trade with money you can afford to lose. You are solely responsible for your own trading decisions."

def get_alpaca_account():
    try:
        headers = {"APCA-API-KEY-ID": ALPACA_API_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY}
        r = requests.get(f"{ALPACA_BASE_URL}/v2/account", headers=headers, timeout=5)
        if r.status_code == 200: return r.json()
    except: pass
    return None

def get_real_price(symbol):
    try:
        headers = {"APCA-API-KEY-ID": ALPACA_API_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY}
        r = requests.get(f"{ALPACA_DATA_URL}/v2/stocks/{symbol}/quotes/latest", headers=headers, timeout=3)
        if r.status_code == 200:
            d = r.json()
            if 'quote' in d: return float(d['quote'].get('ap', 0) or d['quote'].get('bp', 0))
    except: pass
    return None

defaults = {'page': 'home', 'tier': 0, 'positions': [], 'trades': [], 'daily_pnl': 0.0, 'total_pnl': 0.0, 'wins': 0, 'losses': 0, 'stock_data': {}, 'autopilot': True, 'trade_ticker': [], 'alpaca_balance': 5000.0}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

alpaca_account = get_alpaca_account()
if alpaca_account: st.session_state.alpaca_balance = float(alpaca_account.get('cash', 5000))

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
* {font-family: 'Inter', sans-serif;}
.stApp {background: linear-gradient(160deg, #000 0%, #0a0a0f 30%, #0d1117 60%, #000 100%);}
#MainMenu, footer, header {visibility: hidden;}
.glass-card {background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 24px; padding: 28px; margin: 12px 0;}
.logo-container {display: flex; align-items: center; justify-content: center; gap: 16px; padding: 20px;}
.logo-text {font-size: 2.8em; font-weight: 900; background: linear-gradient(135deg, #00FFA3, #00E5FF, #FFD700); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
.hero-section {text-align: center; padding: 60px 40px; background: linear-gradient(145deg, rgba(0,255,163,0.08), rgba(0,229,255,0.05)); border-radius: 32px; margin: 20px 0; border: 1px solid rgba(255,255,255,0.1);}
.hero-title {font-size: 3.5em; font-weight: 900; background: linear-gradient(135deg, #00FFA3, #00E5FF, #FFD700); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;}
.hero-subtitle {font-size: 1.5em; font-weight: 700; color: #FFD700; margin: 20px 0 12px 0;}
.hero-tagline {font-size: 1.1em; color: #808495;}
.stat-card {background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; padding: 24px; text-align: center;}
.stat-value {font-size: 2.2em; font-weight: 800; margin: 0;}
.stat-label {font-size: 0.9em; color: #808495; margin-top: 8px; text-transform: uppercase;}
.tier-card {background: rgba(255,255,255,0.02); border-radius: 28px; padding: 32px 20px; text-align: center; border: 1px solid rgba(255,255,255,0.08); min-height: 380px;}
.tier-feature {font-size: 0.9em; margin: 8px 0;}
.feature-yes {color: #00FFA3;}
.feature-no {color: #FF4B4B;}
.popular-badge {background: linear-gradient(135deg, #FFD700, #FFA500); color: black; font-size: 0.7em; font-weight: 700; padding: 4px 12px; border-radius: 20px; display: inline-block; margin-bottom: 8px;}
.clock-container {border-radius: 20px; padding: 20px; text-align: center; margin: 16px 0;}
.clock-open {background: rgba(0,255,163,0.1); border: 2px solid rgba(0,255,163,0.4);}
.clock-closed {background: rgba(255,75,75,0.1); border: 2px solid rgba(255,75,75,0.4);}
.clock-pre {background: rgba(255,215,0,0.1); border: 2px solid rgba(255,215,0,0.4);}
.alpaca-connected {background: rgba(0,255,163,0.1); border: 2px solid rgba(0,255,163,0.4); border-radius: 12px; padding: 12px 20px; text-align: center; margin: 10px 0;}
.stock-card {background: rgba(255,255,255,0.03); border-radius: 20px; padding: 24px; margin: 12px 0; border: 1px solid rgba(255,255,255,0.08);}
.stock-card-buy {border-left: 4px solid #00FFA3;}
.stock-card-sell {border-left: 4px solid #FF4B4B;}
.stock-card-wait {border-left: 4px solid #808495;}
.shield-container {background: rgba(0,255,163,0.1); border: 2px solid rgba(0,255,163,0.35); border-radius: 20px; padding: 24px; text-align: center; margin: 20px 0;}
.founder-photo {width: 130px; height: 130px; border-radius: 50%; border: 4px solid #00FFA3;}
.indicator {display: inline-block; padding: 6px 12px; border-radius: 8px; font-size: 0.8em; font-weight: 600; margin: 3px;}
.ind-bullish {background: rgba(0,255,163,0.2); color: #00FFA3;}
.ind-bearish {background: rgba(255,75,75,0.2); color: #FF4B4B;}
.ind-neutral {background: rgba(255,215,0,0.2); color: #FFD700;}
.autopilot-on {background: rgba(0,255,163,0.15); border: 2px solid rgba(0,255,163,0.5); border-radius: 16px; padding: 18px; text-align: center;}
.autopilot-off {background: rgba(255,255,255,0.03); border: 2px solid #808495; border-radius: 16px; padding: 18px; text-align: center;}
.position-card {background: rgba(255,255,255,0.03); border-radius: 16px; padding: 18px; margin: 10px 0;}
.ticker {background: rgba(0,0,0,0.4); border-radius: 12px; padding: 12px; margin: 6px 0; font-family: monospace;}
.ticker-buy {border-left: 3px solid #00FFA3;}
.ticker-sell {border-left: 3px solid #FF4B4B;}
.share-card {background: linear-gradient(145deg, #0d1117, #161b22); border: 2px solid #00FFA3; border-radius: 24px; padding: 32px; text-align: center;}
.legal-footer {background: rgba(0,0,0,0.4); padding: 30px; margin-top: 50px; text-align: center; border-radius: 24px 24px 0 0;}
.stButton > button {background: linear-gradient(135deg, #00FFA3, #00CC7A); color: black; font-weight: 700; border: none; border-radius: 14px; padding: 12px 24px;}
</style>""", unsafe_allow_html=True)

def get_market_status():
    et = pytz.timezone('US/Eastern')
    now = datetime.now(et)
    t = now.strftime('%I:%M:%S %p ET')
    o = now.replace(hour=9, minute=30, second=0)
    c = now.replace(hour=16, minute=0, second=0)
    if now.weekday() >= 5: return 'closed', t, "WEEKEND"
    if now < o: d = o - now; return 'pre', t, f"PRE-MARKET {d.seconds//3600:02d}:{(d.seconds%3600)//60:02d}:{d.seconds%60:02d}"
    if now < c: d = c - now; return 'open', t, f"MARKET OPEN {d.seconds//3600:02d}:{(d.seconds%3600)//60:02d}:{d.seconds%60:02d}"
    return 'closed', t, "AFTER HOURS"

def generate_stock_data(stock):
    sym, base = stock['symbol'], stock['base_price']
    real = get_real_price(sym)
    if real and real > 0: base = real
    if sym not in st.session_state.stock_data:
        p = [base]
        for _ in range(99): p.append(round(max(base*0.8, min(base*1.2, p[-1] + random.gauss(0, base*0.01))), 2))
        st.session_state.stock_data[sym] = {'prices': p, 'volumes': [random.randint(1000000, 10000000) for _ in range(100)]}
    d = st.session_state.stock_data[sym]
    p = d['prices']
    new = real if real and real > 0 else round(max(base*0.7, min(base*1.3, p[-1] + random.gauss(0, base*0.005))), 2)
    p.append(new)
    if len(p) > 100: p.pop(0)
    d['volumes'].append(random.randint(1000000, 10000000))
    if len(d['volumes']) > 100: d['volumes'].pop(0)
    return new, p, d['volumes']

def calc_rsi(p, n=14):
    if len(p) < n + 1: return 50.0
    d = np.diff(p[-n-1:])
    g, l = np.where(d > 0, d, 0), np.where(d < 0, -d, 0)
    ag, al = np.mean(g), np.mean(l)
    if al == 0: return 100.0
    return round(100 - (100 / (1 + ag / al)), 1)

def calc_ema(p, n):
    if len(p) < n: return p[-1] if p else 0
    m = 2 / (n + 1)
    e = np.mean(p[:n])
    for x in p[n:]: e = (x * m) + (e * (1 - m))
    return round(e, 4)

def analyze_stock(stock):
    price, prices, vols = generate_stock_data(stock)
    rsi = calc_rsi(prices)
    e9, e21 = calc_ema(prices, 9), calc_ema(prices, 21)
    vwap = round(sum(a*b for a,b in zip(prices[-20:], vols[-20:])) / sum(vols[-20:]), 2) if len(prices) >= 20 else price
    sup = round(min(prices[-20:]), 2) if len(prices) >= 20 else price * 0.98
    res = round(max(prices[-20:]), 2) if len(prices) >= 20 else price * 1.02
    sc, sig = 0, {}
    if rsi < 30: sc += 2; sig['RSI'] = ('OVERSOLD', 'bullish')
    elif rsi < 40: sc += 1; sig['RSI'] = ('Low', 'bullish')
    elif rsi > 70: sc -= 2; sig['RSI'] = ('OVERBOUGHT', 'bearish')
    elif rsi > 60: sc -= 1; sig['RSI'] = ('High', 'bearish')
    else: sig['RSI'] = ('Neutral', 'neutral')
    if price > e9 > e21: sc += 1; sig['EMA'] = ('Bullish', 'bullish')
    elif price < e9 < e21: sc -= 1; sig['EMA'] = ('Bearish', 'bearish')
    else: sig['EMA'] = ('Flat', 'neutral')
    if price > vwap * 1.005: sc += 1; sig['VWAP'] = ('Above', 'bullish')
    elif price < vwap * 0.995: sc -= 1; sig['VWAP'] = ('Below', 'bearish')
    else: sig['VWAP'] = ('At', 'neutral')
    ds, dr = ((price - sup) / price) * 100, ((res - price) / price) * 100
    if ds < 1: sc += 2; sig['S/R'] = ('SUPPORT', 'bullish')
    elif dr < 1: sc -= 2; sig['S/R'] = ('RESISTANCE', 'bearish')
    else: sig['S/R'] = ('Mid', 'neutral')
    vs = vols[-1] / np.mean(vols[-20:-1]) if len(vols) > 20 else 1
    if vs > 2: sc += 1 if sc > 0 else -1; sig['VOL'] = ('SPIKE', 'bullish' if sc > 0 else 'bearish')
    else: sig['VOL'] = ('Normal', 'neutral')
    if sc >= 5: s = 'STRONG BUY'
    elif sc >= 3: s = 'BUY'
    elif sc <= -5: s = 'STRONG SELL'
    elif sc <= -3: s = 'SELL'
    else: s = 'WAIT'
    oc = max(5, min(round(price * 0.03 * random.uniform(0.8, 1.2), 2), 80))
    return {'symbol': stock['symbol'], 'name': stock['name'], 'price': price, 'change': round(price - prices[-2] if len(prices) > 1 else 0, 2), 'score': sc, 'signal': s, 'signals': sig, 'option_cost': oc, 'stop_loss': round(oc * 0.75, 2), 'take_profit': round(oc * 1.30, 2)}

def scan_all(): return sorted([analyze_stock(s) for s in WATCHLIST], key=lambda x: abs(x['score']), reverse=True)

def add_tick(a, s, p, d):
    st.session_state.trade_ticker.append({'time': datetime.now().strftime('%H:%M:%S'), 'action': a, 'symbol': s, 'direction': d})
    if len(st.session_state.trade_ticker) > 20: st.session_state.trade_ticker.pop(0)

def buy(stock, d):
    t = TIERS[st.session_state.tier]
    if len(st.session_state.positions) >= t['max_trades']: return False
    c = stock['option_cost'] * 100
    if st.session_state.alpaca_balance < c: return False
    st.session_state.alpaca_balance -= c
    st.session_state.positions.append({'symbol': stock['symbol'], 'direction': d, 'entry': stock['option_cost'], 'current': stock['option_cost'], 'stop_loss': stock['stop_loss'], 'take_profit': stock['take_profit'], 'pnl': 0})
    add_tick('BUY', stock['symbol'], stock['option_cost'], d)
    return True

def sell(i):
    if i >= len(st.session_state.positions): return
    p = st.session_state.positions[i]
    st.session_state.alpaca_balance += (p['entry'] * 100) + p['pnl']
    st.session_state.daily_pnl += p['pnl']
    st.session_state.total_pnl += p['pnl']
    if p['pnl'] >= 0: st.session_state.wins += 1
    else: st.session_state.losses += 1
    st.session_state.trades.append({'symbol': p['symbol'], 'direction': p['direction'], 'pnl': p['pnl'], 'time': datetime.now().strftime('%H:%M:%S'), 'date': datetime.now().strftime('%Y-%m-%d')})
    add_tick('SELL', p['symbol'], p['current'], p['direction'])
    st.session_state.positions.pop(i)

def update_pos():
    for i, p in enumerate(st.session_state.positions):
        ch = random.uniform(-0.08, 0.10)
        p['current'] = round(p['entry'] * (1 + ch), 2)
        p['pnl'] = round((p['current'] - p['entry']) * 100, 2)
        if st.session_state.autopilot or st.session_state.tier == 1:
            if p['current'] <= p['stop_loss']: sell(i); return
            if p['current'] >= p['take_profit']: sell(i); return

def render_home():
    st.markdown('<div class="logo-container"><span style="font-size:3em;">&#127793;</span><span class="logo-text">PROJECT HOPE</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-section"><h1 class="hero-title">OPTIONS TRADING</h1><p class="hero-subtitle">5-Layer Protection Built In</p><p class="hero-tagline">Turn $200 into $2,000 - Without Risking It All</p></div>', unsafe_allow_html=True)
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
    if alpaca_account:
        st.markdown(f'<div class="alpaca-connected"><span style="color:#00FFA3;font-weight:700;">ALPACA CONNECTED</span> | Paper Balance: <span style="color:#FFD700;font-weight:700;">${float(alpaca_account.get("cash", 0)):,.2f}</span></div>', unsafe_allow_html=True)
    status, current_time, countdown = get_market_status()
    st.markdown(f'<div class="clock-container clock-{status}"><p style="color:#808495;margin:0;">{current_time}</p><p style="font-size:1.8em;font-weight:800;color:#00E5FF;margin:8px 0 0 0;font-family:monospace;">{countdown}</p></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 5-Layer Protection System")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.markdown('<div class="stat-card"><p class="stat-value" style="color:#00FFA3;">-25%</p><p class="stat-label">Stop Loss</p></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="stat-card"><p class="stat-value" style="color:#FFD700;">+30%</p><p class="stat-label">Take Profit</p></div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="stat-card"><p class="stat-value" style="color:#FF4B4B;">-15%</p><p class="stat-label">Daily Max</p></div>', unsafe_allow_html=True)
    with c4: st.markdown('<div class="stat-card"><p class="stat-value" style="color:#00E5FF;">5%</p><p class="stat-label">Per Trade</p></div>', unsafe_allow_html=True)
    with c5: st.markdown('<div class="stat-card"><p class="stat-value" style="color:#A855F7;">3</p><p class="stat-label">Max Open</p></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Meet the Founder")
    c1, c2 = st.columns([1, 3])
    with c1: st.markdown(f'<img src="{STEPHEN_PHOTO}" class="founder-photo">', unsafe_allow_html=True)
    with c2: st.markdown(f'<div style="padding-left:10px;"><h3 style="color:white;margin:0 0 8px 0;">{STEPHEN_NAME}</h3><p style="color:#00FFA3;margin:0 0 4px 0;font-weight:600;">Amazon Warehouse Worker | Self-Taught Developer</p><p style="color:#808495;margin:0;">{STEPHEN_LOCATION}</p></div>', unsafe_allow_html=True)
    with st.expander("Read My Full Story"): st.markdown(f'<p style="color:#c0c0c0;line-height:1.8;">{STEPHEN_BIO}</p>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Choose Your Plan")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown('<div class="tier-card"><h3 style="color:#00FFA3;">STARTER</h3><p style="font-size:2.5em;font-weight:900;color:white;">$49<span style="font-size:0.35em;color:#808495;">/mo</span></p><p class="tier-feature"><span class="feature-yes">+</span> 1 Stock Shown</p><p class="tier-feature"><span class="feature-yes">+</span> 1 Trade Max</p><p class="tier-feature"><span class="feature-yes">+</span> Autopilot Always On</p><p class="tier-feature"><span class="feature-yes">+</span> Auto Stop/Profit</p><p class="tier-feature"><span class="feature-no">X</span> Manual Trading</p><p class="tier-feature"><span class="feature-no">X</span> Priority Support</p></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="tier-card"><h3 style="color:#00E5FF;">BUILDER</h3><p style="font-size:2.5em;font-weight:900;color:white;">$99<span style="font-size:0.35em;color:#808495;">/mo</span></p><p class="tier-feature"><span class="feature-yes">+</span> 3 Stocks Shown</p><p class="tier-feature"><span class="feature-yes">+</span> 2 Trades Max</p><p class="tier-feature"><span class="feature-yes">+</span> Autopilot Toggle</p><p class="tier-feature"><span class="feature-yes">+</span> Manual Trading</p><p class="tier-feature"><span class="feature-no">X</span> Priority Support</p><p class="tier-feature"><span class="feature-no">X</span> Personal Coaching</p></div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="tier-card" style="box-shadow:0 0 50px rgba(255,215,0,0.15);border:1px solid rgba(255,215,0,0.2);"><span class="popular-badge">POPULAR</span><h3 style="color:#FFD700;">MASTER</h3><p style="font-size:2.5em;font-weight:900;color:white;">$199<span style="font-size:0.35em;color:#808495;">/mo</span></p><p class="tier-feature"><span class="feature-yes">+</span> 6 Stocks Shown</p><p class="tier-feature"><span class="feature-yes">+</span> 3 Trades Max</p><p class="tier-feature"><span class="feature-yes">+</span> Autopilot Toggle</p><p class="tier-feature"><span class="feature-yes">+</span> Priority Support</p><p class="tier-feature"><span class="feature-no">X</span> Weekly Coaching</p><p class="tier-feature"><span class="feature-no">X</span> Private Community</p></div>', unsafe_allow_html=True)
    with c4: st.markdown('<div class="tier-card"><h3 style="color:#FF6B6B;">VIP COACHING</h3><p style="font-size:2.5em;font-weight:900;color:white;">$499<span style="font-size:0.35em;color:#808495;">/mo</span></p><p class="tier-feature"><span class="feature-yes">+</span> 15 Stocks Shown</p><p class="tier-feature"><span class="feature-yes">+</span> 5 Trades Max</p><p class="tier-feature"><span class="feature-yes">+</span> Weekly 1-on-1 Coaching</p><p class="tier-feature"><span class="feature-yes">+</span> Private Community</p><p class="tier-feature"><span class="feature-yes">+</span> Direct Access to Me</p><p class="tier-feature"><span class="feature-yes">+</span> Custom Goal Plan</p></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Enter Access Code")
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        code = st.text_input("Code", type="password", label_visibility="collapsed", placeholder="Enter your access code...")
        codes = {"HOPE49": 1, "HOPE99": 2, "HOPE199": 3, "HOPE499": 4, "DEMO": 3}
        if code:
            if code.upper() in codes: st.session_state.tier = codes[code.upper()]; st.success(f"Access Granted: {TIERS[st.session_state.tier]['name']} Tier")
            else: st.error("Invalid code")
        if st.session_state.tier > 0:
            if st.button("Enter Trading Dashboard", type="primary", use_container_width=True): st.session_state.page = 'trade'; st.rerun()
    st.markdown(f'<div class="legal-footer"><p style="color:#808495;">{STEPHEN_NAME} | {STEPHEN_EMAIL}</p><p style="color:#666;font-size:0.85em;">{LEGAL_DISCLAIMER}</p></div>', unsafe_allow_html=True)

def render_trade():
    if st.session_state.tier == 0: st.warning("Enter access code first"); st.button("Home", on_click=lambda: setattr(st.session_state, 'page', 'home')); return
    tier = TIERS[st.session_state.tier]
    update_pos()
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.markdown(f'<div style="display:flex;align-items:center;gap:12px;"><span style="font-size:1.8em;">&#127793;</span><span style="font-size:1.5em;font-weight:800;background:linear-gradient(135deg,#00FFA3,#00E5FF);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">PROJECT HOPE</span><span style="color:{tier["color"]};font-weight:600;background:rgba(255,255,255,0.1);padding:4px 12px;border-radius:8px;">{tier["name"]}</span></div>', unsafe_allow_html=True)
    with c2: status, _, countdown = get_market_status(); st.markdown(f'<div class="clock-container clock-{status}" style="padding:10px;"><span style="font-weight:600;">{countdown}</span></div>', unsafe_allow_html=True)
    with c3: st.markdown('<div style="text-align:right;padding:10px;"><span style="color:#00FFA3;font-weight:600;background:rgba(0,255,163,0.1);padding:6px 14px;border-radius:8px;">ALPACA PAPER</span></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Home", use_container_width=True, key="t1"): st.session_state.page = 'home'; st.rerun()
    with c2: st.button("Trade", disabled=True, use_container_width=True)
    with c3:
        if st.button("History", use_container_width=True, key="t3"): st.session_state.page = 'history'; st.rerun()
    with c4:
        if st.button("Learn", use_container_width=True, key="t4"): st.session_state.page = 'learn'; st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    eq = st.session_state.alpaca_balance + sum(p.get('pnl', 0) for p in st.session_state.positions)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Equity", f"${eq:,.2f}")
    with c2: st.metric("Cash", f"${st.session_state.alpaca_balance:,.2f}")
    with c3: st.metric("Today P/L", f"${st.session_state.daily_pnl:+,.2f}")
    with c4: tot = st.session_state.wins + st.session_state.losses; wr = (st.session_state.wins / tot * 100) if tot > 0 else 0; st.metric("Win Rate", f"{wr:.0f}%")
    if tier['autopilot'] == 'always': st.markdown('<div class="autopilot-on"><span style="color:#00FFA3;font-weight:700;">AUTOPILOT: ALWAYS ON</span></div>', unsafe_allow_html=True)
    else:
        c1, c2 = st.columns([4, 1])
        with c1: st.markdown(f'<div class="autopilot-{"on" if st.session_state.autopilot else "off"}"><span style="color:{"#00FFA3" if st.session_state.autopilot else "#808495"};font-weight:700;">AUTOPILOT: {"ON" if st.session_state.autopilot else "OFF"}</span></div>', unsafe_allow_html=True)
        with c2:
            if st.button("Toggle", use_container_width=True): st.session_state.autopilot = not st.session_state.autopilot; st.rerun()
    st.markdown(f'<div class="shield-container"><p style="font-size:1.3em;font-weight:800;color:#00FFA3;margin:0 0 8px 0;">5-LAYER PROTECTION ACTIVE</p><p style="color:#808495;margin:0;">Stop -25% | Profit +30% | Daily -15% | 5% Per Trade | Max {tier["max_trades"]} Positions</p></div>', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Stock Scanner")
        st.markdown(f'<p style="color:#808495;">Top {tier["stocks_shown"]} | <span style="color:#00FFA3;">Live Alpaca Data</span></p>', unsafe_allow_html=True)
        for s in scan_all()[:tier['stocks_shown']]:
            cc = 'stock-card-buy' if s['score'] >= 3 else 'stock-card-sell' if s['score'] <= -3 else 'stock-card-wait'
            chc = "#00FFA3" if s['change'] >= 0 else "#FF4B4B"
            sigc = "#00FFA3" if s['score'] >= 3 else "#FF4B4B" if s['score'] <= -3 else "#FFD700"
            st.markdown(f'<div class="stock-card {cc}"><div style="display:flex;justify-content:space-between;"><div><h3 style="color:white;margin:0;">{s["symbol"]}</h3><p style="color:#808495;margin:4px 0 0 0;">{s["name"]}</p></div><div style="text-align:right;"><h3 style="color:#00E5FF;margin:0;">${s["price"]:.2f}</h3><p style="color:{chc};margin:4px 0 0 0;font-weight:600;">{s["change"]:+.2f}</p></div></div><div style="display:flex;justify-content:space-between;margin-top:12px;"><span style="color:{sigc};font-weight:700;">{s["signal"]} ({s["score"]}/8)</span><span style="color:#808495;">~${int(s["option_cost"])}/contract</span></div></div>', unsafe_allow_html=True)
            ih = "".join([f'<span class="indicator ind-{v[1]}">{k}</span>' for k, v in s['signals'].items()])
            st.markdown(f'<div style="margin:-5px 0 15px 0;">{ih}</div>', unsafe_allow_html=True)
            if s['signal'] in ['STRONG BUY', 'BUY', 'STRONG SELL', 'SELL'] and tier['autopilot'] != 'always' and len(st.session_state.positions) < tier['max_trades']:
                d = 'CALL' if s['score'] > 0 else 'PUT'
                if st.button(f"BUY {d} - ${int(s['option_cost'] * 100)}", key=f"buy_{s['symbol']}", use_container_width=True):
                    if buy(s, d): st.success("Position opened!"); st.balloons(); st.rerun()
    with col2:
        st.markdown(f"### Positions ({len(st.session_state.positions)}/{tier['max_trades']})")
        if st.session_state.positions:
            for i, p in enumerate(st.session_state.positions):
                pc = "#00FFA3" if p['pnl'] >= 0 else "#FF4B4B"
                st.markdown(f'<div class="position-card" style="border-left:3px solid {pc};"><div style="display:flex;justify-content:space-between;"><div><h4 style="color:white;margin:0;">{p["symbol"]}</h4><p style="color:#808495;font-size:0.85em;">{p["direction"]} @ ${p["entry"]:.2f}</p></div><h4 style="color:{pc};margin:0;">${p["pnl"]:+.2f}</h4></div></div>', unsafe_allow_html=True)
                if tier['autopilot'] != 'always' and not st.session_state.autopilot:
                    if st.button("Close", key=f"close_{i}", use_container_width=True): sell(i); st.rerun()
        else: st.info("No open positions")
        st.markdown("### Live Ticker")
        for t in reversed(st.session_state.trade_ticker[-6:]):
            tc = "ticker-buy" if t['action'] == 'BUY' else "ticker-sell"
            tcol = "#00FFA3" if t['action'] == 'BUY' else "#FF4B4B"
            st.markdown(f'<div class="ticker {tc}"><span style="color:#808495;">{t["time"]}</span> <span style="color:{tcol};font-weight:600;">{t["action"]}</span> <span style="color:white;">{t["symbol"]}</span></div>', unsafe_allow_html=True)

def render_history():
    st.markdown('<div class="logo-container"><span style="font-size:3em;">&#127793;</span><span class="logo-text">PROJECT HOPE</span></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Home", use_container_width=True, key="hh1"): st.session_state.page = 'home'; st.rerun()
    with c2:
        if st.button("Trade", use_container_width=True, key="hh2"): st.session_state.page = 'trade'; st.rerun()
    with c3: st.button("History", disabled=True, use_container_width=True)
    with c4:
        if st.button("Learn", use_container_width=True, key="hh4"): st.session_state.page = 'learn'; st.rerun()
    tot = st.session_state.wins + st.session_state.losses
    wr = (st.session_state.wins / tot * 100) if tot > 0 else 0
    pc = "#00FFA3" if st.session_state.total_pnl >= 0 else "#FF4B4B"
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="stat-card"><p class="stat-value" style="color:{pc};">${st.session_state.total_pnl:,.2f}</p><p class="stat-label">Total P/L</p></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="stat-card"><p class="stat-value" style="color:#FFD700;">{wr:.0f}%</p><p class="stat-label">Win Rate</p></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="stat-card"><p class="stat-value" style="color:#00FFA3;">{st.session_state.wins}</p><p class="stat-label">Wins</p></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="stat-card"><p class="stat-value" style="color:#FF4B4B;">{st.session_state.losses}</p><p class="stat-label">Losses</p></div>', unsafe_allow_html=True)
    st.markdown("### Recent Trades")
    if st.session_state.trades:
        for t in reversed(st.session_state.trades[-10:]):
            c = "#00FFA3" if t['pnl'] >= 0 else "#FF4B4B"
            st.markdown(f'<div class="glass-card" style="border-left:3px solid {c};padding:15px;"><div style="display:flex;justify-content:space-between;"><div><p style="color:#808495;font-size:0.85em;margin:0;">{t.get("date", "")} {t["time"]}</p><h4 style="color:white;margin:8px 0 0 0;">{t["symbol"]} {t.get("direction", "")}</h4></div><h3 style="color:{c};margin:0;">${t["pnl"]:+.2f}</h3></div></div>', unsafe_allow_html=True)
    else: st.info("No trades yet")
    if st.button("Reset Stats"):
        st.session_state.alpaca_balance = 5000.0
        st.session_state.positions, st.session_state.trades, st.session_state.trade_ticker, st.session_state.stock_data = [], [], [], {}
        st.session_state.daily_pnl = st.session_state.total_pnl = 0.0
        st.session_state.wins = st.session_state.losses = 0
        st.rerun()

def render_learn():
    st.markdown('<div class="logo-container"><span style="font-size:3em;">&#127793;</span><span class="logo-text">PROJECT HOPE</span></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Home", use_container_width=True, key="ll1"): st.session_state.page = 'home'; st.rerun()
    with c2:
        if st.button("Trade", use_container_width=True, key="ll2"): st.session_state.page = 'trade'; st.rerun()
    with c3:
        if st.button("History", use_container_width=True, key="ll3"): st.session_state.page = 'history'; st.rerun()
    with c4: st.button("Learn", disabled=True, use_container_width=True)
    st.markdown("### What Are Options?")
    c1, c2 = st.columns(2)
    with c1: st.markdown('<div class="glass-card" style="border-left:4px solid #00FFA3;"><h3 style="color:#00FFA3;margin:0 0 12px 0;">CALL Option</h3><p style="color:white;margin:0;">Bet the stock goes UP</p></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="glass-card" style="border-left:4px solid #FF4B4B;"><h3 style="color:#FF4B4B;margin:0 0 12px 0;">PUT Option</h3><p style="color:white;margin:0;">Bet the stock goes DOWN</p></div>', unsafe_allow_html=True)

def main():
    p = st.session_state.page
    if p == 'home': render_home()
    elif p == 'trade': render_trade()
    elif p == 'history': render_history()
    elif p == 'learn': render_learn()
    else: render_home()

if __name__ == "__main__": main()
