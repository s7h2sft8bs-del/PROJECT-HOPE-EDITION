"""
PROJECT HOPE V1 - Market Analyzer
Regime detection, 4 A+ setups, HOT score, signal generation
All using REST API polling data
"""

import logging
import math
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pytz

from config import (
    Config, MarketRegime, SetupType, WATCHLIST,
    NEGATIVE_NEWS_KEYWORDS, POSITIVE_NEWS_KEYWORDS
)
from tradier_client import TradierClient

logger = logging.getLogger(__name__)

ET = pytz.timezone('US/Eastern')


@dataclass
class StockData:
    """Tracked data for a single stock"""
    symbol: str
    current_price: float = 0.0
    current_volume: int = 0
    average_volume: int = 0
    bid: float = 0.0
    ask: float = 0.0

    # Price history (for EMA calculation)
    price_history: deque = field(default_factory=lambda: deque(maxlen=50))

    # EMAs
    ema_9: float = 0.0
    ema_21: float = 0.0

    # VWAP tracking
    vwap: float = 0.0
    vwap_crosses: int = 0
    last_vwap_side: str = ""  # "above" or "below"
    cum_volume: float = 0.0
    cum_vol_price: float = 0.0

    # Opening range
    opening_range_high: float = 0.0
    opening_range_low: float = 0.0
    opening_range_set: bool = False
    or_start_time: Optional[datetime] = None
    or_prices: list = field(default_factory=list)

    # Key levels
    prior_day_high: float = 0.0
    prior_day_low: float = 0.0
    prior_day_close: float = 0.0
    day_open: float = 0.0
    day_high: float = 0.0
    day_low: float = 0.0

    # Tick count
    tick_count: int = 0


@dataclass
class Signal:
    """Trade signal"""
    symbol: str
    direction: str  # "CALL" or "PUT"
    setup: str      # SetupType
    hot_score: int
    entry_price: float
    stop_price: float
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)


