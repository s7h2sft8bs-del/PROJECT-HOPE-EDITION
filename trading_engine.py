"""
PROJECT HOPE V2 - Trading Engine
WebSocket-powered trading engine with real-time data,
Greeks analysis, IV rank filtering, and multi-timeframe confirmation
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz

from config import Config, WATCHLIST, MarketRegime, NEGATIVE_NEWS_KEYWORDS
from tradier_client import TradierClient
from streaming_client import StreamingClient
from market_analyzer import MarketAnalyzer, Signal
from position_manager import PositionManager
from alert_service import AlertService

logger = logging.getLogger(__name__)

ET = pytz.timezone('US/Eastern')


class TradingEngine:
    """
    V2 Trading Engine
    - WebSocket streaming for real-time tick data
    - Greeks analysis on every trade
    - IV rank filtering
    - Multi-timeframe confirmation
    - Trailing stops after partials
    """
    
    def __init__(self, config: Config):
        self.config = config
        
        # Core components
        self.client = TradierClient(config.tradier)
        self.streamer = StreamingClient(config.tradier)
        self.analyzer = MarketAnalyzer(config, self.client, self.streamer)
        self.positions = PositionManager(config)
        self.alerts = AlertService(config.twilio)
        
        # State
        self.running = False
        self.current_date: Optional[datetime.date] = None
        self.in_trading_window = False
        self.last_window_state = False
        self.last_regime = MarketRegime.UNKNOWN
        
        # Account
        self.account_balance = 0.0
        
        # IV rank cache (updated periodically)
        self._iv_rank_cache: Dict[str, float] = {}
        self._last_iv_update = 0
        self._iv_update_interval = 300  # Update IV rank every 5 min
        
        # Position check timing
        self._last_position_check = 0
        self._option_quotes = {}
        
        # Stream health monitoring
        self._last_stream_check = 0
    
    def initialize(self) -> bool:
        """Initialize engine with WebSocket streaming"""
        logger.info("=" * 60)
        logger.info("🚀 PROJECT HOPE V2 - Initializing...")
        logger.info("=" * 60)
        
        # Validate config
        errors = self.config.validate()
        if errors:
            for err in errors:
                level = logging.ERROR if "TRADIER" in err else logging.WARNING
                logger.log(level, f"⚠️ Config: {err}")
        
        # Test Tradier connection
        if not self.client.test_connection():
            logger.error("❌ Failed to connect to Tradier")
            return False
        
        # Get account balance
        balance = self.client.get_account_balance()
        if balance:
            self.account_balance = balance.get("total_equity", 0)
            self.positions.set_daily_starting_balance(self.account_balance)
            logger.info(f"💰 Account Balance: ${self.account_balance:,.2f}")
        
        # Initialize analyzer
        self.analyzer.initialize(WATCHLIST)
        
        # Create streaming session
        if not self.streamer.create_session():
            logger.warning("⚠️ WebSocket session failed - falling back to polling")
        
        # Start WebSocket stream
        self.streamer.start(
            symbols=WATCHLIST,
            on_tick=self.analyzer.on_tick,
            on_candle=self.analyzer.on_candle,
            on_summary=self.analyzer.on_summary
        )
        
        # Send startup alert
        mode = "SANDBOX" if self.config.tradier.is_sandbox() else "LIVE"
        self.alerts.alert_bot_started(mode, self.account_balance)
        
        logger.info("✅ V2 Engine initialized with WebSocket streaming")
        logger.info(f"📡 Streaming {len(WATCHLIST)} symbols in real-time")
        return True
    
    def run(self):
        """Main trading loop"""
        self.running = True
        logger.info("=" * 60)
        logger.info("🏁 Starting V2 trading loop...")
        logger.info("=" * 60)
        logger.info("▶️ Trading engine started")
        
        try:
            while self.running:
                self._trading_loop()
                time.sleep(self.config.trading.scan_interval_sec)
        except KeyboardInterrupt:
            logger.info("⏹️ Shutdown requested")
        except Exception as e:
            logger.exception(f"❌ Fatal error: {e}")
            self.alerts.alert_error("Fatal Error", str(e))
        finally:
            self.shutdown()
    
    def _trading_loop(self):
        """Single iteration of trading loop"""
        now = datetime.now(ET)
        
        # Check new day
        self._check_new_day(now)
        
        # Check stream health
        self._check_stream_health()
        
        # Pull latest from stream into analyzer
        self.analyzer.update_from_stream()
        
        # Check trading window
        in_window = self._is_trading_window(now)
        
        # Alert window changes
        if in_window != self.last_window_state:
            if in_window:
                window_name = "Morning" if now.hour < 12 else "Afternoon"
                self.alerts.alert_window_open(window_name)
            else:
                self.alerts.alert_window_closed("Trading")
            self.last_window_state = in_window
        
        self.in_trading_window = in_window
        
        # Check existing positions (more frequently)
        current_time = time.time()
        if current_time - self._last_position_check >= self.config.trading.position_check_interval_sec:
            self._check_positions()
            self._last_position_check = current_time
        
        # Scan for new trades
        if in_window and self._can_trade():
            self._scan_and_trade()
        
        # Update IV rank periodically
        if current_time - self._last_iv_update >= self._iv_update_interval:
            self._update_iv_ranks()
            self._last_iv_update = current_time
        
        # Check regime changes
        self._check_regime_change()
    
    def _check_new_day(self, now: datetime):
        """Reset for new trading day"""
        today = now.date()
        if self.current_date != today:
            self.current_date = today
            self.analyzer.reset_daily_data()
            self.positions.reset_daily()
            
            balance = self.client.get_account_balance()
            if balance:
                self.account_balance = balance.get("total_equity", 0)
                self.positions.set_daily_starting_balance(self.account_balance)
            
            logger.info(f"📅 New trading day: {today}")
    
    def _check_stream_health(self):
        """Monitor WebSocket stream health"""
        current_time = time.time()
        if current_time - self._last_stream_check < 30:
            return
        self._last_stream_check = current_time
        
        if not self.streamer.is_healthy():
            if self.streamer.connected:
                logger.warning("⚠️ Stream appears stale - data may be delayed")
            else:
                logger.warning("🔌 Stream disconnected - attempting reconnect")
                self.alerts.alert_connection_lost("WebSocket Stream")
    
    def _is_trading_window(self, now: datetime) -> bool:
        """Check if in trading window"""
        clock = self.client.get_clock()
        if not clock or clock.get("state") != "open":
            return False
        
        current_time = now.time()
        windows = self.config.windows
        
        morning_start = datetime.strptime(windows.morning_start, "%H:%M").time()
        morning_end = datetime.strptime(windows.morning_end, "%H:%M").time()
        afternoon_start = datetime.strptime(windows.afternoon_start, "%H:%M").time()
        afternoon_end = datetime.strptime(windows.afternoon_end, "%H:%M").time()
        
        if morning_start <= current_time <= morning_end:
            return True
        if afternoon_start <= current_time <= afternoon_end:
            return True
        
        return False
    
    def _can_trade(self) -> bool:
        """Check all conditions for new trades"""
        if not self.analyzer.is_trending():
            return False
        if not self.positions.can_open_position():
            return False
        if self.positions.check_daily_loss_limit(self.account_balance):
            return False
        if self.positions.is_on_cooldown():
            return False
        if not self.analyzer.has_enough_data():
            return False
        return True
    
    def _check_positions(self):
        """Check and manage existing positions using stream data"""
        option_symbols = self.positions.get_option_symbols()
        if not option_symbols:
            return
        
        # Get option quotes via REST (options not on WebSocket stream)
        option_quotes = self.client.get_quotes(option_symbols)
        if not option_quotes:
            return
        
        self._option_quotes = option_quotes
        actions = self.positions.check_positions(option_quotes)
        
        for action in actions:
            self._execute_position_action(action)
    
    def _execute_position_action(self, action: Dict):
        """Execute position management action"""
        action_type = action["action"]
        option_symbol = action.get("option_symbol")
        position = self.positions.get_position(option_symbol) if option_symbol else None
        
        if action_type == "STOP_LOSS":
            result = self.client.place_market_sell(option_symbol, action["quantity"])
            if result:
                closed = self.positions.close_position(
                    option_symbol, action["price"], action["reason"]
                )
                if closed:
                    self.alerts.alert_exit_loss(
                        closed.symbol, closed.side,
                        action["pnl_pct"], closed.realized_pnl,
                        action["reason"]
                    )
        
        elif action_type == "TAKE_PROFIT":
            result = self.client.place_market_sell(option_symbol, action["quantity"])
            if result:
                closed = self.positions.close_position(
                    option_symbol, action["price"], action["reason"]
                )
                if closed:
                    self.alerts.alert_exit_profit(
                        closed.symbol, closed.side,
                        action["pnl_pct"], closed.realized_pnl,
                        action["reason"]
                    )
        
        elif action_type == "SET_BREAKEVEN":
            if self.positions.update_stop_to_breakeven(option_symbol):
                if position:
                    self.alerts.alert_breakeven_stop(
                        position.symbol, position.entry_price
                    )
        
        elif action_type == "PARTIAL_1":
            result = self.client.place_market_sell(option_symbol, action["quantity"])
            if result:
                self.positions.partial_close(
                    option_symbol, action["quantity"],
                    action["price"], partial_num=1
                )
                if position:
                    self.alerts.alert_partial_profit(
                        position.symbol, 1, action["quantity"],
                        action["pnl_pct"], position.current_quantity
                    )
        
        elif action_type == "PARTIAL_2":
            result = self.client.place_market_sell(option_symbol, action["quantity"])
            if result:
                self.positions.partial_close(
                    option_symbol, action["quantity"],
                    action["price"], partial_num=2
                )
                if position:
                    self.alerts.alert_partial_profit(
                        position.symbol, 2, action["quantity"],
                        action["pnl_pct"], position.current_quantity
                    )
    
    def _scan_and_trade(self):
        """Scan for signals with full V2 analysis"""
        signals = self.analyzer.scan_for_signals()
        
        for signal in signals:
            if self.positions.has_position(signal.symbol):
                continue
            
            # Calculate HOT score (includes multi-TF and Greeks)
            hot_score = self.analyzer.calculate_hot_score(signal)
            signal.hot_score = hot_score
            
            if hot_score < self.config.trading.min_hot_score:
                self.alerts.alert_low_hot_score(
                    signal.symbol, hot_score, self.config.trading.min_hot_score
                )
                continue
            
            # Multi-timeframe filter (NEW)
            if not signal.tf_1min_aligned and not signal.tf_5min_aligned:
                logger.info(f"⚠️ {signal.symbol} no timeframe alignment - skip")
                continue
            
            # IV rank filter (NEW)
            iv_rank = signal.iv_rank
            if iv_rank > self.config.trading.max_iv_rank:
                logger.info(f"⚠️ {signal.symbol} IV rank {iv_rank:.0f} too high - options expensive")
                continue
            
            # Confirm signal (15 sec hold)
            if not self.analyzer.confirm_signal(signal):
                continue
            
            # Additional filters
            if not self._passes_filters(signal):
                continue
            
            # Execute trade
            self._execute_entry(signal)
    
    def _passes_filters(self, signal: Signal) -> bool:
        """Check additional entry filters"""
        data = self.analyzer.get_stock_data(signal.symbol)
        if data and data.average_volume > 0:
            rvol = data.current_volume / data.average_volume
            if rvol < self.config.trading.min_rvol:
                logger.info(f"⚠️ {signal.symbol} RVOL {rvol:.1f} < {self.config.trading.min_rvol}")
                return False
        return True
    
    def _execute_entry(self, signal: Signal):
        """Execute trade with full Greeks analysis"""
        symbol = signal.symbol
        side = signal.side
        
        logger.info(
            f"🎯 Executing: {symbol} {side} | "
            f"Setup: {signal.setup_type} | HOT: {signal.hot_score} | "
            f"1m: {'✅' if signal.tf_1min_aligned else '❌'} | "
            f"5m: {'✅' if signal.tf_5min_aligned else '❌'} | "
            f"IV: {signal.iv_rank:.0f}"
        )
        
        # Find best option with Greeks analysis
        option_type = "call" if side == "CALL" else "put"
        option = self.client.find_best_option(
            symbol=symbol,
            option_type=option_type,
            trading_config=self.config.trading
        )
        
        if not option:
            logger.warning(f"❌ No suitable option found for {symbol}")
            return
        
        # Log Greeks details
        greeks = option.get("greeks_analysis", {})
        if greeks.get("warnings"):
            for warn in greeks["warnings"]:
                logger.warning(f"  ⚠️ {symbol}: {warn}")
        
        # Update Greeks score in analyzer
        self.analyzer.update_greeks_score(symbol, greeks.get("score", 0))
        
        option_symbol = option["symbol"]
        option_price = option.get("ask") or option.get("last") or 0
        
        if option_price <= 0:
            logger.warning(f"❌ Invalid option price for {symbol}")
            return
        
        # Calculate position size
        position_value = self.account_balance * self.config.trading.position_size_pct
        contract_cost = option_price * 100
        quantity = max(1, int(position_value / contract_cost))
        
        # Place order
        result = self.client.place_market_buy(option_symbol, quantity)
        
        if result:
            stop_pct = abs(self.config.trading.stop_loss_pct)
            stop_price = option_price * (1 - stop_pct)
            
            position = self.positions.open_position(
                symbol=symbol,
                option_symbol=option_symbol,
                side=side,
                quantity=quantity,
                entry_price=option_price,
                stop_price=stop_price,
                setup_type=signal.setup_type,
                hot_score=signal.hot_score
            )
            
            self.alerts.alert_entry(
                symbol=symbol,
                option_symbol=option_symbol,
                side=side,
                quantity=quantity,
                price=option_price,
                hot_score=signal.hot_score,
                setup_type=signal.setup_type
            )
            
            self.analyzer.clear_pending_signals(symbol)
            
            logger.info(
                f"✅ ENTERED: {symbol} {side} x{quantity} @ ${option_price:.2f} | "
                f"Δ={abs(option.get('delta',0)):.2f} θ={option.get('theta',0):.3f} "
                f"IV={option.get('iv',0)*100:.0f}%"
            )
        else:
            logger.error(f"❌ Order failed for {symbol}")
            self.alerts.alert_error("Order Failed", f"Could not enter {symbol} {side}")
    
    def _update_iv_ranks(self):
        """Periodically update IV rank for watchlist"""
        # Only update a few symbols per cycle to avoid rate limits
        symbols_to_update = []
        for symbol in WATCHLIST[:5]:  # Rotate through watchlist
            if symbol not in self._iv_rank_cache:
                symbols_to_update.append(symbol)
                break
        
        if not symbols_to_update:
            # Rotate: update oldest
            idx = int(time.time() / self._iv_update_interval) % len(WATCHLIST)
            symbols_to_update = [WATCHLIST[idx]]
        
        for symbol in symbols_to_update:
            try:
                iv_rank = self.client.calculate_iv_rank(symbol)
                self._iv_rank_cache[symbol] = iv_rank
                self.analyzer.update_iv_rank(symbol, iv_rank)
                logger.debug(f"📊 {symbol} IV Rank: {iv_rank:.0f}")
            except Exception as e:
                logger.error(f"IV rank error for {symbol}: {e}")
    
    def _check_regime_change(self):
        """Alert on regime changes"""
        current_regime = self.analyzer.get_regime()
        if current_regime != self.last_regime and self.last_regime != MarketRegime.UNKNOWN:
            self.alerts.alert_regime_change(self.last_regime, current_regime)
        self.last_regime = current_regime
    
    def shutdown(self):
        """Clean shutdown"""
        self.running = False
        
        # Stop WebSocket stream
        self.streamer.stop()
        
        # Send daily summary
        stats = self.positions.get_daily_stats()
        if stats["trades"] > 0:
            pnl_pct = (stats["realized_pnl"] / self.account_balance * 100) if self.account_balance > 0 else 0
            self.alerts.alert_daily_summary(
                trades=stats["trades"],
                winners=stats["winners"],
                losers=stats["losers"],
                pnl_dollars=stats["realized_pnl"],
                pnl_pct=pnl_pct
            )
        
        self.alerts.alert_bot_stopped("Shutdown requested")
        logger.info("⏹️ V2 Trading engine stopped")
    
    def get_status(self) -> Dict:
        """Get current engine status"""
        return {
            "running": self.running,
            "version": "V2",
            "in_window": self.in_trading_window,
            "regime": self.analyzer.get_regime(),
            "stream_connected": self.streamer.connected,
            "stream_healthy": self.streamer.is_healthy(),
            "can_trade": self._can_trade() if self.in_trading_window else False,
            "positions": self.positions.get_position_count(),
            "daily_pnl": self.positions.daily_realized_pnl,
            "on_cooldown": self.positions.is_on_cooldown(),
            "daily_limit_hit": self.positions.daily_loss_limit_hit,
        }
