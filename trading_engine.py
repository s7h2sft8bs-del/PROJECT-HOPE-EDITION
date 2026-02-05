"""
PROJECT HOPE - Trading Engine
Main orchestrator that runs the trading loop
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz

from config import Config, WATCHLIST, MarketRegime, NEGATIVE_NEWS_KEYWORDS
from tradier_client import TradierClient
from market_analyzer import MarketAnalyzer, Signal
from position_manager import PositionManager
from alert_service import AlertService

logger = logging.getLogger(__name__)

# Eastern timezone for market hours
ET = pytz.timezone('US/Eastern')


class TradingEngine:
    """Main trading engine - runs the bot"""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Initialize components
        self.client = TradierClient(config.tradier)
        self.analyzer = MarketAnalyzer(config, self.client)
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
        
    def initialize(self) -> bool:
        """Initialize the engine and test connections"""
        logger.info("=" * 50)
        logger.info("🚀 PROJECT HOPE - Initializing...")
        logger.info("=" * 50)
        
        # Validate config
        errors = self.config.validate()
        if errors:
            for err in errors:
                logger.warning(f"⚠️ Config: {err}")
        
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
        
        # Initialize analyzer with watchlist
        self.analyzer.initialize(WATCHLIST)
        
        # Send startup alert
        mode = "SANDBOX" if self.config.tradier.is_sandbox() else "LIVE"
        self.alerts.alert_bot_started(mode, self.account_balance)
        
        logger.info("✅ Engine initialized successfully")
        return True
    
    def run(self):
        """Main trading loop"""
        self.running = True
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
        """Single iteration of the trading loop"""
        now = datetime.now(ET)
        
        # Check for new day
        self._check_new_day(now)
        
        # Check trading window
        in_window = self._is_trading_window(now)
        
        # Alert on window changes
        if in_window != self.last_window_state:
            if in_window:
                window_name = "Morning" if now.hour < 12 else "Power Hour"
                self.alerts.alert_window_open(window_name)
            else:
                self.alerts.alert_window_closed("Trading")
            self.last_window_state = in_window
        
        self.in_trading_window = in_window
        
        # Always update prices (for position management)
        self._update_prices()
        
        # Check existing positions
        self._check_positions()
        
        # Only scan for new signals during trading windows
        if in_window and self._can_trade():
            self._scan_and_trade()
        
        # Check regime changes
        self._check_regime_change()
    
    def _check_new_day(self, now: datetime):
        """Reset state for new trading day"""
        today = now.date()
        if self.current_date != today:
            self.current_date = today
            self.analyzer.reset_daily_data()
            self.positions.reset_daily()
            
            # Update starting balance
            balance = self.client.get_account_balance()
            if balance:
                self.account_balance = balance.get("total_equity", 0)
                self.positions.set_daily_starting_balance(self.account_balance)
            
            logger.info(f"📅 New trading day: {today}")
    
    def _is_trading_window(self, now: datetime) -> bool:
        """Check if we're in a valid trading window"""
        # Market must be open
        clock = self.client.get_clock()
        if not clock or clock.get("state") != "open":
            return False
        
        current_time = now.time()
        windows = self.config.windows
        
        # Parse window times
        morning_start = datetime.strptime(windows.morning_start, "%H:%M").time()
        morning_end = datetime.strptime(windows.morning_end, "%H:%M").time()
        afternoon_start = datetime.strptime(windows.afternoon_start, "%H:%M").time()
        afternoon_end = datetime.strptime(windows.afternoon_end, "%H:%M").time()
        
        # Check if in morning window (9:30 - 10:30)
        if morning_start <= current_time <= morning_end:
            return True
        
        # Check if in afternoon window (3:00 - 3:55)
        if afternoon_start <= current_time <= afternoon_end:
            return True
        
        return False
    
    def _can_trade(self) -> bool:
        """Check all conditions to allow new trades"""
        # Check regime
        if not self.analyzer.is_trending():
            return False
        
        # Check position limits
        if not self.positions.can_open_position():
            return False
        
        # Check daily loss limit
        if self.positions.check_daily_loss_limit(self.account_balance):
            return False
        
        # Check cooldown
        if self.positions.is_on_cooldown():
            remaining = self.positions.get_cooldown_remaining()
            logger.debug(f"⏸️ On cooldown: {remaining}s remaining")
            return False
        
        # Check if we have enough data
        if not self.analyzer.has_enough_data():
            return False
        
        return True
    
    def _update_prices(self):
        """Update prices for all watched symbols"""
        # Get quotes for watchlist
        quotes = self.client.get_quotes(WATCHLIST)
        if quotes:
            self.analyzer.update_prices(quotes)
        
        # Get quotes for open positions
        option_symbols = self.positions.get_option_symbols()
        if option_symbols:
            option_quotes = self.client.get_quotes(option_symbols)
            # Store for position checking
            self._option_quotes = option_quotes
    
    def _check_positions(self):
        """Check and manage existing positions"""
        if not hasattr(self, '_option_quotes'):
            return
        
        actions = self.positions.check_positions(self._option_quotes)
        
        for action in actions:
            self._execute_position_action(action)
    
    def _execute_position_action(self, action: Dict):
        """Execute a position management action"""
        action_type = action["action"]
        option_symbol = action["option_symbol"]
        position = self.positions.get_position(option_symbol)
        
        if not position:
            return
        
        if action_type == "STOP_LOSS":
            # Market sell to close
            result = self.client.place_market_sell(
                option_symbol, 
                action["quantity"]
            )
            if result:
                closed = self.positions.close_position(
                    option_symbol, 
                    action["price"],
                    action["reason"]
                )
                if closed:
                    self.alerts.alert_exit_loss(
                        closed.symbol,
                        closed.side,
                        action["pnl_pct"],
                        closed.realized_pnl,
                        action["reason"]
                    )
                    # Start cooldown
                    self.alerts.alert_cooldown_started(
                        closed.symbol,
                        self.config.trading.loss_cooldown_minutes
                    )
        
        elif action_type == "TAKE_PROFIT":
            result = self.client.place_market_sell(
                option_symbol,
                action["quantity"]
            )
            if result:
                closed = self.positions.close_position(
                    option_symbol,
                    action["price"],
                    action["reason"]
                )
                if closed:
                    self.alerts.alert_exit_profit(
                        closed.symbol,
                        closed.side,
                        action["pnl_pct"],
                        closed.realized_pnl,
                        action["reason"]
                    )
        
        elif action_type == "SET_BREAKEVEN":
            if self.positions.update_stop_to_breakeven(option_symbol):
                self.alerts.alert_breakeven_stop(
                    position.symbol,
                    position.entry_price
                )
        
        elif action_type == "PARTIAL_1":
            result = self.client.place_market_sell(
                option_symbol,
                action["quantity"]
            )
            if result:
                self.positions.partial_close(
                    option_symbol,
                    action["quantity"],
                    action["price"],
                    partial_num=1
                )
                self.alerts.alert_partial_profit(
                    position.symbol,
                    1,
                    action["quantity"],
                    action["pnl_pct"],
                    position.current_quantity
                )
        
        elif action_type == "PARTIAL_2":
            result = self.client.place_market_sell(
                option_symbol,
                action["quantity"]
            )
            if result:
                self.positions.partial_close(
                    option_symbol,
                    action["quantity"],
                    action["price"],
                    partial_num=2
                )
                self.alerts.alert_partial_profit(
                    position.symbol,
                    2,
                    action["quantity"],
                    action["pnl_pct"],
                    position.current_quantity
                )
    
    def _scan_and_trade(self):
        """Scan for signals and execute trades"""
        signals = self.analyzer.scan_for_signals()
        
        for signal in signals:
            # Skip if we already have position in this symbol
            if self.positions.has_position(signal.symbol):
                continue
            
            # Calculate HOT score
            hot_score = self.analyzer.calculate_hot_score(signal)
            signal.hot_score = hot_score
            
            # Check minimum HOT score
            if hot_score < self.config.trading.min_hot_score:
                self.alerts.alert_low_hot_score(
                    signal.symbol, 
                    hot_score, 
                    self.config.trading.min_hot_score
                )
                continue
            
            # Confirm signal (15 second hold)
            if not self.analyzer.confirm_signal(signal):
                continue
            
            # Additional filters
            if not self._passes_filters(signal):
                continue
            
            # Execute the trade!
            self._execute_entry(signal)
    
    def _passes_filters(self, signal: Signal) -> bool:
        """Check additional entry filters"""
        symbol = signal.symbol
        
        # Check RVOL
        data = self.analyzer.get_stock_data(symbol)
        if data:
            if data.average_volume > 0:
                rvol = data.current_volume / data.average_volume
                if rvol < self.config.trading.min_rvol:
                    logger.info(f"⚠️ {symbol} RVOL {rvol:.1f} < {self.config.trading.min_rvol}")
                    return False
        
        # TODO: Add earnings calendar check
        # TODO: Add news sentiment check
        
        return True
    
    def _execute_entry(self, signal: Signal):
        """Execute a trade entry"""
        symbol = signal.symbol
        side = signal.side
        
        logger.info(f"🎯 Executing: {symbol} {side} | Setup: {signal.setup_type} | HOT: {signal.hot_score}")
        
        # Find best option contract
        option_type = "call" if side == "CALL" else "put"
        option = self.client.find_best_option(
            symbol=symbol,
            option_type=option_type,
            target_delta=0.40,
            min_volume=self.config.trading.min_option_volume,
            min_oi=self.config.trading.min_open_interest,
            max_spread_pct=self.config.trading.max_spread_pct
        )
        
        if not option:
            logger.warning(f"❌ No suitable option found for {symbol}")
            return
        
        option_symbol = option["symbol"]
        option_price = option.get("ask") or option.get("last") or 0
        
        if option_price <= 0:
            logger.warning(f"❌ Invalid option price for {symbol}")
            return
        
        # Calculate position size (5% of account)
        position_value = self.account_balance * self.config.trading.position_size_pct
        contract_cost = option_price * 100  # Options are 100 shares
        quantity = max(1, int(position_value / contract_cost))
        
        # Place order
        result = self.client.place_market_buy(option_symbol, quantity)
        
        if result:
            # Calculate stop price (based on option, not stock)
            stop_pct = abs(self.config.trading.stop_loss_pct)
            stop_price = option_price * (1 - stop_pct)
            
            # Track position
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
            
            # Send alert
            self.alerts.alert_entry(
                symbol=symbol,
                option_symbol=option_symbol,
                side=side,
                quantity=quantity,
                price=option_price,
                hot_score=signal.hot_score,
                setup_type=signal.setup_type
            )
            
            # Clear pending signals for this symbol
            self.analyzer.clear_pending_signals(symbol)
        else:
            logger.error(f"❌ Order failed for {symbol}")
            self.alerts.alert_error("Order Failed", f"Could not enter {symbol} {side}")
    
    def _check_regime_change(self):
        """Check for and alert on regime changes"""
        current_regime = self.analyzer.get_regime()
        
        if current_regime != self.last_regime and self.last_regime != MarketRegime.UNKNOWN:
            self.alerts.alert_regime_change(self.last_regime, current_regime)
        
        self.last_regime = current_regime
    
    def shutdown(self):
        """Clean shutdown"""
        self.running = False
        
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
        logger.info("⏹️ Trading engine stopped")
    
    def get_status(self) -> Dict:
        """Get current engine status"""
        return {
            "running": self.running,
            "in_window": self.in_trading_window,
            "regime": self.analyzer.get_regime(),
            "can_trade": self._can_trade() if self.in_trading_window else False,
            "positions": self.positions.get_position_count(),
            "daily_pnl": self.positions.daily_realized_pnl,
            "on_cooldown": self.positions.is_on_cooldown(),
            "cooldown_remaining": self.positions.get_cooldown_remaining(),
            "daily_limit_hit": self.positions.daily_loss_limit_hit,
        }
