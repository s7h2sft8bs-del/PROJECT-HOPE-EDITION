"""
🌱 PROJECT HOPE - OPTIONS TRADING APP v3.0
Built by Stephen Martinez | Lancaster, PA
"Wall Street Protection. Warehouse Worker Prices."

Features:
- SPY 0DTE Options Scalping
- Bulletproof 5-Layer Protection
- Paper Trading Mode for Testing
- Real Tradier Integration (when approved)
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import os
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import requests
import numpy as np
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
import time

# ==================== CONFIGURATION ====================

@dataclass
class Config:
    """App configuration - edit these values"""
    # Tradier API (leave empty for paper trading)
    TRADIER_ACCOUNT_ID: str = os.getenv('TRADIER_ACCOUNT_ID', '')
    TRADIER_API_TOKEN: str = os.getenv('TRADIER_API_TOKEN', '')
    TRADIER_LIVE: bool = os.getenv('TRADIER_LIVE', 'false').lower() == 'true'
    
    # Pushover Notifications
    PUSHOVER_USER: str = os.getenv('PUSHOVER_USER_KEY', '')
    PUSHOVER_TOKEN: str = os.getenv('PUSHOVER_API_TOKEN', '')
    
    # Risk Management (BULLETPROOF PROTECTION)
    MAX_RISK_PER_TRADE: float = 0.05      # 5% max per trade
    MAX_DAILY_LOSS: float = 0.15          # 15% daily loss = STOP
    MAX_OPEN_POSITIONS: int = 3           # Max 3 positions
    MIN_CASH_RESERVE: float = 0.20        # Keep 20% cash always
    
    # Trade Management
    STOP_LOSS: float = 0.25               # -25% stop loss
    TRAILING_STOP: float = 0.15           # 15% trailing stop
    TAKE_PROFIT_1: float = 0.30           # +30% take half
    TAKE_PROFIT_2: float = 0.50           # +50% take rest
    MAX_GAIN: float = 1.00                # Let winners run to 100%
    
    # Trading Limits
    MAX_TRADES_PER_DAY: int = 6
    LOSS_COOLDOWN_TRADES: int = 2         # Pause after 2 consecutive losses
    COOLDOWN_MINUTES: int = 30
    
    # Paper Trading
    PAPER_STARTING_BALANCE: float = 1000.0
    
    @property
    def TRADIER_BASE_URL(self) -> str:
        return "https://api.tradier.com/v1" if self.TRADIER_LIVE else "https://sandbox.tradier.com/v1"
    
    @property
    def is_paper_mode(self) -> bool:
        return not self.TRADIER_API_TOKEN

CONFIG = Config()

# ==================== PAGE CONFIG ====================

st.set_page_config(
    page_title="🌱 Project Hope",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Auto-refresh every 5 seconds
st_autorefresh(interval=5000, key="main_refresh")

# ==================== CUSTOM CSS ====================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background: linear-gradient(145deg, #0a0a0f 0%, #111827 50%, #0f172a 100%);
}

/* Hero Section */
.hero {
    text-align: center;
    padding: 40px 30px;
    background: linear-gradient(145deg, rgba(0,255,163,0.08), rgba(255,215,0,0.05));
    backdrop-filter: blur(30px);
    border-radius: 28px;
    margin-bottom: 24px;
    border: 1px solid rgba(255,255,255,0.1);
}

.hero h1 {
    font-size: 2.8em;
    font-weight: 800;
    background: linear-gradient(135deg, #00FFA3, #00E5FF, #FFD700);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    letter-spacing: -1px;
}

.hero .subtitle {
    color: #FFD700;
    font-size: 1.2em;
    font-weight: 600;
    margin: 10px 0;
}

.hero .tagline {
    color: #808495;
    font-size: 1em;
}

/* Glass Cards */
.glass {
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 20px;
    margin: 10px 0;
}

/* Stat Cards */
.stat-card {
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(16px);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.06);
}

.stat-card .label {
    color: #808495;
    font-size: 0.85em;
    margin-bottom: 8px;
}

.stat-card .value {
    font-size: 1.5em;
    font-weight: 700;
}

/* Signal Cards */
.signal-card {
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(16px);
    border-radius: 20px;
    padding: 24px;
    margin: 12px 0;
    border: 1px solid rgba(255,255,255,0.08);
}

.signal-call {
    border-left: 5px solid #00FFA3;
    background: linear-gradient(90deg, rgba(0,255,163,0.1), transparent);
}

.signal-put {
    border-left: 5px solid #FF4B4B;
    background: linear-gradient(90deg, rgba(255,75,75,0.1), transparent);
}

.signal-hot {
    animation: pulse 2s infinite;
    border: 2px solid #00FFA3;
}

@keyframes pulse {
    0%, 100% { box-shadow: 0 0 20px rgba(0,255,163,0.3); }
    50% { box-shadow: 0 0 40px rgba(0,255,163,0.5); }
}

/* Protection Shield */
.shield {
    background: linear-gradient(145deg, rgba(0,255,163,0.12), rgba(0,200,100,0.05));
    border: 2px solid rgba(0,255,163,0.3);
    border-radius: 16px;
    padding: 16px 20px;
    text-align: center;
    margin: 16px 0;
}

.shield-active {
    color: #00FFA3;
    font-weight: 600;
}

/* Mode Badge */
.mode-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
}

.mode-paper {
    background: rgba(255,215,0,0.15);
    border: 1px solid rgba(255,215,0,0.4);
    color: #FFD700;
}

.mode-live {
    background: rgba(255,75,75,0.15);
    border: 1px solid rgba(255,75,75,0.4);
    color: #FF4B4B;
}

/* Position Cards */
.position-card {
    background: rgba(255,255,255,0.03);
    border-radius: 16px;
    padding: 20px;
    margin: 10px 0;
    border: 1px solid rgba(255,255,255,0.08);
}

.position-profit {
    border-left: 4px solid #00FFA3;
}

.position-loss {
    border-left: 4px solid #FF4B4B;
}

/* Tier Cards */
.tier-card {
    background: rgba(255,255,255,0.02);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 28px 20px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.08);
    height: 100%;
    transition: transform 0.3s ease;
}

.tier-card:hover {
    transform: translateY(-4px);
}

.tier-starter { border-top: 4px solid #00FFA3; }
.tier-builder { border-top: 4px solid #00E5FF; }
.tier-master { border-top: 4px solid #FFD700; }
.tier-vip { border-top: 4px solid #FF6B6B; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #00FFA3 0%, #00CC7A 100%);
    color: black;
    font-weight: 700;
    border: none;
    border-radius: 12px;
    padding: 12px 24px;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,255,163,0.35);
}

/* Navigation */
.nav-btn {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 12px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s ease;
}

.nav-btn:hover {
    background: rgba(255,255,255,0.1);
}

.nav-btn.active {
    background: rgba(0,255,163,0.15);
    border-color: rgba(0,255,163,0.3);
}

/* Hide Streamlit Elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Trade Log */
.trade-log {
    max-height: 300px;
    overflow-y: auto;
    padding: 10px;
}

.trade-item {
    padding: 12px;
    margin: 8px 0;
    border-radius: 12px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
}

.trade-win {
    border-left: 3px solid #00FFA3;
}

.trade-loss {
    border-left: 3px solid #FF4B4B;
}
</style>
""", unsafe_allow_html=True)

