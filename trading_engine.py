"""
PROJECT HOPE V1 - Trading Engine (FIXED)
Main trading loop with REST polling.
No WebSocket dependency. Scans, signals, executes, manages positions.

FIXES:
- _scan_and_trade re-checks can_trade() BEFORE each trade (not just once)
- Position checks run FIRST, before scanning for new trades
- _calc_position_size caps at max_contracts from config
- Batch option quote fetching (1 API call instead of N)
- Logs every position check with prices so you can see profits
- Only takes 1 trade per scan cycle (best signal only)
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pytz

from config import Config, WATCHLIST, MarketRegime
from tradier_client import TradierClient
from market_analyzer import MarketAnalyzer, Signal
from position_manager import PositionManager
from alert_service import AlertService

logger = logging.getLogger(__name__)

ET = pytz.timezone('US/Eastern')


class TradingEngine:
    """
    V1 Trading Engine - REST polling (FIXED)
    Scans market, generates signals, executes trades, manages positions
    """

    def __init__(self, config: Config):
        self.config = config

        # Core components
        self.client = TradierClient(config.tradier)
        self.analyzer = MarketAnalyzer(config, self.client)
        self.positions = PositionManager(config)
        self.alerts = AlertService(config.twilio)

        # State
        self.running = False
        self.current_date: Optional[datetime] = None
        self.last_window_state = False
        self.last_regime = MarketRegime.UNKNOWN

        # Account
        self.account_balance = 0.0

        # Timing
        self._last_position_check = 0
        self._last_scan_time = 0

    def initialize(self) -> bool:
        """Initialize the trading engine"""
        logger.info("=" * 60)
        logger.info("🚀 PROJECT HOPE V1 (FIXED) - Initializing...")
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

        # Send startup alert
        mode = "SANDBOX" if self.config.tradier.is_sandbox() else "LIVE"
        self.alerts.alert_bot_started(mode, self.account_balance)

        logger.info(f"✅ Engine initialized (FIXED) - REST polling mode")
        logger.info(f"📊 Watching {len(WATCHLIST)} symbols")
        logger.info(f"⏱️ Scan interval: {self.config.signals.scan_interval_sec}s")
        logger.info(f"⏱️ Position check interval: {self.config.signals.position_check_interval_sec}s")
        logger.info(f"🔒 Max positions: {self.config.risk.max_positions}")
        logger.info(f"🔒 Max contracts: {self.config.risk.max_contracts}")
        logger.info(f"⏸️ Trade cooldown: {self.config.risk.trade_cooldown_sec}s between trades")
        return True

    def run(self):
        """Main trading loop"""
        self.running = True
        logger.info("=" * 60)
        logger.info("🏁 Trading loop started")
        logger.info("=" * 60)

        try:
            while self.running:
                loop_start = time.time()
                self._trading_loop()
                # FIX: Sleep only 1 second between loops
                # Position checks and scans have their own timers
                time.sleep(1)
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
        current_time = time.time()

        # Check for new day
        self._check_new_day(now)

        # Check trading window
        in_window = self._is_trading_window(now)

        # Alert window changes
        if in_window != self.last_window_state:
            if in_window:
                window_name = "Morning" if now.hour < 12 else "Afternoon"
                self.alerts.alert_window_open(window_name)
                logger.info(f"🔔 {window_name} window OPEN")
            else:
                self.alerts.alert_window_closed("Trading")
                logger.info("🔔 Trading window CLOSED")
            self.last_window_state = in_window

        # FIX: ALWAYS check positions FIRST (every 3 seconds)
        # This is the #1 priority - profits must be taken before scanning
        if current_time - self._last_position_check >= self.config.signals.position_check_interval_sec:
            self._check_positions()
            self._last_position_check = current_time

        # Scan for new trades only in trading window (every 15 seconds)
        if in_window and (current_time - self._last_scan_time >= self.config.signals.scan_interval_sec):
            can_trade, reason = self.positions.can_trade()
            if can_trade:
                self._scan_and_trade()
            elif self.analyzer.scan_count % 8 == 0:  # Log periodically
                logger.info(f"⏸️ Not trading: {reason}")
            self._last_scan_time = current_time

        # Check regime changes
        self._check_regime_change()

    # ==================== SCANNING ====================

    def _scan_and_trade(self):
        """
        Scan for signals and execute trades.
        
        FIX: Only takes the BEST signal per scan cycle.
        FIX: Re-checks can_trade() before executing.
        """
        # Run analyzer update (fetches quotes, checks setups)
        signals = self.analyzer.update(WATCHLIST)

        if not signals:
            return

        # Sort by HOT score, take the best one only
        signals.sort(key=lambda s: s.hot_score, reverse=True)

        for signal in signals:
            # FIX: Re-check can_trade before EVERY trade attempt
            can_trade, reason = self.positions.can_trade()
            if not can_trade:
                logger.info(f"⏸️ Can't trade: {reason}")
                break  # Stop trying - we're blocked

            # Duplicate check
            if self.positions.is_duplicate(signal.symbol):
                logger.debug(f"⏭️ Skip {signal.symbol} - already holding")
                continue

            # Find best option contract
            option = self._find_option(signal)
            if not option:
                logger.info(f"⚠️ No suitable option for {signal.symbol} {signal.direction}")
                continue

            # Calculate position size (with hard cap)
            quantity = self._calc_position_size(option)
            if quantity <= 0:
                continue

            # Execute trade
            self._execute_entry(signal, option, quantity)

            # FIX: Only 1 trade per scan cycle - let position checks run
            break

    def _find_option(self, signal: Signal) -> Optional[dict]:
        """Find best option contract for a signal"""
        try:
            # Get expirations
            expirations = self.client.get_option_expirations(signal.symbol)
            if not expirations:
                return None

            # Find nearest valid expiration (1-14 DTE)
            today = datetime.now().date()
            valid_exp = None
            for exp_str in expirations:
                try:
                    exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
                    dte = (exp_date - today).days
                    if self.config.options.min_dte <= dte <= self.config.options.max_dte:
                        valid_exp = exp_str
                        break
                except ValueError:
                    continue

            if not valid_exp:
                return None

            # Get option chain
            chain = self.client.get_option_chain(signal.symbol, valid_exp)
            if not chain:
                return None

            # Filter for direction
            option_type = "call" if signal.direction == "CALL" else "put"

            best = None
            best_score = -1

            for opt in chain:
                if opt.get("option_type") != option_type:
                    continue

                bid = float(opt.get("bid", 0) or 0)
                ask = float(opt.get("ask", 0) or 0)
                volume = int(opt.get("volume", 0) or 0)
                oi = int(opt.get("open_interest", 0) or 0)

                # Price check
                if bid <= 0 or ask <= 0:
                    continue
                mid = (bid + ask) / 2
                if mid < 0.50 or mid > 20.0:
                    continue

                # Spread check
                spread_pct = (ask - bid) / ask if ask > 0 else 1
                if spread_pct > self.config.options.max_spread_pct:
                    continue

                # Volume check
                if volume < self.config.options.min_volume:
                    continue

                # Open interest check
                if oi < self.config.options.min_open_interest:
                    continue

                # Delta check (from greeks)
                greeks = opt.get("greeks", {}) or {}
                delta = abs(float(greeks.get("delta", 0) or 0))
                if delta > 0 and (delta < self.config.options.min_delta or delta > self.config.options.max_delta):
                    continue

                # Score this option
                score = (1 - spread_pct) * 40 + min(volume / 100, 30) + min(oi / 500, 30)

                if score > best_score:
                    best_score = score
                    best = {
                        "symbol": opt.get("symbol"),
                        "description": opt.get("description", ""),
                        "bid": bid,
                        "ask": ask,
                        "mid": mid,
                        "volume": volume,
                        "open_interest": oi,
                        "strike": float(opt.get("strike", 0)),
                        "expiration": valid_exp,
                        "greeks": greeks,
                        "score": score
                    }

            return best

        except Exception as e:
            logger.error(f"❌ Option search failed for {signal.symbol}: {e}")
            return None

    def _calc_position_size(self, option: dict) -> int:
        """
        Calculate number of contracts based on account size.
        FIX: Hard capped at max_contracts from config.
        """
        if self.account_balance <= 0:
            return 1

        max_risk = self.account_balance * self.config.risk.position_size_pct
        contract_cost = option["ask"] * 100

        if contract_cost <= 0:
            return 0

        quantity = int(max_risk / contract_cost)

        # FIX: Hard cap from config (default 5, was allowing up to 10)
        max_contracts = self.config.risk.max_contracts
        quantity = max(1, min(quantity, max_contracts))

        logger.info(
            f"📏 Position size: {quantity} contracts "
            f"(${max_risk:.0f} budget / ${contract_cost:.0f} per contract, "
            f"cap: {max_contracts})"
        )
        return quantity

    def _execute_entry(self, signal: Signal, option: dict, quantity: int):
        """Execute a trade entry"""
        opt_symbol = option["symbol"]
        price = option["ask"]

        logger.info(
            f"🎯 ENTERING: {signal.symbol} {signal.direction} | "
            f"{signal.setup} | HOT:{signal.hot_score} | "
            f"{quantity}x @ ${price:.2f}"
        )

        # Place order
        result = self.client.place_option_order(
            option_symbol=opt_symbol,
            side="buy_to_open",
            quantity=quantity,
            order_type="market"
        )

        if result:
            # Track position
            self.positions.add_position(
                symbol=signal.symbol,
                option_symbol=opt_symbol,
                direction=signal.direction,
                setup=signal.setup,
                quantity=quantity,
                entry_price=price,
                stop_price=signal.stop_price,
                hot_score=signal.hot_score
            )

            # Send alert
            self.alerts.alert_entry(
                symbol=signal.symbol,
                direction=signal.direction,
                setup=signal.setup,
                quantity=quantity,
                price=price,
                hot_score=signal.hot_score,
                stop=signal.stop_price
            )
        else:
            logger.error(f"❌ Order failed for {signal.symbol}")

    # ==================== POSITION MANAGEMENT ====================

    def _check_positions(self):
        """
        Check all positions for exits, partials, breakeven.
        FIX: Batch quote fetch + better logging.
        """
        if not self.positions.positions:
            return

        # FIX: Batch fetch all option quotes in ONE API call
        option_symbols = list(self.positions.positions.keys())
        option_quotes = {}

        # Use batch get_quotes instead of individual get_option_quote
        quotes_data = self.client.get_quotes(option_symbols)
        if quotes_data:
            for opt_sym, quote in quotes_data.items():
                price = quote.get("price", 0)
                if price <= 0:
                    # Try mid price
                    bid = quote.get("bid", 0)
                    ask = quote.get("ask", 0)
                    if bid > 0 and ask > 0:
                        price = (bid + ask) / 2
                if price > 0:
                    option_quotes[opt_sym] = price

        # FIX: Log what we got
        if option_symbols:
            got = len(option_quotes)
            total = len(option_symbols)
            if got < total:
                logger.warning(f"⚠️ Only got {got}/{total} option quotes")
            
            # Log each position status
            for opt_sym in option_symbols:
                pos = self.positions.positions.get(opt_sym)
                price = option_quotes.get(opt_sym, 0)
                if pos and price > 0:
                    pnl_pct = (price - pos.entry_price) / pos.entry_price if pos.entry_price > 0 else 0
                    logger.info(
                        f"📋 {pos.symbol}: entry ${pos.entry_price:.2f} → now ${price:.2f} "
                        f"| P&L: {pnl_pct:+.1%} | Qty: {pos.quantity} "
                        f"| T1:{pos.t1_hit} T2:{pos.t2_hit} BE:{pos.breakeven_set}"
                    )

        # Check positions against prices
        actions = self.positions.check_positions(option_quotes)

        for action in actions:
            opt_sym = action["option_symbol"]
            pos = self.positions.positions.get(opt_sym)

            if action["action"] == "close":
                # Full close
                result = self.client.place_option_order(
                    option_symbol=opt_sym,
                    side="sell_to_close",
                    quantity=action["quantity"],
                    order_type="market"
                )
                if result:
                    trade = self.positions.remove_position(
                        opt_sym, action["price"], action["reason"]
                    )
                    if trade:
                        self.alerts.alert_exit(
                            symbol=trade["symbol"],
                            direction=trade["direction"],
                            reason=trade["reason"],
                            pnl=trade["pnl"],
                            pnl_pct=trade["pnl_pct"],
                            held_seconds=trade["held_seconds"]
                        )

            elif action["action"] == "partial":
                # Partial sell
                result = self.client.place_option_order(
                    option_symbol=opt_sym,
                    side="sell_to_close",
                    quantity=action["quantity"],
                    order_type="market"
                )
                if result and pos:
                    self.positions.execute_partial(
                        opt_sym, action["quantity"], action["price"]
                    )
                    self.alerts.alert_partial(
                        symbol=pos.symbol,
                        tier=action.get("tier", "T1"),
                        quantity=action["quantity"],
                        price=action["price"],
                        pnl=(action["price"] - pos.entry_price) * action["quantity"] * 100,
                        remaining=pos.quantity
                    )

            elif action["action"] == "breakeven":
                if pos:
                    self.alerts.alert_breakeven(pos.symbol, action["price"])

    # ==================== REGIME TRACKING ====================

    def _check_regime_change(self):
        """Alert on regime changes"""
        current = self.analyzer.get_regime()
        if current != self.last_regime and self.last_regime != MarketRegime.UNKNOWN:
            self.alerts.alert_regime_change(
                self.last_regime, current, self.analyzer.spy_vwap_crosses
            )
        self.last_regime = current

    # ==================== TIME MANAGEMENT ====================

    def _is_trading_window(self, now: datetime) -> bool:
        """Check if within trading window"""
        w = self.config.windows

        # Parse window times
        m_start = self._parse_time(w.morning_start, now)
        m_end = self._parse_time(w.morning_end, now)
        a_start = self._parse_time(w.afternoon_start, now)
        a_end = self._parse_time(w.afternoon_end, now)

        in_morning = m_start <= now <= m_end
        in_afternoon = a_start <= now <= a_end

        return in_morning or in_afternoon

    @staticmethod
    def _parse_time(time_str: str, now: datetime) -> datetime:
        """Parse HH:MM string to datetime"""
        h, m = map(int, time_str.split(":"))
        return now.replace(hour=h, minute=m, second=0, microsecond=0)

    def _check_new_day(self, now: datetime):
        """Reset on new trading day"""
        today = now.date()
        if self.current_date != today:
            if self.current_date is not None:
                # End of previous day - send summary
                self.alerts.alert_daily_summary(
                    self.positions.trades_today,
                    self.positions.daily_pnl,
                    self.account_balance
                )

            self.current_date = today

            # Refresh balance
            balance = self.client.get_account_balance()
            if balance:
                self.account_balance = balance.get("total_equity", self.account_balance)

            # Reset daily trackers
            self.positions.reset_daily(self.account_balance)
            self.analyzer.reset_daily()

            logger.info(f"📅 New trading day: {today} | Balance: ${self.account_balance:,.2f}")

    # ==================== SHUTDOWN ====================

    def shutdown(self):
        """Clean shutdown"""
        self.running = False
        logger.info("⏹️ Trading engine stopped")

        # Final summary
        self.alerts.alert_daily_summary(
            self.positions.trades_today,
            self.positions.daily_pnl,
            self.account_balance
        )