class MarketAnalyzer:
    """
    Analyzes market data from REST polling.
    Detects regime, generates signals, calculates HOT scores.
    """

    def __init__(self, config: Config, client: TradierClient):
        self.config = config
        self.client = client

        # Per-symbol data
        self.stock_data: Dict[str, StockData] = {}

        # Market regime
        self.regime = MarketRegime.UNKNOWN
        self.spy_vwap_crosses = 0

        # Signal confirmation tracking
        self._pending_signals: Dict[str, dict] = {}

        # Scan counter
        self.scan_count = 0

    def initialize(self, symbols: List[str]):
        """Initialize tracking for all symbols"""
        for sym in symbols:
            self.stock_data[sym] = StockData(symbol=sym)
        logger.info(f"📊 Analyzer initialized for {len(symbols)} symbols")

    def update(self, symbols: List[str]) -> List[Signal]:
        """
        Main update cycle - poll quotes and analyze.
        Returns list of confirmed signals.
        """
        self.scan_count += 1
        signals = []

        # Batch fetch quotes
        quotes = self.client.get_quotes(symbols)
        if not quotes:
            logger.warning("⚠️ No quotes received")
            return signals

        now = datetime.now(ET)

        # Update each symbol
        for sym, quote in quotes.items():
            data = self.stock_data.get(sym)
            if not data:
                continue

            price = quote.get("price", 0)
            if price <= 0:
                continue

            # Update basic data
            data.current_price = price
            data.bid = quote.get("bid", price)
            data.ask = quote.get("ask", price)
            data.current_volume = quote.get("volume", 0)
            data.average_volume = quote.get("average_volume", 0)
            data.day_high = quote.get("high", price)
            data.day_low = quote.get("low", price)
            data.day_open = quote.get("open", price)
            data.prior_day_close = quote.get("prevclose", price)
            data.tick_count += 1

            # Add to price history
            data.price_history.append(price)

            # Calculate EMAs
            if len(data.price_history) >= 9:
                data.ema_9 = self._calc_ema(list(data.price_history), 9)
            if len(data.price_history) >= 21:
                data.ema_21 = self._calc_ema(list(data.price_history), 21)

            # Update VWAP (simple approximation from polling)
            if data.current_volume > 0:
                data.cum_volume += data.current_volume
                data.cum_vol_price += price * data.current_volume
                if data.cum_volume > 0:
                    data.vwap = data.cum_vol_price / data.cum_volume

            # Track VWAP crosses (for regime)
            if sym == "SPY" and data.vwap > 0:
                side = "above" if price > data.vwap else "below"
                if data.last_vwap_side and side != data.last_vwap_side:
                    data.vwap_crosses += 1
                data.last_vwap_side = side

            # Opening range (first 15 min of data)
            if not data.opening_range_set:
                if data.or_start_time is None:
                    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
                    if now >= market_open:
                        data.or_start_time = market_open
                
                if data.or_start_time:
                    data.or_prices.append(price)
                    elapsed = (now - data.or_start_time).total_seconds()
                    if elapsed >= 900 and len(data.or_prices) >= 3:  # 15 min
                        data.opening_range_high = max(data.or_prices)
                        data.opening_range_low = min(data.or_prices)
                        data.opening_range_set = True
                        logger.info(f"📐 {sym} OR set: ${data.opening_range_low:.2f} - ${data.opening_range_high:.2f}")

        # Update regime from SPY
        self._update_regime()

        # Log status periodically
        if self.scan_count % 6 == 0:  # Every ~60 sec
            spy = self.stock_data.get("SPY")
            if spy:
                logger.info(
                    f"📊 Scan #{self.scan_count} | SPY ${spy.current_price:.2f} | "
                    f"Regime: {self.regime} | VWAP crosses: {spy.vwap_crosses}"
                )

        # Only generate signals if regime is TREND
        if self.regime != MarketRegime.TREND:
            return signals

        # Scan for setups
        for sym in symbols:
            data = self.stock_data.get(sym)
            if not data or data.tick_count < 5:
                continue
            if data.current_price <= 0:
                continue

            signal = self._check_setups(data, now)
            if signal:
                # Run through confirmation
                confirmed = self._confirm_signal(signal)
                if confirmed:
                    signals.append(confirmed)

        return signals

    def _update_regime(self):
        """Detect market regime from SPY VWAP crosses"""
        spy = self.stock_data.get("SPY")
        if not spy:
            self.regime = MarketRegime.UNKNOWN
            return

        self.spy_vwap_crosses = spy.vwap_crosses
        old_regime = self.regime

        if spy.vwap_crosses <= 2:
            self.regime = MarketRegime.TREND
        elif spy.vwap_crosses <= 5:
            self.regime = MarketRegime.MIXED
        else:
            self.regime = MarketRegime.CHOP

        if self.regime != old_regime:
            logger.info(f"🔄 Regime change: {old_regime} → {self.regime} (crosses: {spy.vwap_crosses})")

    def _check_setups(self, data: StockData, now: datetime) -> Optional[Signal]:
        """Check all 4 A+ setups for a symbol"""
        # Setup 1: Opening Range Break
        signal = self._check_orb(data, now)
        if signal:
            return signal

        # Setup 2: VWAP Bounce
        signal = self._check_vwap_bounce(data, now)
        if signal:
            return signal

        # Setup 3: Pullback Continuation
        signal = self._check_pullback(data, now)
        if signal:
            return signal

        # Setup 4: Break and Retest
        signal = self._check_break_retest(data, now)
        if signal:
            return signal

        return None

    def _check_orb(self, data: StockData, now: datetime) -> Optional[Signal]:
        """Opening Range Breakout"""
        if not data.opening_range_set:
            return None

        price = data.current_price
        or_high = data.opening_range_high
        or_low = data.opening_range_low
        or_range = or_high - or_low

        if or_range <= 0:
            return None

        # Break above OR high
        if price > or_high * 1.001:  # Small buffer
            hot = self._calc_hot_score(data, SetupType.OPENING_RANGE_BREAK, "CALL")
            if hot >= self.config.signals.hot_score_minimum:
                return Signal(
                    symbol=data.symbol,
                    direction="CALL",
                    setup=SetupType.OPENING_RANGE_BREAK,
                    hot_score=hot,
                    entry_price=price,
                    stop_price=or_low,
                    reason=f"ORB above ${or_high:.2f}"
                )

        # Break below OR low
        if price < or_low * 0.999:
            hot = self._calc_hot_score(data, SetupType.OPENING_RANGE_BREAK, "PUT")
            if hot >= self.config.signals.hot_score_minimum:
                return Signal(
                    symbol=data.symbol,
                    direction="PUT",
                    setup=SetupType.OPENING_RANGE_BREAK,
                    hot_score=hot,
                    entry_price=price,
                    stop_price=or_high,
                    reason=f"ORB below ${or_low:.2f}"
                )

        return None

    def _check_vwap_bounce(self, data: StockData, now: datetime) -> Optional[Signal]:
        """VWAP Bounce/Reject"""
        if data.vwap <= 0 or len(data.price_history) < 5:
            return None

        price = data.current_price
        vwap = data.vwap
        distance = abs(price - vwap) / vwap

        # Must be near VWAP (within 0.3%)
        if distance > 0.003:
            return None

        # Check if bouncing up from VWAP
        recent = list(data.price_history)[-5:]
        if recent[-1] > vwap and recent[-2] <= vwap and data.ema_9 > data.ema_21:
            hot = self._calc_hot_score(data, SetupType.VWAP_BOUNCE, "CALL")
            if hot >= self.config.signals.hot_score_minimum:
                return Signal(
                    symbol=data.symbol,
                    direction="CALL",
                    setup=SetupType.VWAP_BOUNCE,
                    hot_score=hot,
                    entry_price=price,
                    stop_price=vwap * 0.995,
                    reason=f"VWAP bounce at ${vwap:.2f}"
                )

        # Check if rejecting down from VWAP
        if recent[-1] < vwap and recent[-2] >= vwap and data.ema_9 < data.ema_21:
            hot = self._calc_hot_score(data, SetupType.VWAP_BOUNCE, "PUT")
            if hot >= self.config.signals.hot_score_minimum:
                return Signal(
                    symbol=data.symbol,
                    direction="PUT",
                    setup=SetupType.VWAP_BOUNCE,
                    hot_score=hot,
                    entry_price=price,
                    stop_price=vwap * 1.005,
                    reason=f"VWAP reject at ${vwap:.2f}"
                )

        return None

    def _check_pullback(self, data: StockData, now: datetime) -> Optional[Signal]:
        """Pullback to EMA 9 in a trend"""
        if data.ema_9 <= 0 or data.ema_21 <= 0:
            return None

        price = data.current_price
        distance_to_ema9 = abs(price - data.ema_9) / data.ema_9

        # Must be near EMA 9 (within 0.2%)
        if distance_to_ema9 > 0.002:
            return None

        # Uptrend pullback: EMA9 > EMA21, price near EMA9
        if data.ema_9 > data.ema_21 and price >= data.ema_9 * 0.998:
            hot = self._calc_hot_score(data, SetupType.PULLBACK_CONTINUATION, "CALL")
            if hot >= self.config.signals.hot_score_minimum:
                return Signal(
                    symbol=data.symbol,
                    direction="CALL",
                    setup=SetupType.PULLBACK_CONTINUATION,
                    hot_score=hot,
                    entry_price=price,
                    stop_price=data.ema_21 * 0.998,
                    reason=f"Pullback to EMA9 ${data.ema_9:.2f}"
                )

        # Downtrend pullback: EMA9 < EMA21, price near EMA9
        if data.ema_9 < data.ema_21 and price <= data.ema_9 * 1.002:
            hot = self._calc_hot_score(data, SetupType.PULLBACK_CONTINUATION, "PUT")
            if hot >= self.config.signals.hot_score_minimum:
                return Signal(
                    symbol=data.symbol,
                    direction="PUT",
                    setup=SetupType.PULLBACK_CONTINUATION,
                    hot_score=hot,
                    entry_price=price,
                    stop_price=data.ema_21 * 1.002,
                    reason=f"Pullback to EMA9 ${data.ema_9:.2f}"
                )

        return None

    def _check_break_retest(self, data: StockData, now: datetime) -> Optional[Signal]:
        """Break and retest of key level"""
        price = data.current_price

        # Check prior day high retest
        if data.prior_day_high > 0:
            dist = abs(price - data.prior_day_high) / data.prior_day_high
            if dist < 0.002 and price > data.prior_day_high and data.ema_9 > data.ema_21:
                hot = self._calc_hot_score(data, SetupType.BREAK_AND_RETEST, "CALL")
                if hot >= self.config.signals.hot_score_minimum:
                    return Signal(
                        symbol=data.symbol,
                        direction="CALL",
                        setup=SetupType.BREAK_AND_RETEST,
                        hot_score=hot,
                        entry_price=price,
                        stop_price=data.prior_day_high * 0.997,
                        reason=f"Retest PDH ${data.prior_day_high:.2f}"
                    )

        # Check prior day low retest
        if data.prior_day_low > 0:
            dist = abs(price - data.prior_day_low) / data.prior_day_low
            if dist < 0.002 and price < data.prior_day_low and data.ema_9 < data.ema_21:
                hot = self._calc_hot_score(data, SetupType.BREAK_AND_RETEST, "PUT")
                if hot >= self.config.signals.hot_score_minimum:
                    return Signal(
                        symbol=data.symbol,
                        direction="PUT",
                        setup=SetupType.BREAK_AND_RETEST,
                        hot_score=hot,
                        entry_price=price,
                        stop_price=data.prior_day_low * 1.003,
                        reason=f"Retest PDL ${data.prior_day_low:.2f}"
                    )

        return None

    # ==================== HOT SCORE ====================

    def _calc_hot_score(self, data: StockData, setup: str, direction: str) -> int:
        """Calculate HOT score (0-100)"""
        w = self.config.hot_weights
        score = 0

        # 1. Regime (25 pts)
        if self.regime == MarketRegime.TREND:
            score += w.regime
        elif self.regime == MarketRegime.MIXED:
            score += 10

        # 2. Setup quality (20 pts)
        score += w.setup_quality  # Full points if setup detected

        # 3. Relative volume (15 pts)
        if data.average_volume > 0 and data.current_volume > 0:
            rvol = data.current_volume / max(data.average_volume, 1)
            if rvol >= 2.0:
                score += w.rvol
            elif rvol >= 1.5:
                score += int(w.rvol * 0.7)
            elif rvol >= 1.0:
                score += int(w.rvol * 0.4)

        # 4. Trend alignment (15 pts)
        if data.ema_9 > 0 and data.ema_21 > 0:
            if direction == "CALL" and data.ema_9 > data.ema_21:
                score += w.trend_alignment
            elif direction == "PUT" and data.ema_9 < data.ema_21:
                score += w.trend_alignment

        # 5. VWAP position (10 pts)
        if data.vwap > 0:
            if direction == "CALL" and data.current_price > data.vwap:
                score += w.vwap_position
            elif direction == "PUT" and data.current_price < data.vwap:
                score += w.vwap_position

        # 6. Spread quality (10 pts)
        if data.bid > 0 and data.ask > 0:
            spread_pct = (data.ask - data.bid) / data.ask
            if spread_pct < 0.02:
                score += w.spread_quality
            elif spread_pct < 0.05:
                score += int(w.spread_quality * 0.6)

        # 7. Time of day (5 pts)
        now = datetime.now(ET)
        if 9 <= now.hour <= 10:
            score += w.time_of_day  # First hour bonus
        elif now.hour >= 15:
            score += w.time_of_day  # Power hour bonus
        else:
            score += 3

        return min(score, 100)

    # ==================== CONFIRMATION ====================

    def _confirm_signal(self, signal: Signal) -> Optional[Signal]:
        """
        15-second confirmation: signal must hold for 3 checks.
        Since we poll every ~10 sec, we track across scans.
        """
        key = f"{signal.symbol}_{signal.direction}_{signal.setup}"

        if key in self._pending_signals:
            pending = self._pending_signals[key]
            pending["checks"] += 1
            pending["last_check"] = datetime.now()

            if pending["checks"] >= self.config.signals.confirmation_checks:
                # Confirmed!
                del self._pending_signals[key]
                logger.info(
                    f"✅ CONFIRMED: {signal.symbol} {signal.direction} "
                    f"{signal.setup} HOT:{signal.hot_score}"
                )
                return signal
        else:
            # Start tracking
            self._pending_signals[key] = {
                "signal": signal,
                "checks": 1,
                "first_check": datetime.now(),
                "last_check": datetime.now()
            }

        # Clean old pending signals (>60 sec old)
        stale = []
        now = datetime.now()
        for k, v in self._pending_signals.items():
            if (now - v["first_check"]).total_seconds() > 60:
                stale.append(k)
        for k in stale:
            del self._pending_signals[k]

        return None

    # ==================== HELPERS ====================

    @staticmethod
    def _calc_ema(prices: list, period: int) -> float:
        """Calculate EMA from price list"""
        if len(prices) < period:
            return 0.0
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        return ema

    def get_regime(self) -> str:
        return self.regime

    def reset_daily(self):
        """Reset daily tracking"""
        for sym, data in self.stock_data.items():
            data.vwap_crosses = 0
            data.last_vwap_side = ""
            data.cum_volume = 0
            data.cum_vol_price = 0
            data.opening_range_set = False
            data.or_start_time = None
            data.or_prices = []
            data.tick_count = 0
            data.price_history.clear()
        self._pending_signals.clear()
        self.regime = MarketRegime.UNKNOWN
        logger.info("🔄 Daily reset complete")
