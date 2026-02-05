#!/usr/bin/env python3
"""
PROJECT HOPE - Headless Options Trading Bot
Main entry point for Render deployment

Environment Variables Required:
    TRADIER_API_KEY - Your Tradier API key
    TRADIER_ACCOUNT_ID - Your Tradier account ID
    TRADIER_BASE_URL - https://sandbox.tradier.com or https://api.tradier.com
    TWILIO_ACCOUNT_SID - Twilio account SID
    TWILIO_AUTH_TOKEN - Twilio auth token
    TWILIO_FROM_NUMBER - Your Twilio phone number
    ALERT_PHONE_NUMBER - Your phone number for alerts

Run locally:
    python main.py

Deploy to Render:
    1. Push to GitHub
    2. Create new Background Worker on Render
    3. Set environment variables
    4. Deploy
"""

import logging
import sys
import os
from datetime import datetime

# Configure logging
def setup_logging():
    """Configure logging for the bot"""
    log_format = "%(asctime)s | %(levelname)-8s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


def check_environment():
    """Check required environment variables"""
    required = [
        "TRADIER_API_KEY",
        "TRADIER_ACCOUNT_ID",
    ]
    
    optional = [
        "TRADIER_BASE_URL",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN", 
        "TWILIO_FROM_NUMBER",
        "ALERT_PHONE_NUMBER",
    ]
    
    missing = []
    for var in required:
        if not os.environ.get(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing required environment variables: {missing}")
        print("\nRequired variables:")
        for var in required:
            print(f"  {var}")
        print("\nOptional variables (for SMS alerts):")
        for var in optional:
            print(f"  {var}")
        return False
    
    return True


def main():
    """Main entry point"""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("🚀 PROJECT HOPE - Headless Options Trading Bot")
    logger.info("=" * 60)
    logger.info(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Import after logging setup
    from config import Config
    from trading_engine import TradingEngine
    
    # Create config
    config = Config()
    
    # Log configuration
    logger.info(f"🔧 Tradier URL: {config.tradier.base_url}")
    logger.info(f"🔧 Max positions: {config.trading.max_positions}")
    logger.info(f"🔧 Stop loss: {config.trading.stop_loss_pct*100:.0f}%")
    logger.info(f"🔧 Take profit: {config.trading.take_profit_pct*100:.0f}%")
    logger.info(f"🔧 Daily loss limit: {config.trading.daily_loss_limit_pct*100:.0f}%")
    logger.info(f"🔧 Min HOT score: {config.trading.min_hot_score}")
    logger.info(f"🔧 SMS alerts: {'Enabled' if config.twilio.account_sid else 'Disabled'}")
    
    # Create and initialize engine
    engine = TradingEngine(config)
    
    if not engine.initialize():
        logger.error("❌ Failed to initialize trading engine")
        sys.exit(1)
    
    # Run the trading loop
    logger.info("=" * 60)
    logger.info("🏁 Starting trading loop...")
    logger.info("=" * 60)
    
    try:
        engine.run()
    except KeyboardInterrupt:
        logger.info("⏹️ Shutdown requested by user")
    except Exception as e:
        logger.exception(f"❌ Fatal error: {e}")
        sys.exit(1)
    
    logger.info("👋 Goodbye!")


if __name__ == "__main__":
    main()
