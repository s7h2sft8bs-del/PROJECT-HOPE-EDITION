"""
PROJECT HOPE V1 - Configuration
All 16 trading protections, watchlist, and settings
REST polling only - no WebSocket needed
"""

import os
from dataclasses import dataclass, field
from typing import List


# ==================== API CONFIGS ====================

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


# ==================== TRADING RULES ====================

@dataclass
class RiskConfig:
    """YOUR 16 PROTECTIONS"""
    # Stop loss / Take profit
    stop_loss_pct: float = -0.25          # -25% stop loss
    take_profit_pct: float = 0.30         # +30% take profit
    partial_t1_pct: float = 0.15          # +15% sell 50%
    partial_t1_sell: float = 0.50         # sell 50% at T1
    partial_t2_pct: float = 0.25          # +25% sell 25% more
    partial_t2_sell: float = 0.25         # sell 25% at T2
    breakeven_trigger_pct: float = 0.10   # +10% move stop to entry

    # Daily limits
    daily_loss_limit_pct: float = 0.04    # 4% daily loss = lock trading
    cooldown_after_loss_sec: int = 600    # 10 min cooldown after loss

    # Position limits
    max_positions: int = 5                # VIP tier max
    position_size_pct: float = 0.05       # 5% of account per trade


@dataclass
class TradingWindows:
    """Trading time windows (ET) - TESTING ALL DAY"""
    morning_start: str = "09:30"
    morning_end: str = "16:00"
    afternoon_start: str = "09:30"
    afternoon_end: str = "16:00"


@dataclass
class SignalConfig:
    """Signal quality requirements"""
    hot_score_minimum: int = 70           # Minimum HOT score
    confirmation_checks: int = 3          # 3 checks over 15 sec
    confirmation_interval_sec: int = 5    # 5 sec between checks
    min_rvol: float = 1.5                 # Relative volume minimum
    scan_interval_sec: int = 10           # Poll every 10 sec
    position_check_interval_sec: int = 5  # Check positions every 5 sec


@dataclass
class OptionFilters:
    """Option quality filters"""
    max_spread_pct: float = 0.10          # Max 10% bid-ask spread
    min_volume: int = 10                  # Minimum option volume
    min_open_interest: int = 50           # Minimum open interest
    min_delta: float = 0.30               # Minimum delta
    max_delta: float = 0.70               # Maximum delta
    max_dte: int = 14                     # Max days to expiration
    min_dte: int = 1                      # Min days to expiration


# ==================== HOT SCORE WEIGHTS ====================

@dataclass
class HotScoreWeights:
    """HOT score component weights (total = 100)"""
    regime: int = 25          # Market regime (TREND = 25, MIXED = 10, CHOP = 0)
    setup_quality: int = 20   # A+ setup match quality
    rvol: int = 15            # Relative volume
    trend_alignment: int = 15 # EMA alignment
    vwap_position: int = 10   # Price vs VWAP
    spread_quality: int = 10  # Bid-ask spread tightness
    time_of_day: int = 5      # First 30 min = 5, rest = 3


# ==================== MASTER CONFIG ====================

@dataclass
class Config:
    tradier: TradierConfig = None
    twilio: TwilioConfig = None
    risk: RiskConfig = field(default_factory=RiskConfig)
    windows: TradingWindows = field(default_factory=TradingWindows)
    signals: SignalConfig = field(default_factory=SignalConfig)
    options: OptionFilters = field(default_factory=OptionFilters)
    hot_weights: HotScoreWeights = field(default_factory=HotScoreWeights)

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            tradier=TradierConfig.from_env(),
            twilio=TwilioConfig.from_env()
        )

    def validate(self) -> list:
        errors = []
        if not self.tradier.api_key:
            errors.append("TRADIER_API_KEY not set")
        if not self.tradier.account_id:
            errors.append("TRADIER_ACCOUNT_ID not set")
        if not self.twilio.account_sid:
            errors.append("TWILIO_ACCOUNT_SID not set (SMS disabled)")
        return errors


# ==================== WATCHLIST ====================

WATCHLIST = [
    "SPY", "QQQ", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA",
    "TSLA", "AMD", "NFLX", "CRM", "ORCL", "ADBE", "INTC",
    "BA", "DIS", "NKE", "SBUX", "HD", "LOW", "TGT", "WMT",
    "JPM", "GS", "BAC", "V", "MA", "PYPL",
    "XOM", "CVX", "PFE", "JNJ", "UNH", "ABBV",
    "COIN", "MARA", "PLTR"
]


# ==================== NEWS KEYWORDS ====================

NEGATIVE_NEWS_KEYWORDS = [
    "downgrade", "miss estimate", "lower guidance", "lawsuit",
    "investigation", "recall", "data breach", "layoff", "bankruptcy",
    "SEC probe", "FDA reject", "trade war", "sanction", "default",
    "crash", "fraud", "scandal", "indictment", "subpoena"
]

POSITIVE_NEWS_KEYWORDS = [
    "upgrade", "beat estimate", "raise guidance", "partnership",
    "contract win", "fda approve", "acquisition", "buyback",
    "dividend increase", "record revenue", "expansion"
]


# ==================== ENUMS ====================

class MarketRegime:
    TREND = "TREND"
    MIXED = "MIXED"
    CHOP = "CHOP"
    UNKNOWN = "UNKNOWN"


class SetupType:
    OPENING_RANGE_BREAK = "ORB"
    VWAP_BOUNCE = "VWAP"
    PULLBACK_CONTINUATION = "PULLBACK"
    BREAK_AND_RETEST = "RETEST"
    ALL = ["ORB", "VWAP", "PULLBACK", "RETEST"]
