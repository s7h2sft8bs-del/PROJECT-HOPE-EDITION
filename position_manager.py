"""
PROJECT HOPE V1 - Position Manager
Tracks all positions, handles partials, stops, breakeven,
cooldowns, daily loss limit, and duplicate protection
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pytz

from config import Config

logger = logging.getLogger(__name__)

ET = pytz.timezone('US/Eastern')


@dataclass
class Position:
    """Tracked position"""
    symbol: str
    option_symbol: str
    direction: str  # "CALL" or "PUT"
    setup: str
    quantity: int
    original_quantity: int
    entry_price: float
    current_price: float
    stop_price: float
    entry_time: datetime
    hot_score: int

    # Partial tracking
    t1_hit: bool = False     # +15% partial
    t2_hit: bool = False     # +25% partial
    breakeven_set: bool = False  # Stop moved to entry

    # P&L
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0

    @property
    def pnl_pct(self) -> float:
        if self.entry_price <= 0:
            return 0.0
        return (self.current_price - self.entry_price) / self.entry_price

    def update_price(self, price: float):
        self.current_price = price
        self.unrealized_pnl = (price - self.entry_price) * self.quantity * 100


class PositionManager:
    """Manages all position tracking and risk rules"""

    def __init__(self, config: Config):
        self.config = config

        # Active positions
        self.positions: Dict[str, Position] = {}

        # Daily tracking
        self.daily_pnl: float = 0.0
        self.daily_starting_balance: float = 0.0
        self.trading_locked: bool = False
        self.lock_reason: str = ""

        # Cooldown
        self.cooldown_until: Optional[datetime] = None
        self.last_loss_time: Optional[datetime] = None

        # Trade history (today)
        self.trades_today: List[dict] = []

        # Symbols currently held (duplicate protection)
        self.held_symbols: set = set()

    def set_daily_starting_balance(self, balance: float):
        self.daily_starting_balance = balance

    # ==================== POSITION MANAGEMENT ====================

    def add_position(self, symbol: str, option_symbol: str, direction: str,
                     setup: str, quantity: int, entry_price: float,
                     stop_price: float, hot_score: int) -> bool:
        """Add a new position"""
        # Check max positions
        if len(self.positions) >= self.config.risk.max_positions:
            logger.warning(f"⚠️ Max positions ({self.config.risk.max_positions}) reached")
            return False

        # Duplicate protection
        if symbol in self.held_symbols:
            logger.warning(f"⚠️ Already holding {symbol}")
            return False

        pos = Position(
            symbol=symbol,
            option_symbol=option_symbol,
            direction=direction,
            setup=setup,
            quantity=quantity,
            original_quantity=quantity,
            entry_price=entry_price,
            current_price=entry_price,
            stop_price=stop_price,
            entry_time=datetime.now(ET),
            hot_score=hot_score
        )

        self.positions[option_symbol] = pos
        self.held_symbols.add(symbol)

        logger.info(
            f"📥 Position added: {symbol} {direction} x{quantity} @ ${entry_price:.2f} "
            f"| Stop: ${stop_price:.2f} | HOT: {hot_score}"
        )
        return True

    def remove_position(self, option_symbol: str, exit_price: float, reason: str) -> Optional[dict]:
        """Remove a position and record the trade"""
        pos = self.positions.get(option_symbol)
        if not pos:
            return None

        # Calculate P&L
        pnl = (exit_price - pos.entry_price) * pos.quantity * 100
        pnl_pct = pos.pnl_pct

        # Record trade
        trade = {
            "symbol": pos.symbol,
            "option_symbol": option_symbol,
            "direction": pos.direction,
            "setup": pos.setup,
            "quantity": pos.quantity,
            "entry_price": pos.entry_price,
            "exit_price": exit_price,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "reason": reason,
            "hot_score": pos.hot_score,
            "entry_time": pos.entry_time,
            "exit_time": datetime.now(ET),
            "held_seconds": (datetime.now(ET) - pos.entry_time).total_seconds()
        }
        self.trades_today.append(trade)

        # Update daily P&L
        self.daily_pnl += pnl

        # Check if loss → trigger cooldown
        if pnl < 0:
            self.last_loss_time = datetime.now(ET)
            self.cooldown_until = self.last_loss_time + timedelta(
                seconds=self.config.risk.cooldown_after_loss_sec
            )
            logger.info(f"⏸️ Cooldown activated until {self.cooldown_until.strftime('%H:%M:%S')}")

        # Check daily loss limit
        if self.daily_starting_balance > 0:
            loss_pct = abs(self.daily_pnl) / self.daily_starting_balance
            if self.daily_pnl < 0 and loss_pct >= self.config.risk.daily_loss_limit_pct:
                self.trading_locked = True
                self.lock_reason = f"Daily loss limit hit: {loss_pct:.1%}"
                logger.warning(f"🔒 {self.lock_reason}")

        # Clean up
        self.held_symbols.discard(pos.symbol)
        del self.positions[option_symbol]

        logger.info(
            f"📤 Position closed: {pos.symbol} {reason} | "
            f"P&L: ${pnl:+,.2f} ({pnl_pct:+.1%})"
        )
        return trade

    # ==================== POSITION CHECKS ====================

    def check_positions(self, option_quotes: Dict[str, float]) -> List[dict]:
        """
        Check all positions for stops, targets, partials.
        Returns list of actions to take.
        """
        actions = []

        for opt_sym, pos in list(self.positions.items()):
            price = option_quotes.get(opt_sym, pos.current_price)
            if price <= 0:
                continue

            pos.update_price(price)
            pnl_pct = pos.pnl_pct

            # 1. STOP LOSS (-25%)
            if pnl_pct <= self.config.risk.stop_loss_pct:
                actions.append({
                    "action": "close",
                    "option_symbol": opt_sym,
                    "quantity": pos.quantity,
                    "reason": f"Stop loss ({pnl_pct:.1%})",
                    "price": price
                })
                continue

            # 2. TAKE PROFIT (+30%)
            if pnl_pct >= self.config.risk.take_profit_pct:
                actions.append({
                    "action": "close",
                    "option_symbol": opt_sym,
                    "quantity": pos.quantity,
                    "reason": f"Take profit ({pnl_pct:.1%})",
                    "price": price
                })
                continue

            # 3. PARTIAL T1 (+15% → sell 50%)
            if not pos.t1_hit and pnl_pct >= self.config.risk.partial_t1_pct:
                sell_qty = max(1, int(pos.quantity * self.config.risk.partial_t1_sell))
                if sell_qty > 0 and pos.quantity > 1:
                    actions.append({
                        "action": "partial",
                        "option_symbol": opt_sym,
                        "quantity": sell_qty,
                        "reason": f"T1 partial ({pnl_pct:.1%})",
                        "price": price,
                        "tier": "T1"
                    })
                pos.t1_hit = True

            # 4. PARTIAL T2 (+25% → sell 25% more)
            if not pos.t2_hit and pos.t1_hit and pnl_pct >= self.config.risk.partial_t2_pct:
                sell_qty = max(1, int(pos.original_quantity * self.config.risk.partial_t2_sell))
                if sell_qty > 0 and pos.quantity > 1:
                    actions.append({
                        "action": "partial",
                        "option_symbol": opt_sym,
                        "quantity": sell_qty,
                        "reason": f"T2 partial ({pnl_pct:.1%})",
                        "price": price,
                        "tier": "T2"
                    })
                pos.t2_hit = True

            # 5. BREAKEVEN (+10% → move stop to entry)
            if not pos.breakeven_set and pnl_pct >= self.config.risk.breakeven_trigger_pct:
                pos.stop_price = pos.entry_price
                pos.breakeven_set = True
                actions.append({
                    "action": "breakeven",
                    "option_symbol": opt_sym,
                    "reason": f"Stop → breakeven ({pnl_pct:.1%})",
                    "price": pos.entry_price
                })

        return actions

    def execute_partial(self, option_symbol: str, quantity: int, price: float):
        """Record a partial sell"""
        pos = self.positions.get(option_symbol)
        if pos:
            pnl = (price - pos.entry_price) * quantity * 100
            pos.realized_pnl += pnl
            pos.quantity -= quantity
            self.daily_pnl += pnl
            logger.info(f"📈 Partial: {pos.symbol} sold {quantity} @ ${price:.2f} (+${pnl:.2f})")

    # ==================== RISK CHECKS ====================

    def can_trade(self) -> tuple:
        """Check if trading is allowed. Returns (allowed, reason)"""
        # Daily loss limit
        if self.trading_locked:
            return False, self.lock_reason

        # Cooldown
        if self.cooldown_until:
            now = datetime.now(ET)
            if now < self.cooldown_until:
                remaining = (self.cooldown_until - now).total_seconds()
                return False, f"Cooldown: {remaining:.0f}s remaining"
            else:
                self.cooldown_until = None

        # Max positions
        if len(self.positions) >= self.config.risk.max_positions:
            return False, f"Max positions ({self.config.risk.max_positions})"

        return True, "OK"

    def is_duplicate(self, symbol: str) -> bool:
        """Check duplicate protection"""
        return symbol in self.held_symbols

    # ==================== DAILY RESET ====================

    def reset_daily(self, new_balance: float):
        """Reset for new trading day"""
        self.daily_pnl = 0.0
        self.daily_starting_balance = new_balance
        self.trading_locked = False
        self.lock_reason = ""
        self.cooldown_until = None
        self.last_loss_time = None
        self.trades_today = []
        logger.info(f"🔄 Position manager reset | Balance: ${new_balance:,.2f}")

    # ==================== STATUS ====================

    def get_status(self) -> dict:
        return {
            "positions": len(self.positions),
            "max_positions": self.config.risk.max_positions,
            "daily_pnl": self.daily_pnl,
            "trading_locked": self.trading_locked,
            "cooldown_active": self.cooldown_until is not None,
            "trades_today": len(self.trades_today)
        }
