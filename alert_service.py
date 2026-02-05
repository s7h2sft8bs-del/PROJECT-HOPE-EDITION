"""
PROJECT HOPE - Alert Service
Sends SMS alerts via Twilio for all trading events
"""

import logging
from datetime import datetime
from typing import Optional

from config import TwilioConfig

logger = logging.getLogger(__name__)


class AlertService:
    """Handles all SMS alerts to the trader"""
    
    def __init__(self, config: TwilioConfig):
        self.config = config
        self.client = None
        self.enabled = False
        self._initialize()
    
    def _initialize(self):
        """Initialize Twilio client"""
        try:
            if self.config.account_sid and self.config.auth_token:
                from twilio.rest import Client
                self.client = Client(self.config.account_sid, self.config.auth_token)
                self.enabled = True
                logger.info("✅ Twilio client initialized - SMS alerts enabled")
            else:
                logger.warning("⚠️ Twilio credentials missing - alerts will log only")
        except ImportError:
            logger.warning("⚠️ Twilio package not installed - alerts will log only")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Twilio: {e}")
    
    def _send_sms(self, message: str) -> bool:
        """Send SMS message"""
        # Always log the alert
        logger.info(f"📱 ALERT: {message}")
        
        if not self.enabled or not self.client:
            return False
        
        try:
            self.client.messages.create(
                body=message,
                from_=self.config.from_number,
                to=self.config.to_number
            )
            return True
        except Exception as e:
            logger.error(f"❌ SMS send failed: {e}")
            return False
    
    # ==================== STARTUP ALERTS ====================
    
    def alert_bot_started(self, mode: str, account_value: float):
        """Alert when bot starts"""
        msg = (
            f"🤖 HOPE BOT STARTED\n"
            f"Mode: {mode}\n"
            f"Account: ${account_value:,.2f}\n"
            f"Time: {datetime.now().strftime('%I:%M %p ET')}"
        )
        self._send_sms(msg)
    
    def alert_bot_stopped(self, reason: str):
        """Alert when bot stops"""
        msg = f"🛑 HOPE BOT STOPPED\nReason: {reason}"
        self._send_sms(msg)
    
    # ==================== TRADE ALERTS ====================
    
    def alert_entry(self, symbol: str, option_symbol: str, side: str, 
                    quantity: int, price: float, hot_score: int, setup_type: str):
        """Alert when entering a new position"""
        emoji = "🟢" if side.upper() == "CALL" else "🔴"
        msg = (
            f"{emoji} ENTRY: {symbol} {side.upper()}\n"
            f"Setup: {setup_type}\n"
            f"Qty: {quantity} @ ${price:.2f}\n"
            f"HOT: {hot_score}/100\n"
            f"Contract: {option_symbol[-15:]}"
        )
        self._send_sms(msg)
    
    def alert_exit_profit(self, symbol: str, side: str, profit_pct: float, 
                          profit_dollars: float, reason: str):
        """Alert when exiting with profit"""
        msg = (
            f"💰 PROFIT: {symbol} {side.upper()}\n"
            f"+{profit_pct:.1f}% (+${profit_dollars:.2f})\n"
            f"Reason: {reason}"
        )
        self._send_sms(msg)
    
    def alert_exit_loss(self, symbol: str, side: str, loss_pct: float,
                        loss_dollars: float, reason: str):
        """Alert when exiting with loss"""
        msg = (
            f"🛑 LOSS: {symbol} {side.upper()}\n"
            f"{loss_pct:.1f}% (-${abs(loss_dollars):.2f})\n"
            f"Reason: {reason}"
        )
        self._send_sms(msg)
    
    def alert_partial_profit(self, symbol: str, partial_num: int, 
                             contracts_sold: int, profit_pct: float, 
                             remaining: int):
        """Alert when taking partial profits"""
        msg = (
            f"📈 PARTIAL T{partial_num}: {symbol}\n"
            f"Sold {contracts_sold} @ +{profit_pct:.1f}%\n"
            f"Remaining: {remaining} contracts"
        )
        self._send_sms(msg)
    
    def alert_breakeven_stop(self, symbol: str, entry_price: float):
        """Alert when stop moved to breakeven"""
        msg = (
            f"🔒 BREAKEVEN: {symbol}\n"
            f"Stop moved to ${entry_price:.2f}"
        )
        self._send_sms(msg)
    
    # ==================== REGIME ALERTS ====================
    
    def alert_regime_change(self, old_regime: str, new_regime: str):
        """Alert on market regime change"""
        if new_regime == "TREND":
            emoji = "✅"
            status = "TRADING ENABLED"
        else:
            emoji = "⚠️"
            status = "TRADING PAUSED"
        
        msg = (
            f"{emoji} REGIME: {old_regime} → {new_regime}\n"
            f"{status}"
        )
        self._send_sms(msg)
    
    def alert_regime_block(self, regime: str, signal_symbol: str):
        """Alert when signal blocked due to regime"""
        msg = (
            f"🚫 BLOCKED: {signal_symbol}\n"
            f"Market is {regime} - no trades"
        )
        self._send_sms(msg)
    
    # ==================== PROTECTION ALERTS ====================
    
    def alert_daily_limit_hit(self, loss_pct: float, loss_dollars: float):
        """Alert when daily loss limit hit"""
        msg = (
            f"🚨 DAILY LIMIT HIT\n"
            f"Loss: {loss_pct:.1f}% (-${abs(loss_dollars):.2f})\n"
            f"Trading locked for today"
        )
        self._send_sms(msg)
    
    def alert_cooldown_started(self, symbol: str, minutes: int):
        """Alert when loss cooldown starts"""
        msg = (
            f"⏸️ COOLDOWN: {minutes} min\n"
            f"After {symbol} loss\n"
            f"No new trades until cooldown ends"
        )
        self._send_sms(msg)
    
    def alert_cooldown_ended(self):
        """Alert when cooldown ends"""
        msg = "▶️ COOLDOWN ENDED\nReady to trade"
        self._send_sms(msg)
    
    def alert_window_open(self, window_name: str):
        """Alert when trading window opens"""
        msg = f"🔔 {window_name.upper()} WINDOW OPEN\nScanning for setups..."
        self._send_sms(msg)
    
    def alert_window_closed(self, window_name: str):
        """Alert when trading window closes"""
        msg = f"🔕 {window_name.upper()} WINDOW CLOSED"
        self._send_sms(msg)
    
    # ==================== FILTER ALERTS ====================
    
    def alert_earnings_block(self, symbol: str, days_until: int):
        """Alert when trade blocked due to earnings"""
        msg = (
            f"📅 EARNINGS BLOCK: {symbol}\n"
            f"Earnings in {days_until} days"
        )
        self._send_sms(msg)
    
    def alert_news_block(self, symbol: str, headline: str):
        """Alert when trade blocked due to bad news"""
        msg = (
            f"📰 NEWS BLOCK: {symbol}\n"
            f"Bad news detected:\n"
            f"{headline[:50]}..."
        )
        self._send_sms(msg)
    
    def alert_low_hot_score(self, symbol: str, score: int, min_score: int):
        """Alert when signal rejected for low HOT score"""
        logger.info(f"⚠️ {symbol} HOT score {score} < {min_score} minimum")
        # Don't SMS for every low score - too noisy
    
    # ==================== ERROR ALERTS ====================
    
    def alert_error(self, error_type: str, details: str):
        """Alert on critical errors"""
        msg = (
            f"❌ ERROR: {error_type}\n"
            f"{details[:100]}"
        )
        self._send_sms(msg)
    
    def alert_connection_lost(self, service: str):
        """Alert when connection to service is lost"""
        msg = f"🔌 CONNECTION LOST: {service}"
        self._send_sms(msg)
    
    def alert_connection_restored(self, service: str):
        """Alert when connection restored"""
        msg = f"✅ CONNECTION RESTORED: {service}"
        self._send_sms(msg)
    
    # ==================== DAILY SUMMARY ====================
    
    def alert_daily_summary(self, trades: int, winners: int, losers: int,
                           pnl_dollars: float, pnl_pct: float):
        """End of day summary alert"""
        if pnl_dollars >= 0:
            emoji = "📈"
            sign = "+"
        else:
            emoji = "📉"
            sign = ""
        
        win_rate = (winners / trades * 100) if trades > 0 else 0
        
        msg = (
            f"{emoji} DAILY SUMMARY\n"
            f"Trades: {trades} ({winners}W / {losers}L)\n"
            f"Win Rate: {win_rate:.0f}%\n"
            f"P&L: {sign}${pnl_dollars:.2f} ({sign}{pnl_pct:.1f}%)"
        )
        self._send_sms(msg)
