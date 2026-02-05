"""
PROJECT HOPE - Market Analyzer
Handles market regime detection, technical analysis, and signal generation
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics

from config import (
    Config, MarketRegime, SetupType, WATCHLIST,
    NEGATIVE_NEWS_KEYWORDS, POSITIVE_NEWS_KEYWORDS
)
from tradier_client import TradierClient

logger = logging.getLogger(__name__)


@dataclass
class PriceBar:
    """Single price bar"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: float = 0.0


@dataclass
class StockData:
    """Accumulated data for a single stock"""
    symbol: str
    bars: deque = field(default_factory=lambda: deque(maxlen=100))
    vwap_crosses: int = 0
    ema_9: float = 0.0
    ema_21: float = 0.0
    vwap: float = 0.0
    opening_range_high: float = 0.0
    opening_range_low: float = 0.0
    opening_range_set: bool = False
    prior_day_high: float = 0.0
    prior_day_low: float = 0.0
    premarket_high: float = 0.0
    premarket_low: float = 0.0
    current_price: float = 0.0
    current_volume: int = 0
    average_volume: int = 0
    tick_count: int = 0


@dataclass
class Signal:
    """Trading signal"""
    symbol: str
    side: str  # "CALL" or "PUT"
    setup_type: str  # From SetupType
    hot_score: int
    entry_price: float
    stop_price: float
    target_price: float
    trigger_level: str  # Description of what triggered
    timestamp: datetime = field(default_factory=datetime.now)
    confirmation_count: int = 0  # For 15-second confirmation


