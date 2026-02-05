"""
PROJECT HOPE V2 - Configuration
Top-tier trading bot configuration with WebSocket streaming,
Greeks filtering, IV rank, and real-time data
"""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class TradierConfig:
    """Tradier API configuration"""
    api_key: str
    account_id: str
    base_url: str
    
    @classmethod
    def from_env(cls) -> "TradierConfig":
        return cls(
            api_key=os.environ.get("TRADIER_API_KEY", ""),
            account_id=os.environ.get("TRADIER_ACCOUNT_ID", ""),
            base_url=os.environ.get("TRADIER_BASE_URL", "https://sandbox.tradier.com")
        )
    
    def is_sandbox(self) -> bool:
        return "sandbox" in self.base_url.lower()
    
    @property
    def ws_url(self) -> str:
        """WebSocket URL based on environment"""
        if self.is_sandbox():
            return "wss://sandbox-ws.tradier.com/v1/markets/events"
        return "wss://ws.tradier.com/v1/markets/events"
    
    @property
    def stream_session_url(self) -> str:
        """URL to create streaming session"""
        return f"{self.base_url}/v1/markets/events/session"


@dataclass
class TwilioConfig:
    """Twilio SMS configuration"""
    account_sid: str
    auth_token: str
    from_number: str
    to_number: str
    
    @classmethod
    def from_env(cls) -> "TwilioConfig":
        return cls(
            account_sid=os.environ.get("TWILIO_ACCOUNT_SID", ""),
            auth_token=os.environ.get("TWILIO_AUTH_TOKEN", ""),
            from_number=os.environ.get("TWILIO_FROM_NUMBER", ""),
            to_number=os.environ.get("ALERT_PHONE_NUMBER", "")
        )


@dataclass
class TradingConfig:
    """Trading rules and limits - YOUR 16 PROTECTIONS"""
    
    # Position sizing
    max_positions: int = 5
    position_size_pct: float = 0.05  # 5% of account per trade
    
    # Stop loss / Take profit
    stop_loss_pct: float = -0.25  # -25% hard stop
    take_profit_pct: float = 0.30  # +30% full exit
    
    # Partial profits
    partial_1_trigger: float = 0.15  # +15% sell 50%
    partial_1_sell_pct: float = 0.50
    partial_2_trigger: float = 0.25  # +25% sell 25% more
    partial_2_sell_pct: float = 0.25
    
    # Breakeven stop
    breakeven_trigger: float = 0.10  # +10% move stop to breakeven
    
    # Trailing stop (NEW - after partial 1)
    trailing_stop_pct: float = 0.08  # 8% trail after first partial
    
    # Daily limits
    daily_loss_limit_pct: float = 0.04  # 4% daily loss locks trading
    loss_cooldown_minutes: int = 10
    
    # Signal confirmation
    confirmation_checks: int = 3
    confirmation_interval_sec: int = 5
    
    # HOT score
    min_hot_score: int = 70
    
    # Option quality filters
    min_option_volume: int = 50
    min_open_interest: int = 100
    max_spread_pct: float = 0.10
    
    # Greeks filters (NEW)
    target_delta: float = 0.40
    min_delta: float = 0.25
    max_delta: float = 0.55
    max_theta_pct: float = 0.05  # Max theta as % of option price
    min_iv_rank: float = 20.0  # Don't buy when IV too low
    max_iv_rank: float = 80.0  # Don't buy when IV too high (crushed)
    
    # Stock filters
    min_rvol: float = 1.5
    
    # Earnings blackout
    earnings_blackout_days: int = 5
    
    # Market data
    min_ticks_before_signals: int = 20
    
    # Scan intervals (faster with WebSocket)
    scan_interval_sec: int = 5  # Reduced from 10 - WebSocket gives faster data
    position_check_interval_sec: int = 2  # Check positions every 2 sec
    
    # Opening range period
    opening_range_minutes: int = 15  # First 15 min for ORB


