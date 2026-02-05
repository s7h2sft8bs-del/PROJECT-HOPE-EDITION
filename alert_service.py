"""
PROJECT HOPE V1 - Alert Service
SMS text alerts via Twilio for all trading events
Works without Twilio (just logs) if credentials not set
"""

import logging
from datetime import datetime
from typing import Optional

from config import TwilioConfig

logger = logging.getLogger(__name__)


class AlertService:
    """SMS alert service via Twilio"""

    def __init__(self, config: TwilioConfig):
        self.config = config
        self.client = None
        self.enabled = False

        if config.account_sid and config.auth_token and config.from_number and config.to_number:
            try:
                from twilio.rest import Client
                self.client = Client(config.account_sid, config.auth_token)
                self.enabled = True
                logger.info("✅ Twilio SMS alerts enabled")
            except ImportError:
                logger.warning("⚠️ twilio package not installed - SMS disabled")
            except Exception as e:
                logger.warning(f"⚠️ Twilio init failed: {e} - SMS disabled")
        else:
            logger.info("ℹ️ Twilio not configured - alerts will log only")

    def _send(self, message: str):
        """Send SMS or log"""
        # Always log
        logger.info(f"📱 ALERT: {message}")

        if not self.enabled:
            return

        try:
            self.client.messages.create(
                body=message,
                from_=self.config.from_number,
                to=self.config.to_number
            )
        except Exception as e:
            logger.error(f"❌ SMS send failed: {e}")

    # ==================== TRADE ALERTS ====================

    def alert_entry(self, symbol: str, direction: str, setup: str,
                    quantity: int, price: float, hot_score: int, stop: float):
        self._send(
            f"🟢 ENTRY: {symbol} {direction}\n"
            f"Setup: {setup}\n"
            f"Qty: {quantity} @ ${price:.2f}\n"
            f"Stop: ${stop:.2f}\n"
            f"HOT: {hot_score}/100"
        )

    def alert_exit(self, symbol: str, direction: str, reason: str,
                   pnl: float, pnl_pct: float, held_seconds: float):
        emoji = "💰" if pnl > 0 else "🔴"
        held_min = held_seconds / 60
        self._send(
            f"{emoji} EXIT: {symbol} {direction}\n"
            f"Reason: {reason}\n"
            f"P&L: ${pnl:+,.2f} ({pnl_pct:+.1%})\n"
            f"Held: {held_min:.1f} min"
        )

    def alert_partial(self, symbol: str, tier: str, quantity: int,
                      price: float, pnl: float, remaining: int):
        self._send(
            f"📈 PARTIAL {tier}: {symbol}\n"
            f"Sold {quantity} @ ${price:.2f}\n"
            f"P&L: +${pnl:.2f}\n"
            f"Remaining: {remaining} contracts"
        )

    def alert_breakeven(self, symbol: str, stop_price: float):
        self._send(
            f"🔒 BREAKEVEN: {symbol}\n"
            f"Stop moved to ${stop_price:.2f}"
        )

    # ==================== STATUS ALERTS ====================

    def alert_bot_started(self, mode: str, balance: float):
        self._send(
            f"🚀 PROJECT HOPE STARTED\n"
            f"Mode: {mode}\n"
            f"Balance: ${balance:,.2f}\n"
            f"Bot is running and scanning..."
        )

    def alert_window_open(self, window_name: str):
        self._send(f"⏰ {window_name} trading window OPEN")

    def alert_window_closed(self, window_name: str):
        self._send(f"⏰ {window_name} trading window CLOSED")

    def alert_regime_change(self, old_regime: str, new_regime: str, crosses: int):
        emoji = "✅" if new_regime == "TREND" else "⚠️" if new_regime == "MIXED" else "🚫"
        self._send(
            f"{emoji} REGIME: {old_regime} → {new_regime}\n"
            f"SPY VWAP crosses: {crosses}"
        )

    def alert_daily_limit(self, pnl: float, limit_pct: float):
        self._send(
            f"🔒 DAILY LIMIT HIT\n"
            f"P&L: ${pnl:+,.2f}\n"
            f"Limit: {limit_pct:.0%}\n"
            f"Trading locked for today"
        )

    def alert_cooldown(self, seconds: int):
        self._send(
            f"⏸️ COOLDOWN: {seconds // 60} min after loss\n"
            f"No new trades until cooldown expires"
        )

    # ==================== ERROR ALERTS ====================

    def alert_error(self, title: str, details: str):
        self._send(
            f"❌ ERROR: {title}\n"
            f"{details}"
        )

    # ==================== DAILY SUMMARY ====================

    def alert_daily_summary(self, trades: list, daily_pnl: float, balance: float):
        wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
        losses = sum(1 for t in trades if t.get("pnl", 0) < 0)
        total = len(trades)

        self._send(
            f"📊 DAILY SUMMARY\n"
            f"Trades: {total} ({wins}W / {losses}L)\n"
            f"P&L: ${daily_pnl:+,.2f}\n"
            f"Balance: ${balance:,.2f}"
        )
