"""
PROJECT HOPE V2 - Market Analyzer
Real-time analysis using WebSocket tick data with multi-timeframe confirmation,
proper candle-based indicators, and institutional-grade signal generation
"""

import logging
import math
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from config import (
    Config, MarketRegime, SetupType, WATCHLIST,
    NEGATIVE_NEWS_KEYWORDS, POSITIVE_NEWS_KEYWORDS
)
from streaming_client import StreamingClient, CandleBar, Tick
from tradier_client import TradierClient

logger = logging.getLogger(__name__)


@dataclass
class StockData:
    """Accumulated analysis data for a single stock"""
    symbol: str
    
    # Real-time from WebSocket
    current_price: float = 0.0
    current_volume: int = 0
    average_volume: int = 0
    tick_count: int = 0
    
    # Indicators calculated from real candles
    ema_9: float = 0.0
    ema_21: float = 0.0
    vwap: float = 0.0
    vwap_upper: float = 0.0   # VWAP + 1 std dev
    vwap_lower: float = 0.0   # VWAP - 1 std dev
    
    # VWAP tracking for regime
    vwap_crosses: int = 0
    last_vwap_side: str = ""  # "above" or "below"
    
    # Key levels
    opening_range_high: float = 0.0
    opening_range_low: float = 0.0
    opening_range_set: bool = False
    or_start_time: Optional[datetime] = None
    
    prior_day_high: float = 0.0
    prior_day_low: float = 0.0
    prior_day_close: float = 0.0
    day_open: float = 0.0
    day_high: float = 0.0
    day_low: float = 0.0
    
    # Multi-timeframe EMAs (NEW)
    ema_9_5min: float = 0.0
    ema_21_5min: float = 0.0
    
    # Volume analysis
    volume_bars: deque = field(default_factory=lambda: deque(maxlen=20))
    
    # IV rank (NEW)
    iv_rank: float = 50.0
    iv_rank_updated: Optional[datetime] = None
    
    # Greeks quality from last option scan
    greeks_score: float = 0.0


@dataclass
class Signal:
    """Trading signal with full context"""
    symbol: str
    side: str  # "CALL" or "PUT"
    setup_type: str
    hot_score: int
    entry_price: float
    stop_price: float
    target_price: float
    trigger_level: str
    timestamp: datetime = field(default_factory=datetime.now)
    confirmation_count: int = 0
    
    # Multi-timeframe alignment (NEW)
    tf_1min_aligned: bool = False
    tf_5min_aligned: bool = False
    
    # Greeks context (NEW)
    iv_rank: float = 50.0
    greeks_score: float = 0.0