class MarketAnalyzer:
    """Analyzes market data and generates signals"""
    
    def __init__(self, config: Config, client: TradierClient):
        self.config = config
        self.client = client
        
        # Market regime (SPY-based)
        self.market_regime = MarketRegime.UNKNOWN
        self.spy_vwap_crosses = 0
        
        # Stock data cache
        self.stock_data: Dict[str, StockData] = {}
        
        # Pending signals (for confirmation)
        self.pending_signals: Dict[str, Signal] = {}
        
        # Trading state
        self.trading_day_date: Optional[datetime.date] = None
        
    def initialize(self, symbols: List[str] = None):
        """Initialize stock data structures"""
        symbols = symbols or WATCHLIST
        for symbol in symbols:
            if symbol not in self.stock_data:
                self.stock_data[symbol] = StockData(symbol=symbol)
        
        # Always include SPY for regime
        if "SPY" not in self.stock_data:
            self.stock_data["SPY"] = StockData(symbol="SPY")
        
        logger.info(f"📊 Initialized analyzer for {len(self.stock_data)} symbols")
    
    def reset_daily_data(self):
        """Reset data for new trading day"""
        today = datetime.now().date()
        if self.trading_day_date != today:
            self.trading_day_date = today
            for data in self.stock_data.values():
                data.bars.clear()
                data.vwap_crosses = 0
                data.opening_range_set = False
                data.opening_range_high = 0
                data.opening_range_low = 0
                data.tick_count = 0
            
            self.market_regime = MarketRegime.UNKNOWN
            self.spy_vwap_crosses = 0
            self.pending_signals.clear()
            
            logger.info(f"🔄 Reset daily data for {today}")
    
    # ==================== PRICE UPDATES ====================
    
    def update_prices(self, quotes: Dict[str, Dict]):
        """Update prices from quote data"""
        now = datetime.now()
        
        for symbol, quote in quotes.items():
            if symbol not in self.stock_data:
                continue
            
            data = self.stock_data[symbol]
            price = quote.get("last") or quote.get("close") or 0
            
            if price <= 0:
                continue
            
            # Update current values
            data.current_price = price
            data.current_volume = quote.get("volume", 0)
            data.average_volume = quote.get("average_volume", 0)
            data.tick_count += 1
            
            # Update prior day levels (from quote)
            if quote.get("close"):
                # These are approximations; ideally load from historical data
                if data.prior_day_high == 0:
                    data.prior_day_high = quote.get("high", price)
                    data.prior_day_low = quote.get("low", price)
            
            # Create price bar (simplified - in production use actual candle data)
            bar = PriceBar(
                timestamp=now,
                open=price,
                high=price,
                low=price,
                close=price,
                volume=quote.get("volume", 0)
            )
            data.bars.append(bar)
            
            # Update EMAs
            self._update_emas(data)
            
            # Update VWAP (simplified calculation)
            self._update_vwap(data)
            
            # Check for VWAP cross
            self._check_vwap_cross(data, price)
            
            # Set opening range (first 15 mins)
            self._update_opening_range(data, price)
        
        # Update market regime based on SPY
        self._update_market_regime()
    
    def _update_emas(self, data: StockData):
        """Update EMA 9 and EMA 21"""
        if len(data.bars) < 2:
            data.ema_9 = data.current_price
            data.ema_21 = data.current_price
            return
        
        # EMA multipliers
        mult_9 = 2 / (9 + 1)
        mult_21 = 2 / (21 + 1)
        
        price = data.current_price
        data.ema_9 = (price * mult_9) + (data.ema_9 * (1 - mult_9))
        data.ema_21 = (price * mult_21) + (data.ema_21 * (1 - mult_21))
    
    def _update_vwap(self, data: StockData):
        """Update VWAP (Volume Weighted Average Price)"""
        if len(data.bars) < 1:
            data.vwap = data.current_price
            return
        
        # Simplified VWAP: average of prices weighted by volume
        total_pv = 0
        total_vol = 0
        
        for bar in data.bars:
            if bar.volume > 0:
                typical_price = (bar.high + bar.low + bar.close) / 3
                total_pv += typical_price * bar.volume
                total_vol += bar.volume
        
        if total_vol > 0:
            data.vwap = total_pv / total_vol
        else:
            data.vwap = data.current_price
    
    def _check_vwap_cross(self, data: StockData, current_price: float):
        """Check for VWAP cross and count them"""
        if len(data.bars) < 2 or data.vwap == 0:
            return
        
        prev_price = data.bars[-2].close if len(data.bars) >= 2 else current_price
        
        # Cross up
        if prev_price < data.vwap and current_price > data.vwap:
            data.vwap_crosses += 1
        # Cross down
        elif prev_price > data.vwap and current_price < data.vwap:
            data.vwap_crosses += 1
    
    def _update_opening_range(self, data: StockData, price: float):
        """Set opening range from first 15 minutes"""
        now = datetime.now()
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        range_end = market_open + timedelta(minutes=15)
        
        if now < market_open:
            # Premarket
            if data.premarket_high == 0 or price > data.premarket_high:
                data.premarket_high = price
            if data.premarket_low == 0 or price < data.premarket_low:
                data.premarket_low = price
        elif now <= range_end and not data.opening_range_set:
            # During opening range formation
            if data.opening_range_high == 0 or price > data.opening_range_high:
                data.opening_range_high = price
            if data.opening_range_low == 0 or price < data.opening_range_low:
                data.opening_range_low = price
        elif now > range_end and not data.opening_range_set:
            # Opening range complete
            data.opening_range_set = True
            logger.info(f"📊 {data.symbol} Opening Range: ${data.opening_range_low:.2f} - ${data.opening_range_high:.2f}")
    
    def _update_market_regime(self):
        """Update market regime based on SPY VWAP crosses"""
        spy_data = self.stock_data.get("SPY")
        if not spy_data or spy_data.tick_count < self.config.trading.min_ticks_before_signals:
            self.market_regime = MarketRegime.UNKNOWN
            return
        
        old_regime = self.market_regime
        crosses = spy_data.vwap_crosses
        
        # Regime rules: 0-2 = TREND, 3 = MIXED, 4+ = CHOP
        if crosses <= 2:
            self.market_regime = MarketRegime.TREND
        elif crosses == 3:
            self.market_regime = MarketRegime.MIXED
        else:
            self.market_regime = MarketRegime.CHOP
        
        self.spy_vwap_crosses = crosses
        
        if old_regime != self.market_regime:
            logger.info(f"📈 Regime change: {old_regime} → {self.market_regime} (SPY crosses: {crosses})")
    
    # ==================== SIGNAL GENERATION ====================
    
    def scan_for_signals(self, symbols: List[str] = None) -> List[Signal]:
        """Scan watchlist for trading signals"""
        symbols = symbols or list(self.stock_data.keys())
        signals = []
        
        for symbol in symbols:
            if symbol == "SPY":  # Don't trade SPY directly (use for regime only)
                continue
            
            data = self.stock_data.get(symbol)
            if not data:
                continue
            
            # Need minimum ticks before generating signals
            if data.tick_count < self.config.trading.min_ticks_before_signals:
                continue
            
            # Check each setup type
            signal = self._check_setups(data)
            if signal:
                signals.append(signal)
        
        return signals
    
    def _check_setups(self, data: StockData) -> Optional[Signal]:
        """Check all setup types for a symbol"""
        # Setup 1: Opening Range Break
        signal = self._check_opening_range_break(data)
        if signal:
            return signal
        
        # Setup 2: VWAP Bounce
        signal = self._check_vwap_bounce(data)
        if signal:
            return signal
        
        # Setup 3: Pullback Continuation
        signal = self._check_pullback(data)
        if signal:
            return signal
        
        # Setup 4: Break and Retest
        signal = self._check_break_retest(data)
        if signal:
            return signal
        
        return None
    
    def _check_opening_range_break(self, data: StockData) -> Optional[Signal]:
        """Check for Opening Range Breakout setup"""
        if not data.opening_range_set:
            return None
        
        price = data.current_price
        range_high = data.opening_range_high
        range_low = data.opening_range_low
        
        if range_high == 0 or range_low == 0:
            return None
        
        range_size = range_high - range_low
        if range_size < 0.10:  # Range too tight
            return None
        
        # Break above range high = CALL
        if price > range_high * 1.001:  # Small buffer for noise
            return Signal(
                symbol=data.symbol,
                side="CALL",
                setup_type=SetupType.OPENING_RANGE_BREAK,
                hot_score=0,  # Will be calculated
                entry_price=price,
                stop_price=range_low,
                target_price=price + (range_size * 2),  # 2R target
                trigger_level=f"ORB High ${range_high:.2f}"
            )
        
        # Break below range low = PUT
        if price < range_low * 0.999:
            return Signal(
                symbol=data.symbol,
                side="PUT",
                setup_type=SetupType.OPENING_RANGE_BREAK,
                hot_score=0,
                entry_price=price,
                stop_price=range_high,
                target_price=price - (range_size * 2),
                trigger_level=f"ORB Low ${range_low:.2f}"
            )
        
        return None
    
    def _check_vwap_bounce(self, data: StockData) -> Optional[Signal]:
        """Check for VWAP Bounce/Reject setup"""
        if data.vwap == 0 or len(data.bars) < 5:
            return None
        
        price = data.current_price
        vwap = data.vwap
        
        # Price must be near VWAP (within 0.3%)
        distance_pct = abs(price - vwap) / vwap
        if distance_pct > 0.003:
            return None
        
        # Determine trend from EMAs
        uptrend = data.ema_9 > data.ema_21
        
        # Get recent price action (last 5 bars)
        recent_bars = list(data.bars)[-5:]
        if len(recent_bars) < 5:
            return None
        
        # Check for bounce pattern
        prices = [b.close for b in recent_bars]
        
        if uptrend and price > vwap:
            # Bullish bounce from VWAP in uptrend
            # Price should have come down to VWAP and bounced
            lowest = min(prices[:-1])
            if lowest <= vwap * 1.002 and price > lowest:
                return Signal(
                    symbol=data.symbol,
                    side="CALL",
                    setup_type=SetupType.VWAP_BOUNCE,
                    hot_score=0,
                    entry_price=price,
                    stop_price=vwap * 0.995,  # Stop just below VWAP
                    target_price=price * 1.02,  # 2% target
                    trigger_level=f"VWAP Bounce ${vwap:.2f}"
                )
        
        elif not uptrend and price < vwap:
            # Bearish reject from VWAP in downtrend
            highest = max(prices[:-1])
            if highest >= vwap * 0.998 and price < highest:
                return Signal(
                    symbol=data.symbol,
                    side="PUT",
                    setup_type=SetupType.VWAP_BOUNCE,
                    hot_score=0,
                    entry_price=price,
                    stop_price=vwap * 1.005,
                    target_price=price * 0.98,
                    trigger_level=f"VWAP Reject ${vwap:.2f}"
                )
        
        return None
    
    def _check_pullback(self, data: StockData) -> Optional[Signal]:
        """Check for EMA Pullback Continuation setup"""
        if data.ema_9 == 0 or data.ema_21 == 0:
            return None
        
        price = data.current_price
        ema_9 = data.ema_9
        ema_21 = data.ema_21
        
        # Check trend direction
        uptrend = ema_9 > ema_21
        
        if uptrend:
            # Price should be near/touching EMA 9 and bouncing
            distance_to_ema9 = (price - ema_9) / ema_9
            
            # Price pulled back to EMA 9 (within 0.2%) and above EMA 21
            if -0.002 <= distance_to_ema9 <= 0.003 and price > ema_21:
                return Signal(
                    symbol=data.symbol,
                    side="CALL",
                    setup_type=SetupType.PULLBACK_CONTINUATION,
                    hot_score=0,
                    entry_price=price,
                    stop_price=ema_21 * 0.998,  # Stop below EMA 21
                    target_price=price * 1.02,
                    trigger_level=f"EMA9 Bounce ${ema_9:.2f}"
                )
        else:
            # Downtrend pullback
            distance_to_ema9 = (ema_9 - price) / ema_9
            
            if -0.002 <= distance_to_ema9 <= 0.003 and price < ema_21:
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
        """Check for Break and Retest setup"""
        price = data.current_price
        
        # Check key levels
        levels = self._get_key_levels(data)
        
        for level_name, level_price in levels.items():
            if level_price == 0:
                continue
            
            # Check if price is retesting a broken level
            distance_pct = abs(price - level_price) / level_price
            
            if distance_pct > 0.003:  # Not near level
                continue
            
            # Determine if this was a break up or break down
            # by checking if price is above or below the level
            if price > level_price and data.ema_9 > data.ema_21:
                # Retesting broken resistance as support (bullish)
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
                # Retesting broken support as resistance (bearish)
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
        """Get key price levels for a symbol"""
        levels = {}
        
        # Prior day levels
        if data.prior_day_high > 0:
            levels["PDH"] = data.prior_day_high
        if data.prior_day_low > 0:
            levels["PDL"] = data.prior_day_low
        
        # Premarket levels
        if data.premarket_high > 0:
            levels["PMH"] = data.premarket_high
        if data.premarket_low > 0:
            levels["PML"] = data.premarket_low
        
        # Opening range
        if data.opening_range_set:
            levels["ORH"] = data.opening_range_high
            levels["ORL"] = data.opening_range_low
        
        # VWAP
        if data.vwap > 0:
            levels["VWAP"] = data.vwap
        
        # Whole dollar levels near current price
        price = data.current_price
        if price > 0:
            whole = round(price)
            levels[f"${whole}"] = float(whole)
            
            # Half dollar
            half = round(price * 2) / 2
            if half != whole:
                levels[f"${half:.2f}"] = half
        
        return levels
    
    # ==================== HOT SCORE ====================
    
    def calculate_hot_score(self, signal: Signal) -> int:
        """Calculate HOT score for a signal (0-100)"""
        score = 0
        weights = self.config.weights
        data = self.stock_data.get(signal.symbol)
        
        if not data:
            return 0
        
        # 1. RVOL (Relative Volume) - up to 30 points
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
        
        # 2. Near Key Level - 20 points
        levels = self._get_key_levels(data)
        price = data.current_price
        for level_price in levels.values():
            if level_price > 0:
                distance = abs(price - level_price) / level_price
                if distance < 0.005:  # Within 0.5%
                    score += weights.key_level_points
                    break
        
        # 3. TREND Regime - 20 points
        if self.market_regime == MarketRegime.TREND:
            score += weights.trend_regime_points
        
        # 4. Volume Spike (2x+) - 15 points
        if len(data.bars) >= 2:
            prev_vol = data.bars[-2].volume if len(data.bars) >= 2 else 0
            curr_vol = data.current_volume
            if prev_vol > 0 and curr_vol >= prev_vol * 2:
                score += weights.volume_spike_points
        
        # 5. Good Spread - 10 points
        # (Would need option quote to check; assume good for now)
        score += weights.good_spread_points
        
        # 6. Bullish News - 5 points
        # (Would need news API; placeholder)
        # score += weights.bullish_news_points
        
        return min(100, score)
    
    # ==================== SIGNAL CONFIRMATION ====================
    
    def confirm_signal(self, signal: Signal) -> bool:
        """
        Add signal to confirmation queue. 
        Returns True if signal has been confirmed (held for 3 checks).
        """
        key = f"{signal.symbol}_{signal.side}_{signal.setup_type}"
        
        if key in self.pending_signals:
            pending = self.pending_signals[key]
            
            # Check if signal still valid (price hasn't reversed)
            data = self.stock_data.get(signal.symbol)
            if not data:
                del self.pending_signals[key]
                return False
            
            price = data.current_price
            
            # For CALL, price must stay above trigger
            # For PUT, price must stay below trigger
            if signal.side == "CALL" and price < pending.entry_price * 0.998:
                logger.info(f"❌ {signal.symbol} CALL signal invalidated - price dropped")
                del self.pending_signals[key]
                return False
            
            if signal.side == "PUT" and price > pending.entry_price * 1.002:
                logger.info(f"❌ {signal.symbol} PUT signal invalidated - price rose")
                del self.pending_signals[key]
                return False
            
            # Signal still valid - increment confirmation
            pending.confirmation_count += 1
            
            if pending.confirmation_count >= self.config.trading.confirmation_checks:
                logger.info(f"✅ {signal.symbol} {signal.side} CONFIRMED after {pending.confirmation_count} checks")
                del self.pending_signals[key]
                return True
            
            logger.info(f"⏳ {signal.symbol} {signal.side} confirmation {pending.confirmation_count}/{self.config.trading.confirmation_checks}")
            return False
        else:
            # New signal - start confirmation
            signal.confirmation_count = 1
            self.pending_signals[key] = signal
            logger.info(f"🔍 {signal.symbol} {signal.side} signal detected - starting confirmation")
            return False
    
    def clear_pending_signals(self, symbol: str = None):
        """Clear pending signals for a symbol or all"""
        if symbol:
            keys_to_remove = [k for k in self.pending_signals if k.startswith(symbol)]
            for key in keys_to_remove:
                del self.pending_signals[key]
        else:
            self.pending_signals.clear()
    
    # ==================== GETTERS ====================
    
    def get_regime(self) -> str:
        """Get current market regime"""
        return self.market_regime
    
    def is_trending(self) -> bool:
        """Check if market is in TREND regime"""
        return self.market_regime == MarketRegime.TREND
    
    def get_stock_data(self, symbol: str) -> Optional[StockData]:
        """Get stock data for a symbol"""
        return self.stock_data.get(symbol)
    
    def has_enough_data(self, symbol: str = "SPY") -> bool:
        """Check if we have enough data to trade"""
        data = self.stock_data.get(symbol)
        if not data:
            return False
        return data.tick_count >= self.config.trading.min_ticks_before_signals
