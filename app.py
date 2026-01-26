# PROJECT HOPE v4.3 - BULLETPROOF EDITION
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import random
from datetime import datetime, timedelta
import numpy as np
import pytz
import requests

st.set_page_config(page_title="Project Hope", page_icon="🌱", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=5000, key="refresh")

ALPACA_KEY = "PKQJEFSQBY2CFDYYHDR372QB3S"
ALPACA_SECRET = "ArMPEE3fqY1JCB5CArZUQ5wY8fYQjuPXJ9qpnwYPHJuw"
ALPACA_URL = "https://paper-api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"

PHOTO = "https://i.postimg.cc/qvVSgvfx/IMG-7642.jpg"
NAME = "Stephen Martinez"
LOCATION = "Lancaster, PA"
EMAIL = "thetradingprotocol@gmail.com"

STOP_LOSS = 0.25
TAKE_PROFIT = 0.30
DAILY_LIMIT = 0.15
MAX_POS = 0.05
MIN_SCORE = 3

RED = ['bankruptcy','fraud','sec investigation','lawsuit','downgrade','misses estimates','ceo resigns','delisting','layoffs','fda rejection','criminal']
GREEN = ['beats estimates','upgrade','fda approval','partnership','acquisition','buyback','record revenue','breakthrough','contract win']

TIERS = {1:{"name":"STARTER","stocks":1,"trades":1,"color":"#00FFA3","auto":"always"},2:{"name":"BUILDER","stocks":3,"trades":2,"color":"#00E5FF","auto":"toggle"},3:{"name":"MASTER","stocks":6,"trades":3,"color":"#FFD700","auto":"toggle"},4:{"name":"VIP","stocks":15,"trades":5,"color":"#FF6B6B","auto":"toggle"}}

STOCKS = [{"s":"SOFI","n":"SoFi Technologies","p":14.50},{"s":"PLTR","n":"Palantir","p":78.00},{"s":"NIO","n":"NIO Inc","p":4.85},{"s":"RIVN","n":"Rivian","p":12.30},{"s":"HOOD","n":"Robinhood","p":24.50},{"s":"SNAP","n":"Snapchat","p":11.20},{"s":"COIN","n":"Coinbase","p":265.00},{"s":"MARA","n":"Marathon Digital","p":18.75},{"s":"RIOT","n":"Riot Platforms","p":12.40},{"s":"LCID","n":"Lucid Motors","p":2.80},{"s":"F","n":"Ford","p":10.25},{"s":"AAL","n":"American Airlines","p":17.80},{"s":"PLUG","n":"Plug Power","p":2.15},{"s":"BB","n":"BlackBerry","p":2.45},{"s":"AMC","n":"AMC Entertainment","p":3.20}]

BIO = "I'm Stephen Martinez, an Amazon warehouse worker from Lancaster, PA. I watched coworkers lose savings on trading apps designed to make them trade MORE, not SMARTER. So I taught myself to code. Project Hope PROTECTS you first - stops you from blowing up your account. This isn't about getting rich quick. It's about building something real, one smart trade at a time."

def headers():
    return {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}

def get_acct():
    try:
        r = requests.get(f"{ALPACA_URL}/v2/account", headers=headers(), timeout=5)
        if r.status_code == 200: return r.json()
    except: pass
    return None

def get_price(sym):
    try:
        r = requests.get(f"{DATA_URL}/v2/stocks/{sym}/quotes/latest", headers=headers(), timeout=3)
        if r.status_code == 200:
            d = r.json()
            if 'quote' in d: return float(d['quote'].get('ap',0) or d['quote'].get('bp',0))
    except: pass
    return None

def get_news(sym):
    try:
        end = datetime.now()
        start = end - timedelta(days=1)
        r = requests.get(f"{DATA_URL}/v1beta1/news", headers=headers(), params={'symbols':sym,'start':start.strftime('%Y-%m-%dT%H:%M:%SZ'),'end':end.strftime('%Y-%m-%dT%H:%M:%SZ'),'limit':10}, timeout=5)
        if r.status_code == 200: return r.json().get('news',[])
    except: pass
    return []

