"""
PROJECT HOPE - Configuration
All settings loaded from environment variables for security
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
    max_positions: int = 5  # VIP tier max
    position_size_pct: float = 0.05  # 5% of account per trade
    
    # Stop loss / Take profit
    stop_loss_pct: float = -0.25  # -25% hard stop
    take_profit_pct: float = 0.30  # +30% full exit
    
    # Partial profits
    partial_1_trigger: float = 0.15  # +15% triggers first partial
    partial_1_sell_pct: float = 0.50  # Sell 50% at first partial
    partial_2_trigger: float = 0.25  # +25% triggers second partial
    partial_2_sell_pct: float = 0.25  # Sell 25% more at second partial
    
    # Breakeven stop
    breakeven_trigger: float = 0.10  # +10% move stop to breakeven
    
    # Daily limits
    daily_loss_limit_pct: float = 0.04  # 4% daily loss locks trading
    loss_cooldown_minutes: int = 10  # Minutes to wait after any loss
    
    # Signal confirmation (15 seconds total)
    confirmation_checks: int = 3  # Signal must hold for 3 checks
    confirmation_interval_sec: int = 5  # 5 seconds between checks
    
    # HOT score
    min_hot_score: int = 70
    
    # Option quality filters
    min_option_volume: int = 50
    min_open_interest: int = 100
    max_spread_pct: float = 0.10  # Max 10% bid-ask spread
    
    # Stock filters
    min_rvol: float = 1.5  # Minimum relative volume
    
    # Earnings blackout
    earnings_blackout_days: int = 5
    
    # Market data requirements
    min_ticks_before_signals: int = 20  # Need 20 price ticks first
    
    # Scan intervals
    scan_interval_sec: int = 10  # How often to scan for signals
    price_check_interval_sec: int = 3  # How often to check positions


@dataclass 
class TradingWindows:
    """Trading time windows (ET) - TESTING ALL DAY"""
    morning_start: str = "04:00"
    morning_end: str = "20:00"
    afternoon_start: str = "04:00"
    afternoon_end: str = "20:00"


@dataclass
class SetupWeights:
    """Weights for HOT score calculation"""
    rvol_max_points: int = 30  # Relative volume contribution
    key_level_points: int = 20  # Near support/resistance
    trend_regime_points: int = 20  # TREND market bonus
    volume_spike_points: int = 15  # 2x+ volume spike
    good_spread_points: int = 10  # Tight bid-ask
    bullish_news_points: int = 5  # Positive news sentiment


class Config:
    """Main configuration container"""
    
    def __init__(self):
        self.tradier = TradierConfig.from_env()
        self.twilio = TwilioConfig.from_env()
        self.trading = TradingConfig()
        self.windows = TradingWindows()
        self.weights = SetupWeights()
    
    def validate(self) -> list:
        """Validate configuration, return list of errors"""
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
# High volume, options-friendly stocks

WATCHLIST = [
    # ETFs (most liquid)
    "SPY", "QQQ", "IWM",
    
    # Big Tech
    "AAPL", "MSFT", "NVDA", "AMD", "TSLA", "META", "GOOGL", "AMZN", "NFLX",
    
    # Retail favorites (high volume, volatile)
    "SOFI", "PLTR", "NIO", "RIVN", "HOOD", "SNAP", "COIN", "MARA", "RIOT",
    
    # Financials
    "JPM", "BAC", "C",
    
    # Energy
    "XOM", "CVX",
    
    # Airlines (volatile)
    "AAL", "UAL", "DAL",
    
    # Other high-volume
    "F", "GM", "BA", "DIS", "PYPL", "SQ", "ROKU", "UBER"
]


# ==================== NEWS FILTERS ====================
# Keywords that BLOCK trades (negative sentiment)

NEGATIVE_NEWS_KEYWORDS = [
    # Legal/Regulatory
    "lawsuit", "sued", "investigation", "fraud", "scandal", "sec probe",
    "subpoena", "indictment", "settlement", "fine", "penalty",
    
    # Financial distress
    "bankruptcy", "default", "restructuring", "layoff", "layoffs",
    "guidance cut", "miss estimate", "downgrade", "debt", "liquidity",
    
    # Management issues
    "ceo resign", "cfo resign", "executive depart", "accounting",
    "restatement", "audit", "material weakness",
    
    # Product/Operations
    "recall", "fda reject", "clinical fail", "supply chain",
    "production halt", "shortage",
    
    # Cyber/Security
    "hack", "breach", "ransomware", "data leak", "cyber attack",
    
    # Negative price action keywords
    "plunge", "crash", "tumble", "sink", "collapse"
]

# Keywords that are POSITIVE (add to HOT score)
POSITIVE_NEWS_KEYWORDS = [
    "upgrade", "beat estimate", "raise guidance", "partnership",
    "contract win", "fda approve", "acquisition", "buyback",
    "dividend increase", "record revenue", "expansion"
]


# ==================== SETUP TYPES ====================

class SetupType:
    """Setup identification constants"""
    OPENING_RANGE_BREAK = "ORB"  # Opening Range Breakout
    VWAP_BOUNCE = "VWAP"  # VWAP Bounce/Reject
    PULLBACK_CONTINUATION = "PULLBACK"  # EMA Pullback
    BREAK_AND_RETEST = "RETEST"  # Break & Retest
    
    ALL = [OPENING_RANGE_BREAK, VWAP_BOUNCE, PULLBACK_CONTINUATION, BREAK_AND_RETEST]


# ==================== MARKET REGIMES ====================

class MarketRegime:
    """Market regime constants"""
    TREND = "TREND"  # Good to trade
    MIXED = "MIXED"  # No trading
    CHOP = "CHOP"    # No trading
    UNKNOWN = "UNKNOWN"  # Waiting for data