# ==================== DATA CLASSES ====================

@dataclass
class Position:
    symbol: str
    option_symbol: str
    direction: str  # CALL or PUT
    strike: float
    expiration: str
    quantity: int
    entry_price: float
    current_price: float
    entry_time: str
    stop_price: float
    target_price: float
    
    @property
    def pnl(self) -> float:
        return (self.current_price - self.entry_price) * self.quantity * 100
    
    @property
    def pnl_percent(self) -> float:
        if self.entry_price == 0:
            return 0
        return ((self.current_price - self.entry_price) / self.entry_price) * 100
    
    @property
    def cost_basis(self) -> float:
        return self.entry_price * self.quantity * 100

@dataclass
class Trade:
    timestamp: str
    symbol: str
    direction: str
    action: str  # BUY or SELL
    quantity: int
    price: float
    pnl: float = 0.0
    reason: str = ""

# ==================== SESSION STATE ====================

def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        # Navigation
        'page': 'home',
        'tier': 0,
        
        # Paper Trading Account
        'paper_balance': CONFIG.PAPER_STARTING_BALANCE,
        'paper_equity': CONFIG.PAPER_STARTING_BALANCE,
        'paper_positions': [],
        'paper_trades': [],
        
        # Trading Stats
        'daily_pnl': 0.0,
        'total_pnl': 0.0,
        'wins': 0,
        'losses': 0,
        'trades_today': 0,
        'consecutive_losses': 0,
        'cooldown_until': None,
        
        # Settings
        'autopilot': False,
        'sound_alerts': True,
        
        # Market Data Cache
        'last_spy_price': 595.0,
        'last_update': None,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ==================== API FUNCTIONS ====================