def check_news(news):
    if not news: return {'sent':'NEUTRAL','red':[],'green':[],'block':False}
    red,green = [],[]
    for i in news:
        txt = (i.get('headline','') + ' ' + i.get('summary','')).lower()
        for w in RED:
            if w in txt and w not in red: red.append(w)
        for w in GREEN:
            if w in txt and w not in green: green.append(w)
    if len(red) >= 2: sent = 'DANGER'
    elif len(red) == 1: sent = 'CAUTION'
    elif len(green) >= 2: sent = 'BULLISH'
    elif len(green) == 1: sent = 'POSITIVE'
    else: sent = 'NEUTRAL'
    return {'sent':sent,'red':red,'green':green,'block':len(red)>=2}

defs = {'page':'home','tier':0,'pos':[],'trades':[],'daily':0.0,'total':0.0,'wins':0,'losses':0,'data':{},'auto':True,'ticker':[],'bal':5000.0,'start':5000.0,'locked':False,'date':datetime.now().strftime('%Y-%m-%d'),'nc':{}}
for k,v in defs.items():
    if k not in st.session_state: st.session_state[k] = v

if st.session_state.date != datetime.now().strftime('%Y-%m-%d'):
    st.session_state.daily = 0.0
    st.session_state.locked = False
    st.session_state.date = datetime.now().strftime('%Y-%m-%d')