@dataclass
class TradingWindows:
    """Trading time windows (ET) - TESTING ALL DAY"""
    morning_start: str = "09:30"
    morning_end: str = "16:00"
    afternoon_start: str = "09:30"
    afternoon_end: str = "16:00"


@dataclass
class SetupWeights:
    """Weights for HOT score calculation (0-100)"""
    rvol_max_points: int = 25       # Relative volume
    key_level_points: int = 15      # Near support/resistance
    trend_regime_points: int = 15   # TREND market bonus
    volume_spike_points: int = 10   # 2x+ volume spike
    good_spread_points: int = 10    # Tight bid-ask
    greeks_quality_points: int = 15 # Good delta/theta/IV (NEW)
    multi_timeframe_points: int = 10 # Multi-TF alignment (NEW)


class Config:
    """Main configuration container"""
    
    def __init__(self):
        self.tradier = TradierConfig.from_env()
        self.twilio = TwilioConfig.from_env()
        self.trading = TradingConfig()
        self.windows = TradingWindows()
        self.weights = SetupWeights()
    
    def validate(self) -> list:
        errors = []
        if not self.tradier.api_key:
            errors.append("TRADIER_API_KEY not set")
        if not self.tradier.account_id:
            errors.append("TRADIER_ACCOUNT_ID not set")
        if not self.twilio.account_sid:
            errors.append("TWILIO_ACCOUNT_SID not set (alerts disabled)")
        if not self.twilio.auth_token:
            errors.append("TWILIO_AUTH_TOKEN not set (alerts disabled)")
        if not self.twilio.from_number:
            errors.append("TWILIO_FROM_NUMBER not set (alerts disabled)")
        if not self.twilio.to_number:
            errors.append("ALERT_PHONE_NUMBER not set (alerts disabled)")
        return errors


# ==================== WATCHLIST ====================

WATCHLIST = [
    # ETFs
    "SPY", "QQQ", "IWM",
    # Big Tech
    "AAPL", "MSFT", "NVDA", "AMD", "TSLA", "META", "GOOGL", "AMZN", "NFLX",
    # Retail favorites
    "SOFI", "PLTR", "NIO", "RIVN", "HOOD", "SNAP", "COIN", "MARA", "RIOT",
    # Financials
    "JPM", "BAC", "C",
    # Energy
    "XOM", "CVX",
    # Airlines
    "AAL", "UAL", "DAL",
    # Other high-volume
    "F", "GM", "BA", "DIS", "PYPL", "SQ", "ROKU", "UBER"
]


# ==================== NEWS FILTERS ====================

NEGATIVE_NEWS_KEYWORDS = [
    "lawsuit", "sued", "investigation", "fraud", "scandal", "sec probe",
    "subpoena", "indictment", "settlement", "fine", "penalty",
    "bankruptcy", "default", "restructuring", "layoff", "layoffs",
    "guidance cut", "miss estimate", "downgrade", "debt", "liquidity",
    "ceo resign", "cfo resign", "executive depart", "accounting",
    "restatement", "audit", "material weakness",
    "recall", "fda reject", "clinical fail", "supply chain",
    "production halt", "shortage",
    "hack", "breach", "ransomware", "data leak", "cyber attack",
    "plunge", "crash", "tumble", "sink", "collapse"
]

POSITIVE_NEWS_KEYWORDS = [
    "upgrade", "beat estimate", "raise guidance", "partnership",
    "contract win", "fda approve", "acquisition", "buyback",
    "dividend increase", "record revenue", "expansion"
]


# ==================== SETUP TYPES ====================

class SetupType:
    OPENING_RANGE_BREAK = "ORB"
    VWAP_BOUNCE = "VWAP"
    PULLBACK_CONTINUATION = "PULLBACK"
    BREAK_AND_RETEST = "RETEST"
    ALL = [OPENING_RANGE_BREAK, VWAP_BOUNCE, PULLBACK_CONTINUATION, BREAK_AND_RETEST]


# ==================== MARKET REGIMES ====================

class MarketRegime:
    TREND = "TREND"
    MIXED = "MIXED"
    CHOP = "CHOP"
    UNKNOWN = "UNKNOWN"
