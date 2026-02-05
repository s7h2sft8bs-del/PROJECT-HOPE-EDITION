"""
PROJECT HOPE - Position Manager
Tracks open positions and manages exits, partials, and stops
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum

from config import Config, TradingConfig

logger = logging.getLogger(__name__)


class PositionState(Enum):
    """Position lifecycle states"""
    OPEN = "open"
    PARTIAL_1_TAKEN = "partial_1"  # 50% sold at +15%
    PARTIAL_2_TAKEN = "partial_2"  # 25% more sold at +25%
    BREAKEVEN_SET = "breakeven"    # Stop moved to entry
    CLOSED = "closed"


@dataclass
class Position:
    """Tracks a single position with all management state"""
    # Identity
    symbol: str
    option_symbol: str
    side: str  # "CALL" or "PUT"
    setup_type: str
    
    # Entry
    entry_price: float
    entry_quantity: int
    entry_time: datetime
    entry_cost: float = 0.0
    
    # Current state
    current_quantity: int = 0
    current_price: float = 0.0
    state: PositionState = PositionState.OPEN
    
    # Stop management
    stop_price: float = 0.0
    original_stop: float = 0.0
    stop_at_breakeven: bool = False
    
    # Profit tracking
    realized_pnl: float = 0.0
    partial_1_price: float = 0.0
    partial_1_qty: int = 0
    partial_2_price: float = 0.0
    partial_2_qty: int = 0
    
    # HOT score at entry
    hot_score: int = 0
    
    def __post_init__(self):
        self.current_quantity = self.entry_quantity
        self.entry_cost = self.entry_price * self.entry_quantity * 100
        self.original_stop = self.stop_price
    
    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized P&L"""
        if self.current_quantity <= 0:
            return 0
        current_value = self.current_price * self.current_quantity * 100
        remaining_cost = self.entry_price * self.current_quantity * 100
        return current_value - remaining_cost
    
    @property
    def unrealized_pnl_pct(self) -> float:
        """Calculate unrealized P&L percentage"""
        if self.entry_price <= 0:
            return 0
        return ((self.current_price - self.entry_price) / self.entry_price) * 100
    
    @property
    def total_pnl(self) -> float:
        """Total P&L (realized + unrealized)"""
        return self.realized_pnl + self.unrealized_pnl
    
    @property
    def total_pnl_pct(self) -> float:
        """Total P&L percentage"""
        if self.entry_cost <= 0:
            return 0
        return (self.total_pnl / self.entry_cost) * 100