class MarketAnalyzer:
    """
    V2 Market Analyzer
    Uses real WebSocket candles instead of polling snapshots
    Multi-timeframe confirmation
    Proper VWAP with standard deviation bands
    """
    
    def __init__(self, config: Config, client: TradierClient, 
                 streamer: StreamingClient):
        self.config = config
        self.client = client
        self.streamer = streamer
        
        # Market regime
        self.market_regime = MarketRegime.UNKNOWN
        self.spy_vwap_crosses = 0
        
        # Stock data cache
        self.stock_data: Dict[str, StockData] = {}
        
        # Pending signals for confirmation
        self.pending_signals: Dict[str, Signal] = {}
        
        # VWAP calculation accumulators
        self._vwap_pv: Dict[str, float] = {}  # sum(price * volume)
        self._vwap_vol: Dict[str, float] = {}  # sum(volume)
        self._vwap_pv2: Dict[str, float] = {}  # sum(price^2 * volume) for std dev
        
        self.trading_day_date: Optional[datetime.date] = None
    
    def initialize(self, symbols: List[str] = None):
        symbols = symbols or WATCHLIST
        for symbol in symbols:
            if symbol not in self.stock_data:
                self.stock_data[symbol] = StockData(symbol=symbol)
                self._vwap_pv[symbol] = 0
                self._vwap_vol[symbol] = 0
                self._vwap_pv2[symbol] = 0
        
        if "SPY" not in self.stock_data:
            self.stock_data["SPY"] = StockData(symbol="SPY")
        
        logger.info(f"📊 Initialized V2 analyzer for {len(self.stock_data)} symbols")
    
    def reset_daily_data(self):
        today = datetime.now().date()
        if self.trading_day_date != today:
            self.trading_day_date = today
            for symbol, data in self.stock_data.items():
                data.vwap_crosses = 0
                data.last_vwap_side = ""
                data.opening_range_set = False
                data.opening_range_high = 0
                data.opening_range_low = 0
                data.or_start_time = None
                data.tick_count = 0
                data.day_high = 0
                data.day_low = 0
                data.day_open = 0
                data.ema_9 = 0
                data.ema_21 = 0
                data.ema_9_5min = 0
                data.ema_21_5min = 0
                data.vwap = 0
                data.vwap_upper = 0
                data.vwap_lower = 0
                data.volume_bars.clear()
                self._vwap_pv[symbol] = 0
                self._vwap_vol[symbol] = 0
                self._vwap_pv2[symbol] = 0
            
            self.market_regime = MarketRegime.UNKNOWN
            self.spy_vwap_crosses = 0
            self.pending_signals.clear()
            logger.info(f"🔄 Reset daily data for {today}")

    # ==================== REAL-TIME DATA PROCESSING ====================
    
    def on_tick(self, tick: Tick):
        """Process incoming tick from WebSocket"""
        symbol = tick.symbol
        data = self.stock_data.get(symbol)
        if not data:
            return
        
        price = tick.price
        data.current_price = price
        data.current_volume = tick.volume
        data.tick_count += 1
        
        # Set day open
        if data.day_open == 0:
            data.day_open = price
        
        # Update day high/low
        if price > data.day_high or data.day_high == 0:
            data.day_high = price
        if price < data.day_low or data.day_low == 0:
            data.day_low = price
        
        # Update VWAP with real tick data
        self._update_vwap_tick(symbol, price, tick.size)
        
        # Check VWAP cross
        self._check_vwap_cross(data, price)
    
    def on_summary(self, symbol: str, summary: dict):
        """Process daily summary from WebSocket"""
        data = self.stock_data.get(symbol)
        if not data:
            return
        
        if summary.get("open", 0) > 0:
            data.day_open = summary["open"]
        if summary.get("high", 0) > 0:
            data.day_high = summary["high"]
        if summary.get("low", 0) > 0:
            data.day_low = summary["low"]
        if summary.get("prev_close", 0) > 0:
            data.prior_day_close = summary["prev_close"]
    
    def on_candle(self, candle: CandleBar):
        """Process completed 1-minute candle"""
        symbol = candle.symbol
        data = self.stock_data.get(symbol)
        if not data:
            return
        
        # Update EMAs from real candles
        self._update_ema_from_candle(data, candle.close, "1min")
        
        # Update opening range from real candle data
        self._update_opening_range_candle(data, candle)
        
        # Store volume bar
        data.volume_bars.append(candle.volume)
        
        # Update regime
        if symbol == "SPY":
            self._update_market_regime()
    
    def update_from_stream(self):
        """
        Pull latest data from streamer and update all indicators
        Called periodically from trading engine
        """
        for symbol, data in self.stock_data.items():
            # Get latest price from stream
            price = self.streamer.get_latest_price(symbol)
            if price > 0:
                data.current_price = price
                data.tick_count = self.streamer.get_tick_count(symbol)
                data.current_volume = self.streamer.get_cumulative_volume(symbol)
            
            # Get summary data (prior day, open, high, low)
            summary = self.streamer.get_summary(symbol)
            if summary:
                if summary.get("prev_close", 0) > 0:
                    data.prior_day_close = summary["prev_close"]
                    if data.prior_day_high == 0:
                        data.prior_day_high = summary.get("high", 0)
                    if data.prior_day_low == 0:
                        data.prior_day_low = summary.get("low", 0)
            
            # Update EMAs from 1-min candles
            candles_1m = self.streamer.get_1min_candles(symbol, 30)
            if candles_1m:
                self._recalculate_emas(data, candles_1m, "1min")
            
            # Update EMAs from 5-min candles (multi-timeframe)
            candles_5m = self.streamer.get_5min_candles(symbol, 30)
            if candles_5m:
                self._recalculate_emas(data, candles_5m, "5min")
            
            # Update opening range from real candles
            if not data.opening_range_set and candles_1m:
                self._build_opening_range(data, candles_1m)
        
        # Update regime
        self._update_market_regime()
    
    def _update_vwap_tick(self, symbol: str, price: float, size: int):
        """Update VWAP with tick-level data (proper calculation)"""
        if size <= 0:
            size = 1
        
        self._vwap_pv[symbol] = self._vwap_pv.get(symbol, 0) + (price * size)
        self._vwap_vol[symbol] = self._vwap_vol.get(symbol, 0) + size
        self._vwap_pv2[symbol] = self._vwap_pv2.get(symbol, 0) + (price * price * size)
        
        data = self.stock_data.get(symbol)
        if data and self._vwap_vol[symbol] > 0:
            data.vwap = self._vwap_pv[symbol] / self._vwap_vol[symbol]
            
            # VWAP standard deviation bands
            variance = (self._vwap_pv2[symbol] / self._vwap_vol[symbol]) - (data.vwap ** 2)
            if variance > 0:
                std_dev = math.sqrt(variance)
                data.vwap_upper = data.vwap + std_dev
                data.vwap_lower = data.vwap - std_dev
    
    def _recalculate_emas(self, data: StockData, candles: List[CandleBar], 
                          timeframe: str):
        """Recalculate EMAs from candle series"""
        if len(candles) < 2:
            return
        
        closes = [c.close for c in candles]
        
        # Calculate EMA 9
        ema_9 = closes[0]
        mult_9 = 2 / (9 + 1)
        for price in closes[1:]:
            ema_9 = (price * mult_9) + (ema_9 * (1 - mult_9))
        
        # Calculate EMA 21
        ema_21 = closes[0]
        mult_21 = 2 / (21 + 1)
        for price in closes[1:]:
            ema_21 = (price * mult_21) + (ema_21 * (1 - mult_21))
        
        if timeframe == "1min":
            data.ema_9 = ema_9
            data.ema_21 = ema_21
        elif timeframe == "5min":
            data.ema_9_5min = ema_9
            data.ema_21_5min = ema_21
    
    def _update_ema_from_candle(self, data: StockData, close: float, 
                                 timeframe: str):
        """Update EMA incrementally from a new candle close"""
        mult_9 = 2 / (9 + 1)
        mult_21 = 2 / (21 + 1)
        
        if timeframe == "1min":
            if data.ema_9 == 0:
                data.ema_9 = close
                data.ema_21 = close
            else:
                data.ema_9 = (close * mult_9) + (data.ema_9 * (1 - mult_9))
                data.ema_21 = (close * mult_21) + (data.ema_21 * (1 - mult_21))
    
    def _build_opening_range(self, data: StockData, candles: List[CandleBar]):
        """Build opening range from first N minutes of 1-min candles"""
        if data.opening_range_set:
            return
        
        or_minutes = self.config.trading.opening_range_minutes
        now = datetime.now()
        
        # Filter candles to first 15 minutes after 9:30
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        or_end = market_open + timedelta(minutes=or_minutes)
        
        if now < or_end:
            return  # Still forming
        
        or_candles = [c for c in candles 
                      if market_open <= c.timestamp < or_end]
        
        if len(or_candles) >= 3:  # Need at least 3 candles
            data.opening_range_high = max(c.high for c in or_candles)
            data.opening_range_low = min(c.low for c in or_candles)
            data.opening_range_set = True
            logger.info(
                f"📊 {data.symbol} Opening Range: "
                f"${data.opening_range_high:.2f} - ${data.opening_range_low:.2f}"
            )
    
    def _update_opening_range_candle(self, data: StockData, candle: CandleBar):
        """Update opening range with each new candle"""
        if data.opening_range_set:
            return
        
        now = datetime.now()
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        or_end = market_open + timedelta(minutes=self.config.trading.opening_range_minutes)
        
        if candle.timestamp < market_open or candle.timestamp >= or_end:
            return
        
        # Track forming range
        if data.opening_range_high == 0 or candle.high > data.opening_range_high:
            data.opening_range_high = candle.high
        if data.opening_range_low == 0 or candle.low < data.opening_range_low:
            data.opening_range_low = candle.low
        
        if data.or_start_time is None:
            data.or_start_time = candle.timestamp
    
    def _check_vwap_cross(self, data: StockData, price: float):
        """Track VWAP crosses"""
        if data.vwap <= 0:
            return
        
        current_side = "above" if price > data.vwap else "below"
        
        if data.last_vwap_side and current_side != data.last_vwap_side:
            data.vwap_crosses += 1
        
        data.last_vwap_side = current_side
    
    def _update_market_regime(self):
        """Update market regime from SPY VWAP crosses"""
        spy_data = self.stock_data.get("SPY")
        if not spy_data or spy_data.tick_count < 10:
            return
        
        crosses = spy_data.vwap_crosses
        self.spy_vwap_crosses = crosses
        
        old_regime = self.market_regime
        
        if crosses <= 2:
            self.market_regime = MarketRegime.TREND
        elif crosses == 3:
            self.market_regime = MarketRegime.MIXED
        else:
            self.market_regime = MarketRegime.CHOP
        
        if old_regime != self.market_regime and old_regime != MarketRegime.UNKNOWN:
            logger.info(f"📊 Regime change: {old_regime} → {self.market_regime} ({crosses} crosses)")

    # ==================== SIGNAL GENERATION ====================
    
    def scan_for_signals(self) -> List[Signal]:
        """Scan all symbols for trade setups"""
        signals = []
        
        if self.market_regime != MarketRegime.TREND:
            return signals
        
        for symbol, data in self.stock_data.items():
            if symbol == "SPY" and symbol not in WATCHLIST[:3]:
                continue  # SPY is for regime only unless in watchlist
            
            if data.tick_count < self.config.trading.min_ticks_before_signals:
                continue
            
            if data.current_price <= 0:
                continue
            
            # Check each setup type
            for setup_fn in [
                self._check_opening_range_break,
                self._check_vwap_bounce,
                self._check_pullback,
                self._check_break_retest,
            ]:
                signal = setup_fn(data)
                if signal:
                    # Add multi-timeframe context
                    signal.tf_1min_aligned = self._check_1min_alignment(data, signal.side)
                    signal.tf_5min_aligned = self._check_5min_alignment(data, signal.side)
                    signal.iv_rank = data.iv_rank
                    signals.append(signal)
                    break  # One signal per symbol
        
        return signals
    
    def _check_1min_alignment(self, data: StockData, side: str) -> bool:
        """Check if 1-minute trend aligns with signal"""
        if data.ema_9 == 0 or data.ema_21 == 0:
            return True  # No data = assume aligned
        if side == "CALL":
            return data.ema_9 > data.ema_21
        return data.ema_9 < data.ema_21
    
    def _check_5min_alignment(self, data: StockData, side: str) -> bool:
        """Check if 5-minute trend aligns with signal"""
        if data.ema_9_5min == 0 or data.ema_21_5min == 0:
            return True
        if side == "CALL":
            return data.ema_9_5min > data.ema_21_5min
        return data.ema_9_5min < data.ema_21_5min
    
    def _check_opening_range_break(self, data: StockData) -> Optional[Signal]:
        """Opening Range Breakout using real candle data"""
        if not data.opening_range_set:
            return None
        
        price = data.current_price
        or_high = data.opening_range_high
        or_low = data.opening_range_low
        or_range = or_high - or_low
        
        if or_range <= 0:
            return None
        
        # Break above with volume
        if price > or_high * 1.001:
            rvol = data.current_volume / max(data.average_volume, 1)
            if rvol >= 1.0:
                return Signal(
                    symbol=data.symbol,
                    side="CALL",
                    setup_type=SetupType.OPENING_RANGE_BREAK,
                    hot_score=0,
                    entry_price=price,
                    stop_price=or_low,
                    target_price=price + or_range,
                    trigger_level=f"ORB High ${or_high:.2f}"
                )
        
        # Break below with volume
        elif price < or_low * 0.999:
            rvol = data.current_volume / max(data.average_volume, 1)
            if rvol >= 1.0:
                return Signal(
                    symbol=data.symbol,
                    side="PUT",
                    setup_type=SetupType.OPENING_RANGE_BREAK,
                    hot_score=0,
                    entry_price=price,
                    stop_price=or_high,
                    target_price=price - or_range,
                    trigger_level=f"ORB Low ${or_low:.2f}"
                )
        
        return None
    
    def _check_vwap_bounce(self, data: StockData) -> Optional[Signal]:
        """VWAP Bounce/Reject using proper VWAP with bands"""
        price = data.current_price
        vwap = data.vwap
        
        if vwap <= 0 or data.ema_9 == 0:
            return None
        
        distance_pct = abs(price - vwap) / vwap
        
        # Must be near VWAP (within 0.3%)
        if distance_pct > 0.003:
            return None
        
        # CALL: Price bouncing up off VWAP in uptrend
        if (price > vwap and data.ema_9 > data.ema_21 
            and data.current_price > data.day_open):
            return Signal(
                symbol=data.symbol,
                side="CALL",
                setup_type=SetupType.VWAP_BOUNCE,
                hot_score=0,
                entry_price=price,
                stop_price=data.vwap_lower if data.vwap_lower > 0 else vwap * 0.998,
                target_price=price * 1.02,
                trigger_level=f"VWAP Bounce ${vwap:.2f}"
            )
        
        # PUT: Price rejecting down from VWAP in downtrend
        elif (price < vwap and data.ema_9 < data.ema_21
              and data.current_price < data.day_open):
            return Signal(
                symbol=data.symbol,
                side="PUT",
                setup_type=SetupType.VWAP_BOUNCE,
                hot_score=0,
                entry_price=price,
                stop_price=data.vwap_upper if data.vwap_upper > 0 else vwap * 1.002,
                target_price=price * 0.98,
                trigger_level=f"VWAP Reject ${vwap:.2f}"
            )
        
        return None
    
    def _check_pullback(self, data: StockData) -> Optional[Signal]:
        """EMA Pullback Continuation"""
        price = data.current_price
        ema_9 = data.ema_9
        ema_21 = data.ema_21
        
        if ema_9 == 0 or ema_21 == 0:
            return None
        
        distance_to_9 = abs(price - ema_9) / ema_9
        
        # CALL: Uptrend, pullback to EMA 9
        if (ema_9 > ema_21 and distance_to_9 < 0.002
            and price >= ema_9 * 0.998):
            return Signal(
                symbol=data.symbol,
                side="CALL",
                setup_type=SetupType.PULLBACK_CONTINUATION,
                hot_score=0,
                entry_price=price,
                stop_price=ema_21 * 0.998,
                target_price=price * 1.02,
                trigger_level=f"EMA9 Pullback ${ema_9:.2f}"
            )
        
        # PUT: Downtrend, pullback up to EMA 9
        elif (ema_9 < ema_21 and distance_to_9 < 0.002
              and price <= ema_9 * 1.002):
            return Signal(
                symbol=data.symbol,
                side="PUT",
                setup_type=SetupType.PULLBACK_CONTINUATION,
                hot_score=0,
                entry_price=price,
                stop_price=ema_21 * 1.002,
                target_price=price * 0.98,
                trigger_level=f"EMA9 Reject ${ema_9:.2f}"
            )
        
        return None
    
    def _check_break_retest(self, data: StockData) -> Optional[Signal]:
        """Break and Retest of key levels"""
        price = data.current_price
        levels = self._get_key_levels(data)
        
        for level_name, level_price in levels.items():
            if level_price == 0:
                continue
            
            distance_pct = abs(price - level_price) / level_price
            if distance_pct > 0.003:
                continue
            
            if price > level_price and data.ema_9 > data.ema_21:
                return Signal(
                    symbol=data.symbol,
                    side="CALL",
                    setup_type=SetupType.BREAK_AND_RETEST,
                    hot_score=0,
                    entry_price=price,
                    stop_price=level_price * 0.995,
                    target_price=price * 1.02,
                    trigger_level=f"Retest {level_name} ${level_price:.2f}"
                )
            elif price < level_price and data.ema_9 < data.ema_21:
                return Signal(
                    symbol=data.symbol,
                    side="PUT",
                    setup_type=SetupType.BREAK_AND_RETEST,
                    hot_score=0,
                    entry_price=price,
                    stop_price=level_price * 1.005,
                    target_price=price * 0.98,
                    trigger_level=f"Retest {level_name} ${level_price:.2f}"
                )
        
        return None
    
    def _get_key_levels(self, data: StockData) -> Dict[str, float]:
        """Get key price levels"""
        levels = {}
        
        if data.prior_day_high > 0:
            levels["PDH"] = data.prior_day_high
        if data.prior_day_low > 0:
            levels["PDL"] = data.prior_day_low
        if data.prior_day_close > 0:
            levels["PDC"] = data.prior_day_close
        if data.opening_range_set:
            levels["ORH"] = data.opening_range_high
            levels["ORL"] = data.opening_range_low
        if data.vwap > 0:
            levels["VWAP"] = data.vwap
        
        price = data.current_price
        if price > 0:
            whole = round(price)
            levels[f"${whole}"] = float(whole)
            half = round(price * 2) / 2
            if half != whole:
                levels[f"${half:.2f}"] = half
        
        return levels

    # ==================== HOT SCORE ====================
    
    def calculate_hot_score(self, signal: Signal) -> int:
        """Calculate HOT score with multi-timeframe and Greeks"""
        score = 0
        weights = self.config.weights
        data = self.stock_data.get(signal.symbol)
        
        if not data:
            return 0
        
        # 1. RVOL - up to 25 points
        if data.average_volume > 0 and data.current_volume > 0:
            rvol = data.current_volume / data.average_volume
            if rvol >= 3.0:
                score += weights.rvol_max_points
            elif rvol >= 2.0:
                score += int(weights.rvol_max_points * 0.8)
            elif rvol >= 1.5:
                score += int(weights.rvol_max_points * 0.6)
            elif rvol >= 1.0:
                score += int(weights.rvol_max_points * 0.3)
        
        # 2. Near Key Level - 15 points
        levels = self._get_key_levels(data)
        price = data.current_price
        for level_price in levels.values():
            if level_price > 0:
                distance = abs(price - level_price) / level_price
                if distance < 0.005:
                    score += weights.key_level_points
                    break
        
        # 3. TREND Regime - 15 points
        if self.market_regime == MarketRegime.TREND:
            score += weights.trend_regime_points
        
        # 4. Volume Spike - 10 points
        if len(data.volume_bars) >= 2:
            avg_vol = sum(data.volume_bars) / len(data.volume_bars)
            if avg_vol > 0 and data.current_volume >= avg_vol * 2:
                score += weights.volume_spike_points
        
        # 5. Bid-Ask Spread quality - 10 points
        spread = self.streamer.get_spread_pct(signal.symbol)
        if spread < 0.02:
            score += weights.good_spread_points
        elif spread < 0.05:
            score += int(weights.good_spread_points * 0.6)
        
        # 6. Greeks Quality - 15 points (NEW)
        if data.greeks_score > 0:
            score += int(weights.greeks_quality_points * min(1, data.greeks_score / 80))
        else:
            score += 8  # Default if not yet analyzed
        
        # 7. Multi-Timeframe Alignment - 10 points (NEW)
        tf_score = 0
        if signal.tf_1min_aligned:
            tf_score += 5
        if signal.tf_5min_aligned:
            tf_score += 5
        score += tf_score
        
        return min(100, score)

    # ==================== SIGNAL CONFIRMATION ====================
    
    def confirm_signal(self, signal: Signal) -> bool:
        """15-second signal confirmation"""
        key = f"{signal.symbol}_{signal.side}_{signal.setup_type}"
        
        if key in self.pending_signals:
            pending = self.pending_signals[key]
            data = self.stock_data.get(signal.symbol)
            if not data:
                del self.pending_signals[key]
                return False
            
            price = data.current_price
            
            if signal.side == "CALL" and price < pending.entry_price * 0.998:
                logger.info(f"❌ {signal.symbol} CALL invalidated - price dropped")
                del self.pending_signals[key]
                return False
            
            if signal.side == "PUT" and price > pending.entry_price * 1.002:
                logger.info(f"❌ {signal.symbol} PUT invalidated - price rose")
                del self.pending_signals[key]
                return False
            
            pending.confirmation_count += 1
            
            if pending.confirmation_count >= self.config.trading.confirmation_checks:
                logger.info(f"✅ {signal.symbol} {signal.side} CONFIRMED after {pending.confirmation_count} checks")
                del self.pending_signals[key]
                return True
            
            logger.info(f"⏳ {signal.symbol} {signal.side} confirmation {pending.confirmation_count}/{self.config.trading.confirmation_checks}")
            return False
        else:
            signal.confirmation_count = 1
            self.pending_signals[key] = signal
            logger.info(f"🔍 {signal.symbol} {signal.side} signal detected - confirming...")
            return False
    
    def clear_pending_signals(self, symbol: str = None):
        if symbol:
            keys_to_remove = [k for k in self.pending_signals if k.startswith(symbol)]
            for key in keys_to_remove:
                del self.pending_signals[key]
        else:
            self.pending_signals.clear()

    # ==================== GETTERS ====================
    
    def get_regime(self) -> str:
        return self.market_regime
    
    def is_trending(self) -> bool:
        return self.market_regime == MarketRegime.TREND
    
    def get_stock_data(self, symbol: str) -> Optional[StockData]:
        return self.stock_data.get(symbol)
    
    def has_enough_data(self, symbol: str = "SPY") -> bool:
        data = self.stock_data.get(symbol)
        if not data:
            return False
        return data.tick_count >= self.config.trading.min_ticks_before_signals
    
    def update_iv_rank(self, symbol: str, iv_rank: float):
        """Update IV rank for a symbol"""
        data = self.stock_data.get(symbol)
        if data:
            data.iv_rank = iv_rank
            data.iv_rank_updated = datetime.now()
    
    def update_greeks_score(self, symbol: str, score: float):
        """Update Greeks quality score"""
        data = self.stock_data.get(symbol)
        if data:
            data.greeks_score = score