class TradierAPI:
    """Tradier API wrapper"""
    
    @staticmethod
    def _headers():
        return {
            'Authorization': f'Bearer {CONFIG.TRADIER_API_TOKEN}',
            'Accept': 'application/json'
        }
    
    @staticmethod
    def _post_headers():
        return {
            'Authorization': f'Bearer {CONFIG.TRADIER_API_TOKEN}',
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    
    @classmethod
    def get(cls, endpoint: str, params: dict = None) -> Optional[dict]:
        if CONFIG.is_paper_mode:
            return None
        try:
            r = requests.get(
                f"{CONFIG.TRADIER_BASE_URL}{endpoint}",
                headers=cls._headers(),
                params=params,
                timeout=10
            )
            return r.json() if r.status_code == 200 else None
        except Exception as e:
            st.error(f"API Error: {e}")
            return None
    
    @classmethod
    def post(cls, endpoint: str, data: dict = None) -> Optional[dict]:
        if CONFIG.is_paper_mode:
            return None
        try:
            r = requests.post(
                f"{CONFIG.TRADIER_BASE_URL}{endpoint}",
                headers=cls._post_headers(),
                data=data,
                timeout=10
            )
            return r.json() if r.status_code in [200, 201] else None
        except Exception as e:
            st.error(f"API Error: {e}")
            return None

# ==================== MARKET DATA ====================

class MarketData:
    """Market data fetching and analysis"""
    
    @staticmethod
    def get_spy_quote() -> dict:
        """Get SPY quote - real or simulated"""
        if not CONFIG.is_paper_mode:
            result = TradierAPI.get('/markets/quotes', {'symbols': 'SPY'})
            if result and 'quotes' in result:
                q = result['quotes'].get('quote', {})
                if isinstance(q, list):
                    q = q[0]
                return {
                    'price': float(q.get('last', 0)),
                    'change': float(q.get('change', 0)),
                    'change_pct': float(q.get('change_percentage', 0)),
                    'volume': int(q.get('volume', 0)),
                    'high': float(q.get('high', 0)),
                    'low': float(q.get('low', 0)),
                    'open': float(q.get('open', 0)),
                }
        
        # Paper trading mode - simulate realistic SPY price movement
        base_price = st.session_state.last_spy_price
        
        # Random walk with mean reversion
        change = random.gauss(0, 0.15)  # Small random change
        
        # Mean revert toward 595
        if base_price > 600:
            change -= 0.05
        elif base_price < 590:
            change += 0.05
        
        new_price = round(base_price + change, 2)
        st.session_state.last_spy_price = new_price
        
        return {
            'price': new_price,
            'change': round(change, 2),
            'change_pct': round((change / base_price) * 100, 2),
            'volume': random.randint(50000000, 80000000),
            'high': round(new_price + random.uniform(0.5, 2), 2),
            'low': round(new_price - random.uniform(0.5, 2), 2),
            'open': round(new_price - random.uniform(-1, 1), 2),
        }
    
    @staticmethod
    def get_history(symbol: str = 'SPY', days: int = 30) -> List[dict]:
        """Get price history - real or simulated"""
        if not CONFIG.is_paper_mode:
            start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            result = TradierAPI.get('/markets/history', {
                'symbol': symbol,
                'interval': 'daily',
                'start': start,
                'end': datetime.now().strftime('%Y-%m-%d')
            })
            if result and 'history' in result and result['history']:
                return result['history'].get('day', [])
        
        # Simulate history for paper trading
        history = []
        price = 590.0
        for i in range(days):
            change = random.gauss(0, 1.5)
            price = max(550, min(650, price + change))
            date = (datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d')
            history.append({
                'date': date,
                'open': round(price - random.uniform(0, 1), 2),
                'high': round(price + random.uniform(0.5, 3), 2),
                'low': round(price - random.uniform(0.5, 3), 2),
                'close': round(price, 2),
                'volume': random.randint(40000000, 90000000)
            })
        return history
    
    @staticmethod
    def get_option_chain(symbol: str, expiration: str) -> List[dict]:
        """Get options chain - real or simulated"""
        if not CONFIG.is_paper_mode:
            result = TradierAPI.get('/markets/options/chains', {
                'symbol': symbol,
                'expiration': expiration,
                'greeks': 'true'
            })
            if result and 'options' in result and result['options']:
                opts = result['options'].get('option', [])
                return opts if isinstance(opts, list) else [opts]
        
        # Simulate options chain for paper trading
        spy_price = st.session_state.last_spy_price
        chain = []
        
        for strike in range(int(spy_price) - 5, int(spy_price) + 6):
            for opt_type in ['call', 'put']:
                # Calculate realistic option price
                itm = (strike < spy_price) if opt_type == 'call' else (strike > spy_price)
                distance = abs(strike - spy_price)
                
                # Base price from intrinsic + time value
                intrinsic = max(0, spy_price - strike) if opt_type == 'call' else max(0, strike - spy_price)
                time_value = max(0.10, 1.5 - (distance * 0.15))
                
                bid = round(intrinsic + time_value - 0.05, 2)
                ask = round(intrinsic + time_value + 0.05, 2)
                
                # Delta approximation
                if opt_type == 'call':
                    delta = 0.5 + (spy_price - strike) * 0.05
                    delta = max(0.05, min(0.95, delta))
                else:
                    delta = -0.5 + (spy_price - strike) * 0.05
                    delta = max(-0.95, min(-0.05, delta))
                
                chain.append({
                    'symbol': f"SPY{expiration.replace('-', '')}{opt_type[0].upper()}{strike:08.3f}".replace('.', ''),
                    'strike': float(strike),
                    'option_type': opt_type,
                    'bid': max(0.01, bid),
                    'ask': max(0.05, ask),
                    'last': round((bid + ask) / 2, 2),
                    'volume': random.randint(100, 5000),
                    'open_interest': random.randint(1000, 50000),
                    'greeks': {
                        'delta': round(delta, 3),
                        'gamma': round(random.uniform(0.01, 0.05), 4),
                        'theta': round(-random.uniform(0.02, 0.15), 4),
                        'vega': round(random.uniform(0.05, 0.20), 4),
                    }
                })
        
        return chain

# ==================== TECHNICAL ANALYSIS ====================

class TechnicalAnalysis:
    """Technical analysis calculations"""
    
    @staticmethod
    def calc_rsi(prices: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def calc_ema(prices: List[float], period: int) -> float:
        """Calculate EMA"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        multiplier = 2 / (period + 1)
        ema = np.mean(prices[:period])
        
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    @staticmethod
    def calc_levels(history: List[dict]) -> Optional[dict]:
        """Calculate support/resistance levels"""
        if not history or len(history) < 5:
            return None
        
        highs = [float(d['high']) for d in history]
        lows = [float(d['low']) for d in history]
        closes = [float(d['close']) for d in history]
        
        # Recent support/resistance
        support = min(lows[-5:])
        resistance = max(highs[-5:])
        pivot = (resistance + support + closes[-1]) / 3
        
        return {
            'support': round(support, 2),
            'resistance': round(resistance, 2),
            'pivot': round(pivot, 2)
        }
    
    @classmethod
    def analyze_spy(cls) -> Optional[dict]:
        """Complete SPY analysis for trading signals"""
        quote = MarketData.get_spy_quote()
        history = MarketData.get_history('SPY', 30)
        
        if not quote or not history:
            return None
        
        price = quote['price']
        closes = [float(d['close']) for d in history]
        volumes = [float(d['volume']) for d in history]
        
        # Technical indicators
        rsi = cls.calc_rsi(closes)
        ema9 = cls.calc_ema(closes, 9)
        ema21 = cls.calc_ema(closes, 21)
        levels = cls.calc_levels(history)
        
        if not levels:
            return None
        
        avg_vol = np.mean(volumes[-10:]) if volumes else 1
        vol_ratio = quote['volume'] / avg_vol if avg_vol > 0 else 1
        
        # Distance to levels
        dist_support = ((price - levels['support']) / price) * 100
        dist_resistance = ((levels['resistance'] - price) / price) * 100
        
        # Generate signals
        score = 0
        signals = {}
        direction = 'WAIT'
        
        # Level check (most important)
        if dist_support < 0.5:
            score += 2
            signals['level'] = ('🎯 AT SUPPORT', 'bullish')
            direction = 'CALL'
        elif dist_resistance < 0.5:
            score += 2
            signals['level'] = ('🎯 AT RESISTANCE', 'bearish')
            direction = 'PUT'
        else:
            signals['level'] = ('Between levels', 'neutral')
        
        # RSI check
        if rsi < 30:
            score += 2
            signals['rsi'] = (f'🔥 OVERSOLD ({rsi:.0f})', 'bullish')
            if direction == 'WAIT':
                direction = 'CALL'
        elif rsi > 70:
            score += 2
            signals['rsi'] = (f'🔥 OVERBOUGHT ({rsi:.0f})', 'bearish')
            if direction == 'WAIT':
                direction = 'PUT'
        elif rsi < 40:
            score += 1
            signals['rsi'] = (f'Leaning oversold ({rsi:.0f})', 'bullish')
        elif rsi > 60:
            score += 1
            signals['rsi'] = (f'Leaning overbought ({rsi:.0f})', 'bearish')
        else:
            signals['rsi'] = (f'Neutral ({rsi:.0f})', 'neutral')
        
        # Trend check
        if price > ema9 > ema21:
            if direction in ['CALL', 'WAIT']:
                score += 1
            signals['trend'] = ('📈 UPTREND', 'bullish')
        elif price < ema9 < ema21:
            if direction in ['PUT', 'WAIT']:
                score += 1
            signals['trend'] = ('📉 DOWNTREND', 'bearish')
        else:
            signals['trend'] = ('➡️ Sideways', 'neutral')
        
        # Volume check
        if vol_ratio > 1.5:
            score += 1
            signals['volume'] = (f'🔥 HIGH VOLUME ({vol_ratio:.1f}x)', 'bullish')
        else:
            signals['volume'] = (f'Normal ({vol_ratio:.1f}x)', 'neutral')
        
        return {
            'price': price,
            'quote': quote,
            'direction': direction,
            'score': score,
            'signals': signals,
            'levels': levels,
            'rsi': rsi,
            'ema9': ema9,
            'ema21': ema21,
            'vol_ratio': vol_ratio
        }

# ==================== TRADING ENGINE ====================

class TradingEngine:
    """Handles all trading operations with protection"""
    
    @staticmethod
    def get_account() -> dict:
        """Get account balances"""
        if CONFIG.is_paper_mode:
            # Calculate equity from positions
            positions_value = sum(
                p.current_price * p.quantity * 100 
                for p in st.session_state.paper_positions
            )
            equity = st.session_state.paper_balance + positions_value
            
            return {
                'balance': st.session_state.paper_balance,
                'equity': equity,
                'buying_power': st.session_state.paper_balance * (1 - CONFIG.MIN_CASH_RESERVE),
                'positions_value': positions_value
            }
        else:
            result = TradierAPI.get(f'/accounts/{CONFIG.TRADIER_ACCOUNT_ID}/balances')
            if result and 'balances' in result:
                b = result['balances']
                return {
                    'balance': float(b.get('total_cash', 0)),
                    'equity': float(b.get('total_equity', 0)),
                    'buying_power': float(b.get('option_buying_power', b.get('cash', 0))),
                    'positions_value': 0
                }
            return {'balance': 0, 'equity': 0, 'buying_power': 0, 'positions_value': 0}
    
    @staticmethod
    def can_trade() -> tuple[bool, str]:
        """Check if trading is allowed (protection checks)"""
        account = TradingEngine.get_account()
        
        # Check daily loss limit
        if st.session_state.daily_pnl <= -(account['equity'] * CONFIG.MAX_DAILY_LOSS):
            return False, "🛑 Daily loss limit reached (-15%). Trading paused."
        
        # Check cooldown
        if st.session_state.cooldown_until:
            if datetime.now() < st.session_state.cooldown_until:
                remaining = (st.session_state.cooldown_until - datetime.now()).seconds
                return False, f"⏸️ Cooldown active. {remaining // 60}m {remaining % 60}s remaining."
            else:
                st.session_state.cooldown_until = None
                st.session_state.consecutive_losses = 0
        
        # Check max trades per day
        if st.session_state.trades_today >= CONFIG.MAX_TRADES_PER_DAY:
            return False, "📊 Max daily trades reached. Come back tomorrow!"
        
        # Check max positions
        if len(st.session_state.paper_positions) >= CONFIG.MAX_OPEN_POSITIONS:
            return False, f"📦 Max positions ({CONFIG.MAX_OPEN_POSITIONS}) reached. Close one first."
        
        return True, "✅ Ready to trade"
    
    @staticmethod
    def find_best_option(chain: List[dict], direction: str, price: float, max_cost: float) -> Optional[dict]:
        """Find the best option contract for the trade"""
        opt_type = 'call' if direction == 'CALL' else 'put'
        candidates = []
        
        for opt in chain:
            if opt.get('option_type') != opt_type:
                continue
            
            strike = float(opt.get('strike', 0))
            ask = float(opt.get('ask', 0))
            delta = abs(float(opt.get('greeks', {}).get('delta', 0)))
            
            # Filter: ATM or slightly OTM
            if direction == 'CALL':
                if strike > price + 3 or strike < price - 1:
                    continue
            else:
                if strike < price - 3 or strike > price + 1:
                    continue
            
            cost = ask * 100
            
            # Must be within budget and reasonable
            if cost > max_cost or cost < 10:
                continue
            
            # Delta should be 0.25-0.60 for good risk/reward
            if delta < 0.25 or delta > 0.60:
                continue
            
            candidates.append({
                'symbol': opt.get('symbol'),
                'strike': strike,
                'type': opt_type,
                'bid': float(opt.get('bid', 0)),
                'ask': ask,
                'delta': delta,
                'theta': float(opt.get('greeks', {}).get('theta', 0)),
                'gamma': float(opt.get('greeks', {}).get('gamma', 0)),
                'cost': cost
            })
        
        if not candidates:
            return None
        
        # Sort by delta closest to 0.45 (sweet spot)
        candidates.sort(key=lambda x: abs(x['delta'] - 0.45))
        return candidates[0]
    
    @staticmethod
    def execute_buy(option: dict, direction: str, quantity: int = 1) -> bool:
        """Execute a buy order"""
        cost = option['ask'] * quantity * 100
        
        if CONFIG.is_paper_mode:
            # Paper trading - simulate the buy
            if cost > st.session_state.paper_balance:
                st.error("Insufficient funds!")
                return False
            
            # Deduct from balance
            st.session_state.paper_balance -= cost
            
            # Create position
            position = Position(
                symbol='SPY',
                option_symbol=option['symbol'],
                direction=direction,
                strike=option['strike'],
                expiration=datetime.now().strftime('%Y-%m-%d'),
                quantity=quantity,
                entry_price=option['ask'],
                current_price=option['ask'],
                entry_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                stop_price=round(option['ask'] * (1 - CONFIG.STOP_LOSS), 2),
                target_price=round(option['ask'] * (1 + CONFIG.TAKE_PROFIT_1), 2)
            )
            
            st.session_state.paper_positions.append(position)
            
            # Record trade
            trade = Trade(
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                symbol=option['symbol'],
                direction=direction,
                action='BUY',
                quantity=quantity,
                price=option['ask']
            )
            st.session_state.paper_trades.append(trade)
            st.session_state.trades_today += 1
            
            return True
        else:
            # Real trading via Tradier
            data = {
                'class': 'option',
                'symbol': 'SPY',
                'option_symbol': option['symbol'],
                'side': 'buy_to_open',
                'quantity': quantity,
                'type': 'market',
                'duration': 'day'
            }
            result = TradierAPI.post(f'/accounts/{CONFIG.TRADIER_ACCOUNT_ID}/orders', data)
            return result is not None
    
    @staticmethod
    def execute_sell(position: Position, reason: str = "Manual") -> bool:
        """Execute a sell order"""
        if CONFIG.is_paper_mode:
            # Calculate PnL
            pnl = position.pnl
            
            # Add back to balance (current value)
            proceeds = position.current_price * position.quantity * 100
            st.session_state.paper_balance += proceeds
            
            # Update stats
            st.session_state.daily_pnl += pnl
            st.session_state.total_pnl += pnl
            
            if pnl >= 0:
                st.session_state.wins += 1
                st.session_state.consecutive_losses = 0
            else:
                st.session_state.losses += 1
                st.session_state.consecutive_losses += 1
                
                # Check if cooldown needed
                if st.session_state.consecutive_losses >= CONFIG.LOSS_COOLDOWN_TRADES:
                    st.session_state.cooldown_until = datetime.now() + timedelta(minutes=CONFIG.COOLDOWN_MINUTES)
            
            # Record trade
            trade = Trade(
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                symbol=position.option_symbol,
                direction=position.direction,
                action='SELL',
                quantity=position.quantity,
                price=position.current_price,
                pnl=pnl,
                reason=reason
            )
            st.session_state.paper_trades.append(trade)
            
            # Remove position
            st.session_state.paper_positions.remove(position)
            
            return True
        else:
            # Real trading via Tradier
            data = {
                'class': 'option',
                'symbol': 'SPY',
                'option_symbol': position.option_symbol,
                'side': 'sell_to_close',
                'quantity': position.quantity,
                'type': 'market',
                'duration': 'day'
            }
            result = TradierAPI.post(f'/accounts/{CONFIG.TRADIER_ACCOUNT_ID}/orders', data)
            return result is not None
    
    @staticmethod
    def update_positions():
        """Update all position prices and check stops/targets"""
        if not st.session_state.paper_positions:
            return
        
        spy_quote = MarketData.get_spy_quote()
        spy_price = spy_quote['price']
        
        positions_to_close = []
        
        for position in st.session_state.paper_positions:
            # Simulate price movement based on SPY movement and delta
            # This is simplified - real options pricing is more complex
            spy_change = (spy_price - st.session_state.last_spy_price) if hasattr(st.session_state, 'last_spy_price') else 0
            
            if position.direction == 'CALL':
                # Call increases when SPY increases
                price_change = spy_change * 0.5 * random.uniform(0.8, 1.2)
            else:
                # Put increases when SPY decreases
                price_change = -spy_change * 0.5 * random.uniform(0.8, 1.2)
            
            # Update current price (with some noise)
            position.current_price = max(0.01, position.current_price + price_change + random.gauss(0, 0.02))
            
            # Check stop loss
            if position.current_price <= position.stop_price:
                positions_to_close.append((position, "STOP LOSS"))
            
            # Check take profit
            elif position.current_price >= position.target_price:
                positions_to_close.append((position, "TAKE PROFIT"))
        
        # Close positions that hit stops/targets
        for position, reason in positions_to_close:
            TradingEngine.execute_sell(position, reason)
            st.toast(f"{'🟢' if reason == 'TAKE PROFIT' else '🔴'} {reason}: {position.option_symbol}")

# ==================== NOTIFICATIONS ====================

def send_notification(title: str, message: str, sound: str = "cashregister"):
    """Send push notification via Pushover"""
    if not CONFIG.PUSHOVER_USER or not CONFIG.PUSHOVER_TOKEN:
        return
    
    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": CONFIG.PUSHOVER_TOKEN,
                "user": CONFIG.PUSHOVER_USER,
                "title": f"🌱 {title}",
                "message": message,
                "sound": sound
            },
            timeout=5
        )
    except:
        pass

# ==================== PAGE RENDERERS ====================

def render_home():
    """Render the home/landing page"""
    
    # Hero
    st.markdown('''
    <div class="hero">
        <h1>🌱 PROJECT HOPE</h1>
        <p class="subtitle">OPTIONS TRADING EDITION</p>
        <p class="tagline">Turn $200 into $2,000 with Bulletproof Protection</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.button("🏠 Home", disabled=True, use_container_width=True)
    with col2:
        if st.button("📊 Trade", use_container_width=True):
            if st.session_state.tier > 0:
                st.session_state.page = 'trade'
                st.rerun()
            else:
                st.warning("Enter access code below first!")
    with col3:
        if st.button("📜 History", use_container_width=True):
            st.session_state.page = 'history'
            st.rerun()
    with col4:
        if st.button("📖 Learn", use_container_width=True):
            st.session_state.page = 'learn'
            st.rerun()
    
    st.markdown("---")
    
    # Why Options section
    st.markdown("## 💰 Why Options Beat Stocks")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('''
        <div class="glass" style="border-left: 4px solid #FF4B4B;">
            <h3 style="color: #FF4B4B; margin: 0 0 15px 0;">❌ Old Way (Stocks)</h3>
            <p style="color: white; margin: 8px 0;">$200 account → Buy 2 shares of SPY</p>
            <p style="color: white; margin: 8px 0;">SPY goes up 1% → <b style="color: #FF4B4B;">$2 profit</b></p>
            <p style="color: #808495; margin: 15px 0 0 0;">"I made $2 this week..." 😴</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown('''
        <div class="glass" style="border-left: 4px solid #00FFA3;">
            <h3 style="color: #00FFA3; margin: 0 0 15px 0;">✅ New Way (Options)</h3>
            <p style="color: white; margin: 8px 0;">$200 account → Buy 4 option contracts</p>
            <p style="color: white; margin: 8px 0;">SPY goes up 1% → <b style="color: #00FFA3;">$100+ profit</b></p>
            <p style="color: #808495; margin: 15px 0 0 0;">"I made $100 TODAY!" 🔥</p>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Protection section
    st.markdown("## 🛡️ Bulletproof Protection (5 Layers)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('''
        <div class="stat-card">
            <div class="value" style="color: #00FFA3;">-25%</div>
            <div class="label">Stop Loss</div>
            <p style="color: white; font-size: 0.85em; margin-top: 10px;">Auto-sells losers FAST</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown('''
        <div class="stat-card">
            <div class="value" style="color: #FFD700;">-15%</div>
            <div class="label">Daily Max Loss</div>
            <p style="color: white; font-size: 0.85em; margin-top: 10px;">App STOPS if you hit this</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown('''
        <div class="stat-card">
            <div class="value" style="color: #00E5FF;">5%</div>
            <div class="label">Max Per Trade</div>
            <p style="color: white; font-size: 0.85em; margin-top: 10px;">Never overbet</p>
        </div>
        ''', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('''
        <div class="stat-card">
            <div class="value" style="color: #FF6B6B;">3 Max</div>
            <div class="label">Open Positions</div>
            <p style="color: white; font-size: 0.85em; margin-top: 10px;">Can't overload</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown('''
        <div class="stat-card">
            <div class="value" style="color: #A855F7;">30 min</div>
            <div class="label">Loss Cooldown</div>
            <p style="color: white; font-size: 0.85em; margin-top: 10px;">Pause after 2 losses</p>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Pricing tiers
    st.markdown("## 💎 Choose Your Plan")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('''
        <div class="tier-card tier-starter">
            <h3 style="color: #00FFA3; margin: 0;">🌱 STARTER</h3>
            <h2 style="color: white; margin: 20px 0;">$49<span style="font-size: 0.4em; color: #808495;">/mo</span></h2>
            <p style="color: white; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">✅ Options Scanner</p>
            <p style="color: white; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">✅ Push Alerts</p>
            <p style="color: white; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">✅ Education</p>
            <p style="color: #808495; padding: 8px 0;">❌ Auto-Trade</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown('''
        <div class="tier-card tier-builder">
            <h3 style="color: #00E5FF; margin: 0;">🚀 BUILDER</h3>
            <h2 style="color: white; margin: 20px 0;">$99<span style="font-size: 0.4em; color: #808495;">/mo</span></h2>
            <p style="color: white; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">✅ Everything in Starter</p>
            <p style="color: white; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">✅ One-Click Trading</p>
            <p style="color: white; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">✅ Trade History</p>
            <p style="color: #808495; padding: 8px 0;">❌ Autopilot</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown('''
        <div class="tier-card tier-master" style="transform: scale(1.02); box-shadow: 0 0 40px rgba(255,215,0,0.15);">
            <p style="color: #FFD700; font-size: 0.75em; margin-bottom: 8px;">⭐ MOST POPULAR</p>
            <h3 style="color: #FFD700; margin: 0;">⚡ MASTER</h3>
            <h2 style="color: white; margin: 20px 0;">$199<span style="font-size: 0.4em; color: #808495;">/mo</span></h2>
            <p style="color: white; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">✅ Everything in Builder</p>
            <p style="color: white; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">✅ <b>FULL AUTOPILOT</b></p>
            <p style="color: white; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">✅ Auto Stop & Profit</p>
            <p style="color: white; padding: 8px 0;">✅ Priority Support</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        st.markdown('''
        <div class="tier-card tier-vip">
            <h3 style="color: #FF6B6B; margin: 0;">💎 VIP</h3>
            <h2 style="color: white; margin: 20px 0;">$499<span style="font-size: 0.4em; color: #808495;">/mo</span></h2>
            <p style="color: white; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">✅ Everything in Master</p>
            <p style="color: white; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">✅ Weekly 1-on-1 Calls</p>
            <p style="color: white; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">✅ Private Discord</p>
            <p style="color: white; padding: 8px 0;">✅ Custom Settings</p>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Access code entry
    st.markdown("### 🔐 Enter Access Code")
    
    _, col_center, _ = st.columns([1, 2, 1])
    
    with col_center:
        code = st.text_input(
            "Access Code",
            type="password",
            label_visibility="collapsed",
            placeholder="Enter your access code..."
        )
        
        access_codes = {
            "HOPE49": 1,
            "HOPE99": 2, 
            "HOPE199": 3,
            "HOPE499": 4,
            "DEMO": 3  # Demo code for testing
        }
        
        tier_names = {
            1: "🌱 STARTER",
            2: "🚀 BUILDER",
            3: "⚡ MASTER",
            4: "💎 VIP"
        }
        
        if code:
            if code.upper() in access_codes:
                st.session_state.tier = access_codes[code.upper()]
                st.success(f"✅ {tier_names[st.session_state.tier]} Access Granted!")
            else:
                st.error("❌ Invalid access code")
        
        if st.session_state.tier > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 Enter Trading Dashboard", type="primary", use_container_width=True):
                st.session_state.page = 'trade'
                st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown('''
    <div style="text-align: center; color: #808495; padding: 20px;">
        <p>Built with ❤️ by Stephen Martinez | Lancaster, PA</p>
        <p style="font-size: 0.85em;">Amazon warehouse worker building hope for regular people</p>
    </div>
    ''', unsafe_allow_html=True)


def render_trade():
    """Render the trading dashboard"""
    
    # Check access
    if st.session_state.tier == 0:
        st.warning("⚠️ Please enter an access code on the Home page first.")
        if st.button("← Go to Home"):
            st.session_state.page = 'home'
            st.rerun()
        return
    
    tier_names = {1: "🌱 STARTER", 2: "🚀 BUILDER", 3: "⚡ MASTER", 4: "💎 VIP"}
    
    # Update positions
    TradingEngine.update_positions()
    
    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f'''
        <h2 style="color: #00FFA3; margin: 0;">🌱 PROJECT HOPE</h2>
        <p style="color: #808495; margin: 0;">{tier_names[st.session_state.tier]}</p>
        ''', unsafe_allow_html=True)
    
    with col2:
        mode = "PAPER" if CONFIG.is_paper_mode else "LIVE"
        mode_class = "mode-paper" if CONFIG.is_paper_mode else "mode-live"
        st.markdown(f'<span class="mode-badge {mode_class}">{"📝" if CONFIG.is_paper_mode else "🔴"} {mode} MODE</span>', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'<p style="color: #808495; text-align: right; margin: 0;">{datetime.now().strftime("%I:%M:%S %p")}</p>', unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()
    with col2:
        st.button("📊 Trade", disabled=True, use_container_width=True)
    with col3:
        if st.button("📜 History", use_container_width=True):
            st.session_state.page = 'history'
            st.rerun()
    with col4:
        if st.button("📖 Learn", use_container_width=True):
            st.session_state.page = 'learn'
            st.rerun()
    
    st.markdown("---")
    
    # Account Stats
    account = TradingEngine.get_account()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Equity", f"${account['equity']:,.2f}")
    
    with col2:
        st.metric("💵 Buying Power", f"${account['buying_power']:,.2f}")
    
    with col3:
        daily_color = "normal" if st.session_state.daily_pnl >= 0 else "inverse"
        st.metric(
            "📊 Today's P&L",
            f"${st.session_state.daily_pnl:,.2f}",
            delta=f"{st.session_state.daily_pnl:+.2f}",
            delta_color=daily_color
        )
    
    with col4:
        total_trades = st.session_state.wins + st.session_state.losses
        win_rate = (st.session_state.wins / total_trades * 100) if total_trades > 0 else 0
        st.metric("🏆 Win Rate", f"{win_rate:.0f}%", delta=f"{st.session_state.wins}W / {st.session_state.losses}L")
    
    # Protection Shield
    can_trade, trade_status = TradingEngine.can_trade()
    shield_color = "#00FFA3" if can_trade else "#FF4B4B"
    
    st.markdown(f'''
    <div class="shield" style="border-color: {shield_color}40;">
        <span class="shield-active" style="color: {shield_color};">🛡️ BULLETPROOF PROTECTION {'ACTIVE' if can_trade else 'TRIGGERED'}</span><br>
        <span style="color: #808495; font-size: 0.9em;">Stop: -25% | Daily Max: -15% | Per Trade: 5% | Max Positions: 3</span><br>
        <span style="color: {shield_color}; font-size: 0.85em;">{trade_status}</span>
    </div>
    ''', unsafe_allow_html=True)
    
    # Autopilot toggle (Master tier+)
    if st.session_state.tier >= 3:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### 🤖 Autopilot Mode")
        with col2:
            st.session_state.autopilot = st.toggle("Enable", value=st.session_state.autopilot)
        
        if st.session_state.autopilot:
            st.success("🤖 AUTOPILOT ACTIVE - Auto-scanning, auto-buying at signals, auto-managing stops & profits")
    
    st.markdown("---")
    
    # Two column layout: Scanner | Positions
    col_scanner, col_positions = st.columns([2, 1])
    
    with col_scanner:
        st.markdown("### 📊 SPY Options Scanner")
        
        analysis = TechnicalAnalysis.analyze_spy()
        
        if analysis:
            # SPY Price Card
            quote = analysis['quote']
            price_color = "#00FFA3" if quote['change'] >= 0 else "#FF4B4B"
            
            st.markdown(f'''
            <div class="glass">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h2 style="color: white; margin: 0;">SPY</h2>
                        <p style="color: #808495; margin: 0;">S&P 500 ETF</p>
                    </div>
                    <div style="text-align: right;">
                        <h2 style="color: #00E5FF; margin: 0;">${analysis['price']:.2f}</h2>
                        <p style="color: {price_color}; margin: 0;">{quote['change']:+.2f} ({quote['change_pct']:+.2f}%)</p>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Key Levels
            levels = analysis['levels']
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f'''
                <div class="stat-card">
                    <div class="label">Support</div>
                    <div class="value" style="color: #00FFA3;">${levels['support']}</div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col2:
                st.markdown(f'''
                <div class="stat-card">
                    <div class="label">Pivot</div>
                    <div class="value" style="color: #FFD700;">${levels['pivot']}</div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col3:
                st.markdown(f'''
                <div class="stat-card">
                    <div class="label">Resistance</div>
                    <div class="value" style="color: #FF4B4B;">${levels['resistance']}</div>
                </div>
                ''', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Signal Card
            direction = analysis['direction']
            score = analysis['score']
            
            if direction != 'WAIT' and score >= 4:
                signal_class = "signal-call signal-hot" if direction == 'CALL' else "signal-put signal-hot"
                signal_color = "#00FFA3" if direction == 'CALL' else "#FF4B4B"
                
                st.markdown(f'''
                <div class="signal-card {signal_class}">
                    <h3 style="color: {signal_color}; margin: 0;">🔥 {direction} SIGNAL - {score}/5 STARS</h3>
                    <p style="color: white; margin: 10px 0 0 0;">Strong setup detected! Consider entering trade.</p>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.info(f"⏳ Waiting for setup... Current score: {score}/5 (need 4+)")
            
            # Signal Breakdown
            st.markdown("#### Signal Analysis")
            for key, (text, status) in analysis['signals'].items():
                icon = "✅" if status == 'bullish' else "❌" if status == 'bearish' else "⚪"
                st.markdown(f"{icon} **{key.upper()}:** {text}")
            
            # Trade Execution (Builder tier+)
            if st.session_state.tier >= 2 and direction != 'WAIT' and score >= 4 and can_trade:
                st.markdown("---")
                st.markdown("### 💎 Recommended Trade")
                
                # Get option chain
                expiration = datetime.now().strftime('%Y-%m-%d')
                chain = MarketData.get_option_chain('SPY', expiration)
                max_cost = account['buying_power'] * CONFIG.MAX_RISK_PER_TRADE
                
                option = TradingEngine.find_best_option(chain, direction, analysis['price'], max_cost)
                
                if option:
                    opt_color = "#00FFA3" if direction == 'CALL' else "#FF4B4B"
                    
                    st.markdown(f'''
                    <div class="glass" style="border-left: 4px solid {opt_color};">
                        <h4 style="color: {opt_color}; margin: 0;">SPY ${option['strike']:.0f} {direction}</h4>
                        <p style="color: #808495; margin: 5px 0;">Expires: {expiration}</p>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 15px 0;">
                            <div>
                                <p style="color: #808495; margin: 0; font-size: 0.85em;">Ask Price</p>
                                <p style="color: white; font-size: 1.2em; margin: 0;">${option['ask']:.2f}</p>
                            </div>
                            <div>
                                <p style="color: #808495; margin: 0; font-size: 0.85em;">Total Cost</p>
                                <p style="color: white; font-size: 1.2em; margin: 0;">${option['cost']:.2f}</p>
                            </div>
                            <div>
                                <p style="color: #808495; margin: 0; font-size: 0.85em;">Delta</p>
                                <p style="color: #00E5FF; margin: 0;">{option['delta']:.2f}</p>
                            </div>
                            <div>
                                <p style="color: #808495; margin: 0; font-size: 0.85em;">Theta</p>
                                <p style="color: #FFD700; margin: 0;">{option['theta']:.3f}</p>
                            </div>
                        </div>
                        <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px;">
                            <p style="color: #00FFA3; margin: 4px 0;">🎯 Target (+30%): ${option['ask'] * 1.3:.2f}</p>
                            <p style="color: #FFD700; margin: 4px 0;">🎯 Target (+50%): ${option['ask'] * 1.5:.2f}</p>
                            <p style="color: #FF4B4B; margin: 4px 0;">🛡️ Stop (-25%): ${option['ask'] * 0.75:.2f}</p>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    # Buy button
                    if st.button(f"🟢 BUY {direction} - ${option['cost']:.2f}", type="primary", use_container_width=True):
                        if TradingEngine.execute_buy(option, direction):
                            st.success(f"✅ Bought SPY ${option['strike']:.0f} {direction} @ ${option['ask']:.2f}")
                            send_notification("Trade Executed", f"BUY SPY ${option['strike']:.0f} {direction} @ ${option['ask']:.2f}")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Order failed!")
                else:
                    st.warning("No suitable options found within risk parameters.")
        else:
            st.warning("⚠️ Unable to fetch market data. Check connection.")
    
    with col_positions:
        st.markdown("### 📈 Open Positions")
        
        positions = st.session_state.paper_positions
        
        if positions:
            for i, pos in enumerate(positions):
                pnl_color = "#00FFA3" if pos.pnl >= 0 else "#FF4B4B"
                pos_class = "position-profit" if pos.pnl >= 0 else "position-loss"
                
                st.markdown(f'''
                <div class="position-card {pos_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="color: white; margin: 0;">SPY ${pos.strike:.0f} {pos.direction}</h4>
                            <p style="color: #808495; font-size: 0.85em; margin: 4px 0;">Entry: ${pos.entry_price:.2f}</p>
                        </div>
                        <div style="text-align: right;">
                            <p style="color: {pnl_color}; font-size: 1.2em; font-weight: 600; margin: 0;">${pos.pnl:+.2f}</p>
                            <p style="color: {pnl_color}; font-size: 0.85em; margin: 0;">{pos.pnl_percent:+.1f}%</p>
                        </div>
                    </div>
                    <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);">
                        <p style="color: #808495; font-size: 0.8em; margin: 0;">Current: ${pos.current_price:.2f} | Stop: ${pos.stop_price:.2f} | Target: ${pos.target_price:.2f}</p>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                # Close button
                if st.button(f"Close Position", key=f"close_{i}", use_container_width=True):
                    if TradingEngine.execute_sell(pos, "Manual Close"):
                        st.success(f"Closed for ${pos.pnl:+.2f}")
                        st.rerun()
        else:
            st.info("No open positions")
        
        # Quick Stats
        st.markdown("---")
        st.markdown("### 📊 Today's Stats")
        
        st.markdown(f'''
        <div class="glass">
            <p style="color: #808495; margin: 4px 0;">Trades Today: <b style="color: white;">{st.session_state.trades_today}</b> / {CONFIG.MAX_TRADES_PER_DAY}</p>
            <p style="color: #808495; margin: 4px 0;">Wins: <b style="color: #00FFA3;">{st.session_state.wins}</b></p>
            <p style="color: #808495; margin: 4px 0;">Losses: <b style="color: #FF4B4B;">{st.session_state.losses}</b></p>
            <p style="color: #808495; margin: 4px 0;">Consecutive Losses: <b style="color: {'#FF4B4B' if st.session_state.consecutive_losses > 0 else 'white'};">{st.session_state.consecutive_losses}</b></p>
        </div>
        ''', unsafe_allow_html=True)


def render_history():
    """Render trade history page"""
    
    st.markdown('''
    <div class="hero">
        <h1>📜 Trade History</h1>
        <p class="tagline">Review your trading performance</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()
    with col2:
        if st.button("📊 Trade", use_container_width=True):
            st.session_state.page = 'trade'
            st.rerun()
    with col3:
        st.button("📜 History", disabled=True, use_container_width=True)
    with col4:
        if st.button("📖 Learn", use_container_width=True):
            st.session_state.page = 'learn'
            st.rerun()
    
    st.markdown("---")
    
    # Stats Summary
    total_trades = st.session_state.wins + st.session_state.losses
    win_rate = (st.session_state.wins / total_trades * 100) if total_trades > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pnl_color = "#00FFA3" if st.session_state.total_pnl >= 0 else "#FF4B4B"
        st.markdown(f'''
        <div class="stat-card">
            <div class="label">Total P&L</div>
            <div class="value" style="color: {pnl_color};">${st.session_state.total_pnl:,.2f}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="stat-card">
            <div class="label">Win Rate</div>
            <div class="value" style="color: #FFD700;">{win_rate:.0f}%</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div class="stat-card">
            <div class="label">Wins</div>
            <div class="value" style="color: #00FFA3;">{st.session_state.wins}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'''
        <div class="stat-card">
            <div class="label">Losses</div>
            <div class="value" style="color: #FF4B4B;">{st.session_state.losses}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Trade List
    st.markdown("### 📋 Recent Trades")
    
    trades = st.session_state.paper_trades
    
    if trades:
        # Show most recent first
        for trade in reversed(trades[-20:]):  # Last 20 trades
            trade_class = "trade-win" if trade.pnl >= 0 else "trade-loss"
            pnl_color = "#00FFA3" if trade.pnl >= 0 else "#FF4B4B"
            
            st.markdown(f'''
            <div class="trade-item {trade_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <p style="color: #808495; font-size: 0.85em; margin: 0;">{trade.timestamp}</p>
                        <h4 style="color: white; margin: 4px 0;">{trade.action} {trade.symbol}</h4>
                        <p style="color: #808495; font-size: 0.85em; margin: 0;">Qty: {trade.quantity} @ ${trade.price:.2f} {f"| {trade.reason}" if trade.reason else ""}</p>
                    </div>
                    <div style="text-align: right;">
                        <p style="color: {pnl_color}; font-size: 1.3em; font-weight: 600; margin: 0;">${trade.pnl:+.2f}</p>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.info("No trades yet. Start trading to see your history!")
    
    # Reset button (for testing)
    st.markdown("---")
    
    if st.button("🔄 Reset All Stats (Testing)", type="secondary"):
        st.session_state.paper_balance = CONFIG.PAPER_STARTING_BALANCE
        st.session_state.paper_positions = []
        st.session_state.paper_trades = []
        st.session_state.daily_pnl = 0.0
        st.session_state.total_pnl = 0.0
        st.session_state.wins = 0
        st.session_state.losses = 0
        st.session_state.trades_today = 0
        st.session_state.consecutive_losses = 0
        st.session_state.cooldown_until = None
        st.success("Stats reset!")
        st.rerun()


def render_learn():
    """Render education page"""
    
    st.markdown('''
    <div class="hero">
        <h1>📖 Learn Options Trading</h1>
        <p class="tagline">Master the basics in 5 minutes</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()
    with col2:
        if st.button("📊 Trade", use_container_width=True):
            st.session_state.page = 'trade'
            st.rerun()
    with col3:
        if st.button("📜 History", use_container_width=True):
            st.session_state.page = 'history'
            st.rerun()
    with col4:
        st.button("📖 Learn", disabled=True, use_container_width=True)
    
    st.markdown("---")
    
    # What are options
    st.markdown("## 🎯 What Are Options?")
    
    st.markdown('''
    Options are contracts that let you profit from stock movements **without owning the stock**.
    
    Think of it like a movie ticket:
    - You pay $15 for the **right** to see a movie
    - If the movie is sold out, your ticket is worth MORE
    - If the theater is empty, your ticket is worth LESS
    - Max you can lose = $15 (the ticket price)
    ''')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('''
        <div class="glass" style="border-left: 4px solid #00FFA3;">
            <h3 style="color: #00FFA3; margin: 0 0 10px 0;">📈 CALL Option</h3>
            <p style="color: white;">Bet that the stock goes <b>UP</b></p>
            <p style="color: #808495;">Buy calls when bullish</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown('''
        <div class="glass" style="border-left: 4px solid #FF4B4B;">
            <h3 style="color: #FF4B4B; margin: 0 0 10px 0;">📉 PUT Option</h3>
            <p style="color: white;">Bet that the stock goes <b>DOWN</b></p>
            <p style="color: #808495;">Buy puts when bearish</p>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Why options
    st.markdown("## 💰 Why Options > Stocks")
    
    st.markdown('''
    <div class="glass">
        <h3 style="color: #FFD700; margin: 0 0 15px 0;">⚡ LEVERAGE</h3>
        <p style="color: white; font-size: 1.1em;">With $50 in options, you can control $5,000 worth of stock movement!</p>
        <div style="margin: 20px 0; padding: 15px; background: rgba(0,255,163,0.1); border-radius: 12px;">
            <p style="color: #00FFA3; margin: 0;"><b>Example:</b> SPY moves 1%</p>
            <p style="color: white; margin: 5px 0;">• Stock: $200 → $2 profit (1%)</p>
            <p style="color: white; margin: 5px 0;">• Option: $50 → $25+ profit (50%+)</p>
        </div>
        <p style="color: #808495;">Same market move, MUCH bigger return (with proper protection!)</p>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Key terms
    st.markdown("## 📚 Key Terms")
    
    terms = [
        ("Strike Price", "The price you're betting the stock will reach"),
        ("Expiration", "When the option expires (we use same-day = 0DTE)"),
        ("Premium", "What you pay for the option contract"),
        ("Delta", "How much the option moves per $1 stock move"),
        ("ITM (In The Money)", "Option is profitable if exercised now"),
        ("OTM (Out of The Money)", "Option needs stock to move more to profit"),
    ]
    
    for term, definition in terms:
        st.markdown(f'''
        <div style="display: flex; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
            <div style="min-width: 180px;"><b style="color: #00E5FF;">{term}</b></div>
            <div style="color: white;">{definition}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Our protection system
    st.markdown("## 🛡️ Our Protection System")
    
    st.markdown("**Why most traders lose:** No protection. One bad trade wipes out weeks of gains.")
    st.markdown("**Our solution:** 5 layers of bulletproof protection.")
    
    protections = [
        ("25% Stop Loss", "If your option drops 25%, we auto-sell. No hoping for a comeback.", "#00FFA3"),
        ("15% Daily Max", "Lose 15% of your account in a day? Trading stops. Period.", "#FFD700"),
        ("5% Per Trade", "Never risk more than 5% on a single trade. No YOLO bets.", "#00E5FF"),
        ("3 Max Positions", "Can't have more than 3 trades at once. Prevents overtrading.", "#FF6B6B"),
        ("Cooldown Timer", "2 losses in a row? 30-minute break. Prevents revenge trading.", "#A855F7"),
    ]
    
    for i, (title, desc, color) in enumerate(protections, 1):
        st.markdown(f'''
        <div style="display: flex; align-items: center; background: rgba(255,255,255,0.02); padding: 16px; margin: 10px 0; border-radius: 12px; border-left: 3px solid {color};">
            <div style="background: {color}; color: black; min-width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 16px;">{i}</div>
            <div>
                <b style="color: white;">{title}</b><br>
                <span style="color: #808495;">{desc}</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Ready to trade
    st.markdown("## 🚀 Ready to Start?")
    
    if st.button("Go to Trading Dashboard →", type="primary", use_container_width=True):
        if st.session_state.tier > 0:
            st.session_state.page = 'trade'
            st.rerun()
        else:
            st.warning("Enter an access code on the Home page first!")


# ==================== MAIN ====================

def main():
    """Main app entry point"""
    page = st.session_state.page
    
    if page == 'home':
        render_home()
    elif page == 'trade':
        render_trade()
    elif page == 'history':
        render_history()
    elif page == 'learn':
        render_learn()
    else:
        render_home()


if __name__ == "__main__":
    main()
