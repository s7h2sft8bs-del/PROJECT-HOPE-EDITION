"""
PROJECT HOPE V1 - Tradier REST API Client
All API calls: quotes, orders, positions, account, options chain
REST polling only - no WebSocket
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

from config import TradierConfig

logger = logging.getLogger(__name__)


class TradierClient:
    """Tradier REST API wrapper"""

    def __init__(self, config: TradierConfig):
        self.config = config
        self.base_url = config.base_url
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Accept": "application/json"
        }
        self._last_request = 0
        self._min_interval = 0.25  # Max 4 requests/sec

    def _throttle(self):
        """Rate limit protection"""
        now = time.time()
        elapsed = now - self._last_request
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request = time.time()

    def _get(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make GET request to Tradier API"""
        self._throttle()
        url = f"{self.base_url}/v1/{endpoint}"
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP {resp.status_code} on {endpoint}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Request failed {endpoint}: {e}")
            return None

    def _post(self, endpoint: str, data: dict = None) -> Optional[dict]:
        """Make POST request to Tradier API"""
        self._throttle()
        url = f"{self.base_url}/v1/{endpoint}"
        try:
            resp = requests.post(url, headers=self.headers, data=data, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP {resp.status_code} on {endpoint}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Request failed {endpoint}: {e}")
            return None

    # ==================== MARKET DATA ====================

    def get_quotes(self, symbols: List[str]) -> Dict[str, dict]:
        """Get quotes for multiple symbols"""
        if not symbols:
            return {}
        
        symbol_str = ",".join(symbols)
        data = self._get("markets/quotes", {"symbols": symbol_str, "greeks": "false"})
        
        if not data or "quotes" not in data:
            return {}

        quotes = data["quotes"]
        if "quote" not in quotes:
            return {}

        quote_list = quotes["quote"]
        if isinstance(quote_list, dict):
            quote_list = [quote_list]

        result = {}
        for q in quote_list:
            sym = q.get("symbol")
            if sym:
                result[sym] = {
                    "price": float(q.get("last", 0) or 0),
                    "bid": float(q.get("bid", 0) or 0),
                    "ask": float(q.get("ask", 0) or 0),
                    "high": float(q.get("high", 0) or 0),
                    "low": float(q.get("low", 0) or 0),
                    "open": float(q.get("open", 0) or 0),
                    "close": float(q.get("close", 0) or q.get("prevclose", 0) or 0),
                    "prevclose": float(q.get("prevclose", 0) or 0),
                    "volume": int(q.get("volume", 0) or 0),
                    "average_volume": int(q.get("average_volume", 0) or 0),
                    "change_pct": float(q.get("change_percentage", 0) or 0),
                }
        return result

    def get_quote(self, symbol: str) -> Optional[dict]:
        """Get single quote"""
        quotes = self.get_quotes([symbol])
        return quotes.get(symbol)

    def get_option_chain(self, symbol: str, expiration: str = None) -> List[dict]:
        """Get options chain for a symbol"""
        params = {"symbol": symbol, "greeks": "true"}
        if expiration:
            params["expiration"] = expiration

        data = self._get("markets/options/chains", params)
        if not data or "options" not in data:
            return []

        options = data["options"]
        if not options or "option" not in options:
            return []

        option_list = options["option"]
        if isinstance(option_list, dict):
            option_list = [option_list]

        return option_list

    def get_option_expirations(self, symbol: str) -> List[str]:
        """Get available option expiration dates"""
        data = self._get("markets/options/expirations", {"symbol": symbol})
        if not data or "expirations" not in data:
            return []

        exp = data["expirations"]
        if not exp or "date" not in exp:
            return []

        dates = exp["date"]
        if isinstance(dates, str):
            dates = [dates]
        return dates

    def get_option_quote(self, option_symbol: str) -> Optional[dict]:
        """Get quote for a specific option contract"""
        data = self._get("markets/quotes", {"symbols": option_symbol, "greeks": "true"})
        if not data or "quotes" not in data:
            return None

        quotes = data["quotes"]
        if "quote" not in quotes:
            return None

        q = quotes["quote"]
        if isinstance(q, list):
            q = q[0]
        return q

    # ==================== ORDERS ====================

    def place_option_order(self, option_symbol: str, side: str, quantity: int,
                           order_type: str = "market", price: float = None) -> Optional[dict]:
        """Place an option order"""
        data = {
            "class": "option",
            "symbol": option_symbol.split(" ")[0] if " " in option_symbol else option_symbol[:4],
            "option_symbol": option_symbol,
            "side": side,  # "buy_to_open", "sell_to_close"
            "quantity": str(quantity),
            "type": order_type,
            "duration": "day"
        }
        if price and order_type == "limit":
            data["price"] = str(price)

        endpoint = f"accounts/{self.config.account_id}/orders"
        result = self._post(endpoint, data)

        if result and "order" in result:
            order_id = result["order"].get("id")
            logger.info(f"✅ Order placed: {side} {quantity}x {option_symbol} - ID: {order_id}")
            return result["order"]
        else:
            logger.error(f"❌ Order failed: {result}")
            return None

    def get_order_status(self, order_id: str) -> Optional[dict]:
        """Get status of an order"""
        endpoint = f"accounts/{self.config.account_id}/orders/{order_id}"
        return self._get(endpoint)

    # ==================== POSITIONS ====================

    def get_positions(self) -> List[dict]:
        """Get all open positions"""
        endpoint = f"accounts/{self.config.account_id}/positions"
        data = self._get(endpoint)

        if not data or "positions" not in data:
            return []

        positions = data["positions"]
        if positions == "null" or not positions:
            return []

        if "position" not in positions:
            return []

        pos_list = positions["position"]
        if isinstance(pos_list, dict):
            pos_list = [pos_list]

        return pos_list

    # ==================== ACCOUNT ====================

    def get_account_balance(self) -> Optional[dict]:
        """Get account balance"""
        endpoint = f"accounts/{self.config.account_id}/balances"
        data = self._get(endpoint)
        if data and "balances" in data:
            return data["balances"]
        return None

    def get_account_history(self, days: int = 30) -> List[dict]:
        """Get account history"""
        endpoint = f"accounts/{self.config.account_id}/history"
        data = self._get(endpoint)
        if data and "history" in data:
            history = data["history"]
            if history and "event" in history:
                events = history["event"]
                if isinstance(events, dict):
                    events = [events]
                return events
        return []

    # ==================== MARKET STATUS ====================

    def get_clock(self) -> Optional[dict]:
        """Get market clock/status"""
        return self._get("markets/clock")

    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        clock = self.get_clock()
        if clock and "clock" in clock:
            return clock["clock"].get("state") == "open"
        return False

    # ==================== CONNECTION TEST ====================

    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            balance = self.get_account_balance()
            if balance:
                equity = balance.get("total_equity", 0)
                logger.info(f"✅ Tradier connected - Equity: ${equity:,.2f}")
                return True
        except Exception as e:
            logger.error(f"❌ Tradier connection failed: {e}")
        return False
