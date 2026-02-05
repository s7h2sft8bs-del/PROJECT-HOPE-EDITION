"""
PROJECT HOPE V1 - Headless Trading Bot
Entry point - runs on Render as background worker
REST polling only, no WebSocket needed
"""

import logging
import sys
import time
from datetime import datetime

import pytz

from config import Config
from trading_engine import TradingEngine

ET = pytz.timezone('US/Eastern')

# ==================== LOGGING ====================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 60)
    logger.info("🌱 PROJECT HOPE - Headless Trading Bot V1")
    logger.info("=" * 60)
    logger.info(f"⏰ Started at {datetime.now(ET).strftime('%Y-%m-%d %H:%M:%S ET')}")
    logger.info("📡 Mode: REST Polling (no WebSocket)")
    logger.info("")

    # Load config from environment
    config = Config.from_env()

    # Validate
    errors = config.validate()
    for err in errors:
        logger.warning(f"⚠️ {err}")

    if not config.tradier.api_key:
        logger.error("❌ TRADIER_API_KEY is required. Set it in Render environment variables.")
        logger.error("Waiting 60s before retry...")
        time.sleep(60)
        return main()

    # Create and initialize engine
    engine = TradingEngine(config)

    if not engine.initialize():
        logger.error("❌ Failed to initialize. Retrying in 60s...")
        time.sleep(60)
        return main()

    # Run the trading loop
    logger.info("")
    logger.info("✅ All systems go. Trading loop starting...")
    logger.info("=" * 60)
    engine.run()


if __name__ == "__main__":
    main()