acct = get_acct()
if acct:
    st.session_state.bal = float(acct.get('cash',5000))
    if st.session_state.start == 5000.0: st.session_state.start = st.session_state.bal

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
.shld{background:rgba(0,255,163,0.1);border:2px solid rgba(0,255,163,0.35);border-radius:14px;padding:14px;text-align:center;margin:12px 0}
.nb{background:rgba(255,0,0,0.15);border:1px solid rgba(255,0,0,0.4);border-radius:6px;padding:6px 10px;margin:5px 0;font-size:0.85em}
.nw{background:rgba(255,165,0,0.15);border:1px solid rgba(255,165,0,0.4);border-radius:6px;padding:6px 10px;margin:5px 0;font-size:0.85em}
.ng{background:rgba(0,255,163,0.15);border:1px solid rgba(0,255,163,0.4);border-radius:6px;padding:6px 10px;margin:5px 0;font-size:0.85em}
.ph{width:80px;height:80px;border-radius:50%;border:3px solid #00FFA3}
.ind{display:inline-block;padding:3px 7px;border-radius:5px;font-size:0.7em;font-weight:600;margin:2px}
.ind.bu{background:rgba(0,255,163,0.2);color:#00FFA3}.ind.be{background:rgba(255,75,75,0.2);color:#FF4B4B}.ind.ne{background:rgba(255,215,0,0.2);color:#FFD700}
.aon{background:rgba(0,255,163,0.15);border:2px solid rgba(0,255,163,0.5);border-radius:12px;padding:10px;text-align:center}
.aoff{background:rgba(255,255,255,0.03);border:2px solid #808495;border-radius:12px;padding:10px;text-align:center}
.lck{background:rgba(255,0,0,0.2);border:2px solid rgba(255,0,0,0.5);border-radius:12px;padding:10px;text-align:center}
.pcard{background:rgba(255,255,255,0.03);border-radius:12px;padding:10px;margin:6px 0}
.tck{background:rgba(0,0,0,0.4);border-radius:8px;padding:6px;margin:3px 0;font-family:monospace;font-size:0.7em}
.tck.b{border-left:3px solid #00FFA3}.tck.s{border-left:3px solid #FF4B4B}
.ft{background:rgba(0,0,0,0.4);padding:18px;margin-top:25px;text-align:center;border-radius:18px 18px 0 0}
.stButton>button{background:linear-gradient(135deg,#00FFA3,#00CC7A);color:black;font-weight:700;border:none;border-radius:10px;padding:8px 16px}
</style>""", unsafe_allow_html=True)

def mkt():
    et = pytz.timezone('US/Eastern')
    now = datetime.now(et)
    t = now.strftime('%I:%M:%S %p ET')
    o,c = now.replace(hour=9,minute=30,second=0), now.replace(hour=16,minute=0,second=0)
    if now.weekday() >= 5: return 'closed',t,"WEEKEND",False
    if now < o: d=o-now; return 'pre',t,f"PRE {d.seconds//3600:02d}:{(d.seconds%3600)//60:02d}:{d.seconds%60:02d}",False
    if now < c: d=c-now; return 'open',t,f"OPEN {d.seconds//3600:02d}:{(d.seconds%3600)//60:02d}:{d.seconds%60:02d}",True
    return 'closed',t,"CLOSED",False

def hit_limit():
    if st.session_state.daily <= -(st.session_state.start * DAILY_LIMIT): st.session_state.locked = True
    return st.session_state.locked

def gen(stk):
    sym,b = stk['s'],stk['p']
    real = get_price(sym)
    if real and real > 0: b = real
    if sym not in st.session_state.data:
        p = [b]
        for _ in range(99): p.append(round(max(b*0.8,min(b*1.2,p[-1]+random.gauss(0,b*0.01))),2))
        st.session_state.data[sym] = {'p':p,'v':[random.randint(1000000,10000000) for _ in range(100)]}
    d = st.session_state.data[sym]
    p = d['p']
    new = real if real and real > 0 else round(max(b*0.7,min(b*1.3,p[-1]+random.gauss(0,b*0.005))),2)
    p.append(new)
    if len(p) > 100: p.pop(0)
    d['v'].append(random.randint(1000000,10000000))
    if len(d['v']) > 100: d['v'].pop(0)
    return new,p,d['v']

def rsi(p,n=14):
    if len(p)<n+1: return 50.0
    d = np.diff(p[-n-1:])
    g,l = np.where(d>0,d,0),np.where(d<0,-d,0)
    ag,al = np.mean(g),np.mean(l)
    return 100.0 if al==0 else round(100-(100/(1+ag/al)),1)

def ema(p,n):
    if len(p)<n: return p[-1] if p else 0
    m,e = 2/(n+1),np.mean(p[:n])
    for x in p[n:]: e = (x*m)+(e*(1-m))
    return round(e,4)

def cnews(sym):
    k = f"{sym}_{datetime.now().strftime('%Y%m%d%H')}"
    if k in st.session_state.nc: return st.session_state.nc[k]
    n = check_news(get_news(sym))
    st.session_state.nc[k] = n
    return n

def analyze(stk):
    pr,ps,vs = gen(stk)
    r = rsi(ps)
    e9,e21 = ema(ps,9),ema(ps,21)
    vwap = round(sum(a*b for a,b in zip(ps[-20:],vs[-20:]))/sum(vs[-20:]),2) if len(ps)>=20 else pr
    sup,res = (round(min(ps[-20:]),2),round(max(ps[-20:]),2)) if len(ps)>=20 else (pr*0.98,pr*1.02)
    sc,sig = 0,{}
    if r<30: sc+=2; sig['RSI']=('OVERSOLD','bu')
    elif r<40: sc+=1; sig['RSI']=('Low','bu')
    elif r>70: sc-=2; sig['RSI']=('OVERBOUGHT','be')
    elif r>60: sc-=1; sig['RSI']=('High','be')
    else: sig['RSI']=('Neutral','ne')
    if pr>e9>e21: sc+=1; sig['EMA']=('Bull','bu')
    elif pr<e9<e21: sc-=1; sig['EMA']=('Bear','be')
    else: sig['EMA']=('Flat','ne')
    if pr>vwap*1.005: sc+=1; sig['VWAP']=('Above','bu')
    elif pr<vwap*0.995: sc-=1; sig['VWAP']=('Below','be')
    else: sig['VWAP']=('At','ne')
    ds,dr = ((pr-sup)/pr)*100,((res-pr)/pr)*100
    if ds<1: sc+=2; sig['S/R']=('SUPPORT','bu')
    elif dr<1: sc-=2; sig['S/R']=('RESIST','be')
    else: sig['S/R']=('Mid','ne')
    vs_r = vs[-1]/np.mean(vs[-20:-1]) if len(vs)>20 else 1
    if vs_r>2: sc+=1 if sc>0 else -1; sig['VOL']=('SPIKE','bu' if sc>0 else 'be')
    else: sig['VOL']=('Normal','ne')
    nws = cnews(stk['s'])
    blk = False
    if nws['sent']=='DANGER': sc-=5; blk=True; sig['NEWS']=('DANGER','be')
    elif nws['sent']=='CAUTION': sc-=2; sig['NEWS']=('CAUTION','be')
    elif nws['sent']=='BULLISH': sc+=2; sig['NEWS']=('BULLISH','bu')
    elif nws['sent']=='POSITIVE': sc+=1; sig['NEWS']=('GOOD','bu')
    else: sig['NEWS']=('OK','ne')
    if blk: signal = 'BLOCKED'
    elif sc>=5: signal = 'STRONG BUY'
    elif sc>=MIN_SCORE: signal = 'BUY'
    elif sc<=-5: signal = 'STRONG SELL'
    elif sc<=-MIN_SCORE: signal = 'SELL'
    else: signal = 'WAIT'
    mx = (st.session_state.bal*MAX_POS)/100
    oc = min(max(5,round(pr*0.03*random.uniform(0.8,1.2),2)),mx,80)
    return {'sym':stk['s'],'name':stk['n'],'pr':pr,'chg':round(pr-ps[-2] if len(ps)>1 else 0,2),'sc':sc,'sig':signal,'sigs':sig,'oc':oc,'sl':round(oc*(1-STOP_LOSS),2),'tp':round(oc*(1+TAKE_PROFIT),2),'news':nws,'blk':blk}

def scan():
    return sorted([analyze(s) for s in STOCKS], key=lambda x:abs(x['sc']), reverse=True)

def tick(a,sym,d):
    st.session_state.ticker.append({'t':datetime.now().strftime('%H:%M:%S'),'a':a,'s':sym,'d':d})
    if len(st.session_state.ticker)>15: st.session_state.ticker.pop(0)

def can_buy(stk):
    tier = TIERS[st.session_state.tier]
    if stk.get('blk'): return False,"News blocked"
    if hit_limit(): return False,"Daily limit"
    if len(st.session_state.pos)>=tier['trades']: return False,"Max positions"
    if st.session_state.bal<stk['oc']*100: return False,"No balance"
    _,_,_,op = mkt()
    if not op: return False,"Market closed"
    if abs(stk['sc'])<MIN_SCORE: return False,f"Score < {MIN_SCORE}"
    return True,"OK"

def buy(stk,d):
    ok,_ = can_buy(stk)
    if not ok: return False
    st.session_state.bal -= stk['oc']*100
    st.session_state.pos.append({'sym':stk['sym'],'dir':d,'entry':stk['oc'],'cur':stk['oc'],'sl':stk['sl'],'tp':stk['tp'],'pnl':0})
    tick('BUY',stk['sym'],d)
    return True

def sell(i):
    if i>=len(st.session_state.pos): return
    p = st.session_state.pos[i]
    st.session_state.bal += (p['entry']*100)+p['pnl']
    st.session_state.daily += p['pnl']
    st.session_state.total += p['pnl']
    if p['pnl']>=0: st.session_state.wins+=1
    else: st.session_state.losses+=1
    st.session_state.trades.append({'sym':p['sym'],'dir':p['dir'],'pnl':p['pnl'],'t':datetime.now().strftime('%H:%M:%S'),'d':datetime.now().strftime('%Y-%m-%d')})
    tick('SELL',p['sym'],p['dir'])
    st.session_state.pos.pop(i)

def update():
    for i,p in enumerate(st.session_state.pos):
        ch = random.uniform(-0.08,0.10)
        p['cur'] = round(p['entry']*(1+ch),2)
        p['pnl'] = round((p['cur']-p['entry'])*100,2)
        if st.session_state.auto or st.session_state.tier==1:
            if p['cur']<=p['sl']: sell(i); return
            if p['cur']>=p['tp']: sell(i); return

def auto_trade(stks):
    if not st.session_state.auto and st.session_state.tier!=1: return
    tier = TIERS[st.session_state.tier]
    _,_,_,op = mkt()
    if not op or hit_limit() or len(st.session_state.pos)>=tier['trades']: return
    for stk in stks[:tier['stocks']]:
        if len(st.session_state.pos)>=tier['trades']: break
        if stk['sig'] in ['STRONG BUY','BUY']:
            if buy(stk,'CALL'): st.balloons(); break
        elif stk['sig'] in ['STRONG SELL','SELL']:
            if buy(stk,'PUT'): st.balloons(); break

def home():
    st.markdown('<div class="logo"><span>🌱</span><span>PROJECT HOPE</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="hero"><h1>OPTIONS TRADING</h1><p class="sub">5-Layer Protection Built In</p><p class="tag">Turn $200 into $2,000 - Without Risking It All</p></div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.button("Home",disabled=True,use_container_width=True)
    with c2:
        if st.button("Trade",use_container_width=True,key="h1"):
            if st.session_state.tier>0: st.session_state.page='trade'; st.rerun()
            else: st.warning("Enter code first!")
    with c3:
        if st.button("History",use_container_width=True,key="h2"): st.session_state.page='history'; st.rerun()
    with c4:
        if st.button("Learn",use_container_width=True,key="h3"): st.session_state.page='learn'; st.rerun()
    if acct: st.markdown(f'<div class="conn"><span style="color:#00FFA3;font-weight:700;">✓ ALPACA</span> | <span style="color:#FFD700;font-weight:700;">${st.session_state.bal:,.2f}</span></div>', unsafe_allow_html=True)
    status,ct,cd,_ = mkt()
    st.markdown(f'<div class="clk {status}"><p style="color:#808495;margin:0;font-size:0.85em;">{ct}</p><p style="font-size:1.3em;font-weight:800;color:#00E5FF;margin:6px 0 0;font-family:monospace;">{cd}</p></div>', unsafe_allow_html=True)
    st.markdown("### 🛡️ 5-Layer Protection")
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.markdown('<div class="card stat"><p class="v" style="color:#00FFA3;">-25%</p><p class="l">Stop</p></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="card stat"><p class="v" style="color:#FFD700;">+30%</p><p class="l">Profit</p></div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="card stat"><p class="v" style="color:#FF4B4B;">-15%</p><p class="l">Daily</p></div>', unsafe_allow_html=True)
    with c4: st.markdown('<div class="card stat"><p class="v" style="color:#00E5FF;">5%</p><p class="l">Max</p></div>', unsafe_allow_html=True)
    with c5: st.markdown('<div class="card stat"><p class="v" style="color:#A855F7;">📰</p><p class="l">News</p></div>', unsafe_allow_html=True)
    st.markdown("### 👨‍💻 Founder")
    c1,c2 = st.columns([1,3])
    with c1: st.markdown(f'<img src="{PHOTO}" class="ph">', unsafe_allow_html=True)
    with c2: st.markdown(f'<div><h4 style="color:white;margin:0;">{NAME}</h4><p style="color:#00FFA3;margin:2px 0;font-size:0.9em;">Amazon Worker | Self-Taught Dev</p><p style="color:#808495;margin:0;font-size:0.85em;">{LOCATION}</p></div>', unsafe_allow_html=True)
    with st.expander("My Story"): st.write(BIO)
    st.markdown("### 💎 Plans")
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown('<div class="tier"><h3 style="color:#00FFA3;">STARTER</h3><p class="pr">$49<span style="font-size:0.4em;color:#808495;">/mo</span></p><p class="f"><span class="yes">✓</span> 1 Stock</p><p class="f"><span class="yes">✓</span> 1 Trade</p><p class="f"><span class="yes">✓</span> Auto Always</p><p class="f"><span class="yes">✓</span> News Filter</p><p class="f"><span class="no">✗</span> Manual</p></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="tier"><h3 style="color:#00E5FF;">BUILDER</h3><p class="pr">$99<span style="font-size:0.4em;color:#808495;">/mo</span></p><p class="f"><span class="yes">✓</span> 3 Stocks</p><p class="f"><span class="yes">✓</span> 2 Trades</p><p class="f"><span class="yes">✓</span> Auto Toggle</p><p class="f"><span class="yes">✓</span> News Filter</p><p class="f"><span class="no">✗</span> Coaching</p></div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="tier" style="box-shadow:0 0 30px rgba(255,215,0,0.15);border:1px solid rgba(255,215,0,0.2);"><span class="badge">POPULAR</span><h3 style="color:#FFD700;">MASTER</h3><p class="pr">$199<span style="font-size:0.4em;color:#808495;">/mo</span></p><p class="f"><span class="yes">✓</span> 6 Stocks</p><p class="f"><span class="yes">✓</span> 3 Trades</p><p class="f"><span class="yes">✓</span> Auto Toggle</p><p class="f"><span class="yes">✓</span> Priority</p></div>', unsafe_allow_html=True)
    with c4: st.markdown('<div class="tier"><h3 style="color:#FF6B6B;">VIP</h3><p class="pr">$499<span style="font-size:0.4em;color:#808495;">/mo</span></p><p class="f"><span class="yes">✓</span> 15 Stocks</p><p class="f"><span class="yes">✓</span> 5 Trades</p><p class="f"><span class="yes">✓</span> 1-on-1 Coach</p><p class="f"><span class="yes">✓</span> Community</p></div>', unsafe_allow_html=True)
    st.markdown("### 🔐 Access Code")
    _,c2,_ = st.columns([1,2,1])
    with c2:
        code = st.text_input("Code",type="password",label_visibility="collapsed",placeholder="Enter code...")
        codes = {"HOPE49":1,"HOPE99":2,"HOPE199":3,"HOPE499":4,"DEMO":3}
        if code:
            if code.upper() in codes: st.session_state.tier=codes[code.upper()]; st.success(f"✓ {TIERS[st.session_state.tier]['name']}")
            else: st.error("Invalid")
        if st.session_state.tier>0:
            if st.button("🚀 Start Trading",type="primary",use_container_width=True): st.session_state.page='trade'; st.rerun()
    st.markdown(f'<div class="ft"><p style="color:#808495;font-size:0.85em;margin:0;">{NAME} | {EMAIL}</p><p style="color:#666;font-size:0.75em;margin:8px 0 0;">Not financial advice. Educational only.</p></div>', unsafe_allow_html=True)

def trade():
    if st.session_state.tier==0: st.warning("Enter code first"); return
    tier = TIERS[st.session_state.tier]
    update()
    stks = scan()
    auto_trade(stks)
    c1,c2 = st.columns([2,1])
    with c1: st.markdown(f'<div style="display:flex;align-items:center;gap:8px;"><span style="font-size:1.3em;">🌱</span><span style="font-size:1.2em;font-weight:800;background:linear-gradient(135deg,#00FFA3,#00E5FF);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">PROJECT HOPE</span><span style="color:{tier["color"]};font-weight:600;background:rgba(255,255,255,0.1);padding:3px 8px;border-radius:6px;font-size:0.8em;">{tier["name"]}</span></div>', unsafe_allow_html=True)
    with c2:
        status,_,cd,_ = mkt()
        st.markdown(f'<div class="clk {status}" style="padding:6px;"><span style="font-size:0.8em;font-weight:600;">{cd}</span></div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        if st.button("Home",use_container_width=True,key="t1"): st.session_state.page='home'; st.rerun()
    with c2: st.button("Trade",disabled=True,use_container_width=True)
    with c3:
        if st.button("History",use_container_width=True,key="t3"): st.session_state.page='history'; st.rerun()
    with c4:
        if st.button("Learn",use_container_width=True,key="t4"): st.session_state.page='learn'; st.rerun()
    eq = st.session_state.bal + sum(p.get('pnl',0) for p in st.session_state.pos)
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("Equity",f"${eq:,.2f}")
    with c2: st.metric("Cash",f"${st.session_state.bal:,.2f}")
    with c3: st.metric("Today",f"${st.session_state.daily:+,.2f}")
    with c4: tot=st.session_state.wins+st.session_state.losses; wr=(st.session_state.wins/tot*100) if tot>0 else 0; st.metric("Win%",f"{wr:.0f}%")
    if hit_limit(): st.markdown('<div class="lck"><span style="color:#FF4B4B;font-weight:700;">🔒 DAILY LIMIT - Trading locked</span></div>', unsafe_allow_html=True)
    elif tier['auto']=='always': st.markdown('<div class="aon"><span style="color:#00FFA3;font-weight:700;">🤖 AUTOPILOT ALWAYS ON</span></div>', unsafe_allow_html=True)
    else:
        c1,c2 = st.columns([4,1])
        with c1: st.markdown(f'<div class="{"aon" if st.session_state.auto else "aoff"}"><span style="color:{"#00FFA3" if st.session_state.auto else "#808495"};font-weight:700;">🤖 AUTO: {"ON" if st.session_state.auto else "OFF"}</span></div>', unsafe_allow_html=True)
        with c2:
            if st.button("Toggle",use_container_width=True): st.session_state.auto=not st.session_state.auto; st.rerun()
    st.markdown(f'<div class="shld"><p style="font-weight:800;color:#00FFA3;margin:0;font-size:1em;">🛡️ PROTECTED</p><p style="color:#808495;margin:4px 0 0;font-size:0.8em;">Stop -25% | Profit +30% | Daily -15% | Max {tier["trades"]}</p></div>', unsafe_allow_html=True)
    col1,col2 = st.columns([2,1])
    with col1:
        st.markdown(f"### 📊 Scanner ({tier['stocks']} stocks)")
        for stk in stks[:tier['stocks']]:
            cc = 'blk' if stk['blk'] else 'buy' if stk['sc']>=MIN_SCORE else 'sell' if stk['sc']<=-MIN_SCORE else 'wait'
            chc = "#00FFA3" if stk['chg']>=0 else "#FF4B4B"
            sgc = "#FF0000" if stk['blk'] else "#00FFA3" if stk['sc']>=MIN_SCORE else "#FF4B4B" if stk['sc']<=-MIN_SCORE else "#FFD700"
            st.markdown(f'<div class="stk {cc}"><div style="display:flex;justify-content:space-between;"><div><h4 style="color:white;margin:0;font-size:1em;">{stk["sym"]}</h4><p style="color:#808495;margin:2px 0 0;font-size:0.8em;">{stk["name"]}</p></div><div style="text-align:right;"><h4 style="color:#00E5FF;margin:0;font-size:1em;">${stk["pr"]:.2f}</h4><p style="color:{chc};margin:2px 0 0;font-weight:600;font-size:0.85em;">{stk["chg"]:+.2f}</p></div></div><div style="display:flex;justify-content:space-between;margin-top:8px;"><span style="color:{sgc};font-weight:700;font-size:0.9em;">{stk["sig"]} ({stk["sc"]}/8)</span><span style="color:#808495;font-size:0.8em;">~${int(stk["oc"])}</span></div></div>', unsafe_allow_html=True)
            ih = "".join([f'<span class="ind {v[1]}">{k}</span>' for k,v in stk['sigs'].items()])
            st.markdown(f'<div style="margin:-3px 0 5px;">{ih}</div>', unsafe_allow_html=True)
            if stk['news']['sent']=='DANGER': st.markdown(f'<div class="nb"><span style="color:#FF4B4B;">⚠️ {", ".join(stk["news"]["red"][:2])}</span></div>', unsafe_allow_html=True)
            elif stk['news']['sent']=='CAUTION': st.markdown(f'<div class="nw"><span style="color:#FFA500;">⚡ {", ".join(stk["news"]["red"][:1])}</span></div>', unsafe_allow_html=True)
            elif stk['news']['sent']=='BULLISH': st.markdown(f'<div class="ng"><span style="color:#00FFA3;">📈 {", ".join(stk["news"]["green"][:2])}</span></div>', unsafe_allow_html=True)
            if tier['auto']!='always' and not st.session_state.auto and stk['sig'] in ['STRONG BUY','BUY','STRONG SELL','SELL'] and not stk['blk'] and len(st.session_state.pos)<tier['trades'] and not hit_limit():
                d = 'CALL' if stk['sc']>0 else 'PUT'
                if st.button(f"BUY {d} ${int(stk['oc']*100)}",key=f"b_{stk['sym']}",use_container_width=True):
                    if buy(stk,d): st.success("✓ Opened!"); st.balloons(); st.rerun()
    with col2:
        st.markdown(f"### 📈 Positions ({len(st.session_state.pos)}/{tier['trades']})")
        if st.session_state.pos:
            for i,p in enumerate(st.session_state.pos):
                pc = "#00FFA3" if p['pnl']>=0 else "#FF4B4B"
                st.markdown(f'<div class="pcard" style="border-left:3px solid {pc};"><div style="display:flex;justify-content:space-between;"><div><h4 style="color:white;margin:0;font-size:0.95em;">{p["sym"]}</h4><p style="color:#808495;font-size:0.75em;">{p["dir"]} @ ${p["entry"]:.2f}</p></div><h4 style="color:{pc};margin:0;">${p["pnl"]:+.2f}</h4></div></div>', unsafe_allow_html=True)
                if tier['auto']!='always' and not st.session_state.auto:
                    if st.button("Close",key=f"c_{i}",use_container_width=True): sell(i); st.rerun()
        else: st.info("No positions")
        st.markdown("### 📜 Ticker")
        for t in reversed(st.session_state.ticker[-5:]):
            tc = "b" if t['a']=='BUY' else "s"
            tcol = "#00FFA3" if t['a']=='BUY' else "#FF4B4B"
            st.markdown(f'<div class="tck {tc}"><span style="color:#808495;">{t["t"]}</span> <span style="color:{tcol};font-weight:600;">{t["a"]}</span> <span style="color:white;">{t["s"]}</span></div>', unsafe_allow_html=True)

def history():
    st.markdown('<div class="logo"><span>🌱</span><span>PROJECT HOPE</span></div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        if st.button("Home",use_container_width=True,key="hh1"): st.session_state.page='home'; st.rerun()
    with c2:
        if st.button("Trade",use_container_width=True,key="hh2"): st.session_state.page='trade'; st.rerun()
    with c3: st.button("History",disabled=True,use_container_width=True)
    with c4:
        if st.button("Learn",use_container_width=True,key="hh4"): st.session_state.page='learn'; st.rerun()
    tot = st.session_state.wins+st.session_state.losses
    wr = (st.session_state.wins/tot*100) if tot>0 else 0
    pc = "#00FFA3" if st.session_state.total>=0 else "#FF4B4B"
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(f'<div class="card stat"><p class="v" style="color:{pc};">${st.session_state.total:,.2f}</p><p class="l">Total P/L</p></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="card stat"><p class="v" style="color:#FFD700;">{wr:.0f}%</p><p class="l">Win Rate</p></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="card stat"><p class="v" style="color:#00FFA3;">{st.session_state.wins}</p><p class="l">Wins</p></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="card stat"><p class="v" style="color:#FF4B4B;">{st.session_state.losses}</p><p class="l">Losses</p></div>', unsafe_allow_html=True)
    st.markdown("### Recent Trades")
    if st.session_state.trades:
        for t in reversed(st.session_state.trades[-10:]):
            c = "#00FFA3" if t['pnl']>=0 else "#FF4B4B"
            st.markdown(f'<div class="card" style="border-left:3px solid {c};padding:12px;"><div style="display:flex;justify-content:space-between;"><div><p style="color:#808495;font-size:0.8em;margin:0;">{t.get("d","")} {t["t"]}</p><h4 style="color:white;margin:6px 0 0;">{t["sym"]} {t.get("dir","")}</h4></div><h3 style="color:{c};margin:0;">${t["pnl"]:+.2f}</h3></div></div>', unsafe_allow_html=True)
    else: st.info("No trades yet")
    if st.button("🔄 Reset Stats",use_container_width=True):
        st.session_state.bal=st.session_state.start
        st.session_state.pos,st.session_state.trades,st.session_state.ticker,st.session_state.data=[],[],[],{}
        st.session_state.daily=st.session_state.total=0.0
        st.session_state.wins=st.session_state.losses=0
        st.session_state.locked=False
        st.rerun()

def learn():
    st.markdown('<div class="logo"><span>🌱</span><span>PROJECT HOPE</span></div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        if st.button("Home",use_container_width=True,key="ll1"): st.session_state.page='home'; st.rerun()
    with c2:
        if st.button("Trade",use_container_width=True,key="ll2"): st.session_state.page='trade'; st.rerun()
    with c3:
        if st.button("History",use_container_width=True,key="ll3"): st.session_state.page='history'; st.rerun()
    with c4: st.button("Learn",disabled=True,use_container_width=True)
    st.markdown("### Options 101")
    c1,c2 = st.columns(2)
    with c1: st.markdown('<div class="card" style="border-left:4px solid #00FFA3;"><h4 style="color:#00FFA3;margin:0;">📈 CALL</h4><p style="color:white;margin:8px 0 0;">Bet stock goes UP</p></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="card" style="border-left:4px solid #FF4B4B;"><h4 style="color:#FF4B4B;margin:0;">📉 PUT</h4><p style="color:white;margin:8px 0 0;">Bet stock goes DOWN</p></div>', unsafe_allow_html=True)
    st.markdown("### Our Indicators")
    for n,d,c in [("RSI","Oversold <30 = Buy, Overbought >70 = Sell","#00FFA3"),("EMA","9/21 crossover = trend change","#00E5FF"),("VWAP","Institutional levels","#FFD700"),("S/R","Support & Resistance","#A855F7"),("NEWS","Blocks bad news, boosts good","#FF0080")]:
        st.markdown(f'<div class="card" style="border-left:4px solid {c};padding:12px;"><h4 style="color:{c};margin:0 0 6px;">{n}</h4><p style="color:#c0c0c0;margin:0;font-size:0.85em;">{d}</p></div>', unsafe_allow_html=True)

def main():
    p = st.session_state.page
    if p=='home': home()
    elif p=='trade': trade()
    elif p=='history': history()
    elif p=='learn': learn()
    else: home()

if __name__=="__main__": main()