class PositionManager:
    """Manages all open positions and their lifecycle"""
    
    def __init__(self, config: Config):
        self.config = config
        self.trading_config = config.trading
        
        # Active positions by option symbol
        self.positions: Dict[str, Position] = {}
        
        # Closed positions (for daily tracking)
        self.closed_positions: List[Position] = []
        
        # Daily P&L tracking
        self.daily_realized_pnl: float = 0.0
        self.daily_starting_balance: float = 0.0
        self.daily_loss_limit_hit: bool = False
        
        # Cooldown tracking
        self.cooldown_until: Optional[datetime] = None
        self.last_loss_time: Optional[datetime] = None
        
        # Symbols we're already in (duplicate protection)
        self.active_symbols: set = set()
    
    # ==================== POSITION LIFECYCLE ====================
    
    def open_position(self, symbol: str, option_symbol: str, side: str,
                      quantity: int, entry_price: float, stop_price: float,
                      setup_type: str, hot_score: int) -> Position:
        """Open a new position"""
        position = Position(
            symbol=symbol,
            option_symbol=option_symbol,
            side=side,
            setup_type=setup_type,
            entry_price=entry_price,
            entry_quantity=quantity,
            entry_time=datetime.now(),
            stop_price=stop_price,
            hot_score=hot_score
        )
        
        self.positions[option_symbol] = position
        self.active_symbols.add(symbol)
        
        logger.info(
            f"📥 Opened: {symbol} {side} x{quantity} @ ${entry_price:.2f} "
            f"| Stop: ${stop_price:.2f} | HOT: {hot_score}"
        )
        
        return position
    
    def close_position(self, option_symbol: str, exit_price: float, 
                       reason: str) -> Optional[Position]:
        """Close a position completely"""
        position = self.positions.get(option_symbol)
        if not position:
            logger.warning(f"Position not found: {option_symbol}")
            return None
        
        # Calculate final P&L
        remaining_qty = position.current_quantity
        if remaining_qty > 0:
            exit_value = exit_price * remaining_qty * 100
            cost_basis = position.entry_price * remaining_qty * 100
            final_pnl = exit_value - cost_basis
            position.realized_pnl += final_pnl
        
        position.current_quantity = 0
        position.current_price = exit_price
        position.state = PositionState.CLOSED
        
        # Track daily P&L
        self.daily_realized_pnl += position.realized_pnl
        
        # Check if this was a loss
        if position.realized_pnl < 0:
            self._handle_loss(position)
        
        # Move to closed and remove from active
        self.closed_positions.append(position)
        del self.positions[option_symbol]
        self.active_symbols.discard(position.symbol)
        
        logger.info(
            f"📤 Closed: {position.symbol} {position.side} | "
            f"P&L: ${position.realized_pnl:.2f} ({position.total_pnl_pct:.1f}%) | "
            f"Reason: {reason}"
        )
        
        return position
    
    def partial_close(self, option_symbol: str, quantity: int, 
                      exit_price: float, partial_num: int) -> bool:
        """Close part of a position (partial profit)"""
        position = self.positions.get(option_symbol)
        if not position or quantity > position.current_quantity:
            return False
        
        # Calculate P&L for this partial
        partial_value = exit_price * quantity * 100
        partial_cost = position.entry_price * quantity * 100
        partial_pnl = partial_value - partial_cost
        
        position.realized_pnl += partial_pnl
        position.current_quantity -= quantity
        
        if partial_num == 1:
            position.partial_1_price = exit_price
            position.partial_1_qty = quantity
            position.state = PositionState.PARTIAL_1_TAKEN
        elif partial_num == 2:
            position.partial_2_price = exit_price
            position.partial_2_qty = quantity
            position.state = PositionState.PARTIAL_2_TAKEN
        
        logger.info(
            f"📈 Partial T{partial_num}: {position.symbol} | "
            f"Sold {quantity} @ ${exit_price:.2f} | "
            f"P&L: ${partial_pnl:.2f} | Remaining: {position.current_quantity}"
        )
        
        return True
    
    def update_stop_to_breakeven(self, option_symbol: str) -> bool:
        """Move stop to breakeven"""
        position = self.positions.get(option_symbol)
        if not position or position.stop_at_breakeven:
            return False
        
        position.stop_price = position.entry_price
        position.stop_at_breakeven = True
        position.state = PositionState.BREAKEVEN_SET
        
        logger.info(f"🔒 Breakeven: {position.symbol} stop → ${position.entry_price:.2f}")
        
        return True
    
    # ==================== PRICE CHECKS ====================
    
    def check_positions(self, option_quotes: Dict[str, Dict]) -> List[Dict]:
        """
        Check all positions against current prices.
        Returns list of actions to take.
        """
        actions = []
        
        for option_symbol, position in list(self.positions.items()):
            quote = option_quotes.get(option_symbol)
            if not quote:
                continue
            
            # Update current price
            current_price = quote.get("last") or quote.get("bid") or 0
            if current_price <= 0:
                continue
            
            position.current_price = current_price
            pnl_pct = position.unrealized_pnl_pct
            
            # Check stop loss (-25%)
            if pnl_pct <= self.trading_config.stop_loss_pct * 100:
                actions.append({
                    "action": "STOP_LOSS",
                    "option_symbol": option_symbol,
                    "quantity": position.current_quantity,
                    "price": current_price,
                    "pnl_pct": pnl_pct,
                    "reason": f"Stop loss hit ({pnl_pct:.1f}%)"
                })
                continue
            
            # Check take profit (+30%)
            if pnl_pct >= self.trading_config.take_profit_pct * 100:
                actions.append({
                    "action": "TAKE_PROFIT",
                    "option_symbol": option_symbol,
                    "quantity": position.current_quantity,
                    "price": current_price,
                    "pnl_pct": pnl_pct,
                    "reason": f"Take profit hit (+{pnl_pct:.1f}%)"
                })
                continue
            
            # Check breakeven trigger (+10%)
            if (pnl_pct >= self.trading_config.breakeven_trigger * 100 
                and not position.stop_at_breakeven):
                actions.append({
                    "action": "SET_BREAKEVEN",
                    "option_symbol": option_symbol,
                    "price": position.entry_price
                })
            
            # Check partial 1 (+15%, sell 50%)
            if (pnl_pct >= self.trading_config.partial_1_trigger * 100 
                and position.state == PositionState.OPEN):
                sell_qty = int(position.current_quantity * self.trading_config.partial_1_sell_pct)
                if sell_qty > 0:
                    actions.append({
                        "action": "PARTIAL_1",
                        "option_symbol": option_symbol,
                        "quantity": sell_qty,
                        "price": current_price,
                        "pnl_pct": pnl_pct
                    })
            
            # Check partial 2 (+25%, sell 25% more)
            if (pnl_pct >= self.trading_config.partial_2_trigger * 100 
                and position.state == PositionState.PARTIAL_1_TAKEN):
                sell_qty = int(position.entry_quantity * self.trading_config.partial_2_sell_pct)
                sell_qty = min(sell_qty, position.current_quantity)
                if sell_qty > 0:
                    actions.append({
                        "action": "PARTIAL_2",
                        "option_symbol": option_symbol,
                        "quantity": sell_qty,
                        "price": current_price,
                        "pnl_pct": pnl_pct
                    })
        
        return actions
    
    # ==================== RISK MANAGEMENT ====================
    
    def _handle_loss(self, position: Position):
        """Handle loss - set cooldown"""
        self.last_loss_time = datetime.now()
        cooldown_minutes = self.trading_config.loss_cooldown_minutes
        self.cooldown_until = datetime.now() + timedelta(minutes=cooldown_minutes)
        logger.warning(f"⏸️ Loss on {position.symbol} - {cooldown_minutes}min cooldown")
    
    def is_on_cooldown(self) -> bool:
        """Check if we're in cooldown period"""
        if self.cooldown_until is None:
            return False
        if datetime.now() >= self.cooldown_until:
            self.cooldown_until = None
            return False
        return True
    
    def get_cooldown_remaining(self) -> int:
        """Get remaining cooldown seconds"""
        if not self.cooldown_until:
            return 0
        remaining = (self.cooldown_until - datetime.now()).total_seconds()
        return max(0, int(remaining))
    
    def check_daily_loss_limit(self, account_balance: float) -> bool:
        """Check if daily loss limit hit. Returns True if locked."""
        if self.daily_loss_limit_hit:
            return True
        
        if account_balance <= 0:
            return False
        
        loss_pct = abs(self.daily_realized_pnl) / account_balance
        if self.daily_realized_pnl < 0 and loss_pct >= self.trading_config.daily_loss_limit_pct:
            self.daily_loss_limit_hit = True
            logger.error(f"🚨 DAILY LOSS LIMIT: ${self.daily_realized_pnl:.2f} ({loss_pct*100:.1f}%)")
            return True
        
        return False
    
    def set_daily_starting_balance(self, balance: float):
        """Set starting balance for daily tracking"""
        self.daily_starting_balance = balance
    
    # ==================== QUERIES ====================
    
    def get_position_count(self) -> int:
        """Get number of open positions"""
        return len(self.positions)
    
    def has_position(self, symbol: str) -> bool:
        """Check if we have a position in this underlying"""
        return symbol in self.active_symbols
    
    def can_open_position(self) -> bool:
        """Check if we can open a new position"""
        if len(self.positions) >= self.trading_config.max_positions:
            return False
        if self.daily_loss_limit_hit:
            return False
        if self.is_on_cooldown():
            return False
        return True
    
    def get_position(self, option_symbol: str) -> Optional[Position]:
        """Get a specific position"""
        return self.positions.get(option_symbol)
    
    def get_all_positions(self) -> List[Position]:
        """Get all open positions"""
        return list(self.positions.values())
    
    def get_option_symbols(self) -> List[str]:
        """Get all option symbols we have positions in"""
        return list(self.positions.keys())
    
    def get_daily_stats(self) -> Dict:
        """Get daily trading statistics"""
        winners = len([p for p in self.closed_positions if p.realized_pnl > 0])
        losers = len([p for p in self.closed_positions if p.realized_pnl < 0])
        
        return {
            "trades": len(self.closed_positions),
            "winners": winners,
            "losers": losers,
            "win_rate": (winners / len(self.closed_positions) * 100) if self.closed_positions else 0,
            "realized_pnl": self.daily_realized_pnl,
            "open_positions": len(self.positions),
            "daily_limit_hit": self.daily_loss_limit_hit,
            "on_cooldown": self.is_on_cooldown(),
        }
    
    def reset_daily(self):
        """Reset for new trading day"""
        self.closed_positions.clear()
        self.daily_realized_pnl = 0.0
        self.daily_loss_limit_hit = False
        self.cooldown_until = None
        self.last_loss_time = None
        logger.info("🔄 Position manager reset for new day")
