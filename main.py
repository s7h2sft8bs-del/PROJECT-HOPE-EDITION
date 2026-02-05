#!/usr/bin/env python3
"""
PROJECT HOPE V2 - Headless Options Trading Bot
Top-tier trading bot with:
  - WebSocket real-time streaming
  - Greeks analysis (delta, theta, IV rank)
  - Multi-timeframe confirmation (1min + 5min)
  - Proper VWAP with standard deviation bands
  - Real candle-based indicators
  - 16 protection rules
  - SMS alerts via Twilio

Deploy to Render as Background Worker
"""

import logging
import sys
import os
from datetime import datetime


def setup_logging():
    log_format = "%(asctime)s | %(levelname)-8s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # Reduce noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


def check_environment():
    required = ["TRADIER_API_KEY", "TRADIER_ACCOUNT_ID"]
    optional = [
        "TRADIER_BASE_URL",
        "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN",
        "TWILIO_FROM_NUMBER", "ALERT_PHONE_NUMBER",
    ]
    
    missing = [var for var in required if not os.environ.get(var)]
    
    if missing:
        print(f"❌ Missing required: {missing}")
        return False
    return True


def main():
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("🚀 PROJECT HOPE V2 - Top-Tier Options Trading Bot")
    logger.info("=" * 60)
    logger.info(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    logger.info("⚡ UPGRADES FROM V1:")
    logger.info("  📡 WebSocket real-time streaming (tick-by-tick)")
    logger.info("  📊 Greeks analysis (delta, theta, gamma, IV)")
    logger.info("  📈 IV Rank filtering (avoid expensive options)")
    logger.info("  🔄 Multi-timeframe confirmation (1min + 5min)")
    logger.info("  📉 Proper VWAP with standard deviation bands")
    logger.info("  🕯️ Real candle-based indicators (not snapshots)")
    logger.info("  🛡️ All 16 protection rules active")
    logger.info("")
    
    if not check_environment():
        sys.exit(1)
    
    from config import Config
    from trading_engine import TradingEngine
    
    config = Config()
    
    logger.info(f"🔧 Tradier URL: {config.tradier.base_url}")
    logger.info(f"🔧 WebSocket URL: {config.tradier.ws_url}")
    logger.info(f"🔧 Max positions: {config.trading.max_positions}")
    logger.info(f"🔧 Stop loss: {config.trading.stop_loss_pct*100:.0f}%")
    logger.info(f"🔧 Take profit: {config.trading.take_profit_pct*100:.0f}%")
    logger.info(f"🔧 Daily loss limit: {config.trading.daily_loss_limit_pct*100:.0f}%")
    logger.info(f"🔧 Min HOT score: {config.trading.min_hot_score}")
    logger.info(f"🔧 Delta range: {config.trading.min_delta}-{config.trading.max_delta}")
    logger.info(f"🔧 IV rank range: {config.trading.min_iv_rank}-{config.trading.max_iv_rank}")
    logger.info(f"🔧 SMS alerts: {'Enabled' if config.twilio.account_sid else 'Disabled'}")
    
    engine = TradingEngine(config)
    
    if not engine.initialize():
        logger.error("❌ Failed to initialize V2 engine")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("🏁 Starting V2 trading loop...")
    logger.info("=" * 60)
    
    try:
        engine.run()
    except KeyboardInterrupt:
        logger.info("⏹️ Shutdown requested")
    except Exception as e:
        logger.exception(f"❌ Fatal error: {e}")
        sys.exit(1)
    
    logger.info("👋 Goodbye!")


if __name__ == "__main__":
    main()
