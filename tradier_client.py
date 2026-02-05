"""
PROJECT HOPE - Tradier Client
Handles all interactions with Tradier API for quotes, orders, and account data
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests

from config import TradierConfig

logger = logging.getLogger(__name__)


class TradierClient:
    """Tradier API wrapper for trading operations"""
    
    def __init__(self, config: TradierConfig):
        self.config = config
        self.base_url = config.base_url
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Accept": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _get(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make GET request to Tradier API"""
        self._rate_limit()
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GET {endpoint} failed: {e}")
            return None
    
    def _post(self, endpoint: str, data: dict = None) -> Optional[dict]:
        """Make POST request to Tradier API"""
        self._rate_limit()
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.post(url, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"POST {endpoint} failed: {e}")
            return None
    
    def _delete(self, endpoint: str) -> Optional[dict]:
        """Make DELETE request to Tradier API"""
        self._rate_limit()
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.delete(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"DELETE {endpoint} failed: {e}")
            return None

    # ==================== ACCOUNT ====================
    
    def get_account_balance(self) -> Optional[Dict]:
        """Get account balance and buying power"""
        result = self._get(f"/v1/accounts/{self.config.account_id}/balances")
        if result and "balances" in result:
            bal = result["balances"]
            return {
                "total_equity": bal.get("total_equity", 0),
                "total_cash": bal.get("total_cash", 0),
                "option_buying_power": bal.get("option_buying_power", 0),
                "day_trade_buying_power": bal.get("day_trade_buying_power", 0),
                "pending_cash": bal.get("pending_cash", 0),
            }
        return None
    
    def get_positions(self) -> List[Dict]:
        """Get all open positions"""
        result = self._get(f"/v1/accounts/{self.config.account_id}/positions")
        if result and "positions" in result:
            positions = result["positions"]
            if positions == "null" or positions is None:
                return []
            if isinstance(positions, dict) and "position" in positions:
                pos_list = positions["position"]
                if isinstance(pos_list, dict):
                    return [pos_list]
                return pos_list
        return []
    
    def get_orders(self, status: str = "open") -> List[Dict]:
        """Get orders by status (open, pending, filled, etc.)"""
        result = self._get(f"/v1/accounts/{self.config.account_id}/orders")
        if result and "orders" in result:
            orders = result["orders"]
            if orders == "null" or orders is None:
                return []
            if isinstance(orders, dict) and "order" in orders:
                order_list = orders["order"]
                if isinstance(order_list, dict):
                    order_list = [order_list]
                # Filter by status
                return [o for o in order_list if o.get("status") == status]
        return []

    # ==================== MARKET DATA ====================
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get current quote for a symbol"""
        result = self._get("/v1/markets/quotes", {"symbols": symbol})
        if result and "quotes" in result:
            quote = result["quotes"].get("quote")
            if quote:
                if isinstance(quote, list):
                    quote = quote[0]
                return {
                    "symbol": quote.get("symbol"),
                    "last": quote.get("last"),
                    "bid": quote.get("bid"),
                    "ask": quote.get("ask"),
                    "high": quote.get("high"),
                    "low": quote.get("low"),
                    "open": quote.get("open"),
                    "close": quote.get("close"),  # Previous close
                    "volume": quote.get("volume"),
                    "average_volume": quote.get("average_volume"),
                    "change": quote.get("change"),
                    "change_pct": quote.get("change_percentage"),
                }
        return None
    
    def get_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get quotes for multiple symbols"""
        if not symbols:
            return {}
        
        result = self._get("/v1/markets/quotes", {"symbols": ",".join(symbols)})
        quotes = {}
        
        if result and "quotes" in result:
            quote_data = result["quotes"].get("quote", [])
            if isinstance(quote_data, dict):
                quote_data = [quote_data]
            
            for q in quote_data:
                sym = q.get("symbol")
                if sym:
                    quotes[sym] = {
                        "symbol": sym,
                        "last": q.get("last"),
                        "bid": q.get("bid"),
                        "ask": q.get("ask"),
                        "high": q.get("high"),
                        "low": q.get("low"),
                        "open": q.get("open"),
                        "close": q.get("close"),
                        "volume": q.get("volume"),
                        "average_volume": q.get("average_volume"),
                        "change": q.get("change"),
                        "change_pct": q.get("change_percentage"),
                    }
        return quotes
    
    def get_option_chain(self, symbol: str, expiration: str = None) -> List[Dict]:
        """Get option chain for a symbol"""
        params = {"symbol": symbol, "greeks": "true"}
        if expiration:
            params["expiration"] = expiration
        
        result = self._get("/v1/markets/options/chains", params)
        options = []
        
        if result and "options" in result:
            chain = result["options"].get("option", [])
            if isinstance(chain, dict):
                chain = [chain]
            
            for opt in chain:
                options.append({
                    "symbol": opt.get("symbol"),
                    "underlying": opt.get("underlying"),
                    "strike": opt.get("strike"),
                    "expiration": opt.get("expiration_date"),
                    "option_type": opt.get("option_type"),  # call or put
                    "last": opt.get("last"),
                    "bid": opt.get("bid"),
                    "ask": opt.get("ask"),
                    "volume": opt.get("volume"),
                    "open_interest": opt.get("open_interest"),
                    "delta": opt.get("greeks", {}).get("delta"),
                    "gamma": opt.get("greeks", {}).get("gamma"),
                    "theta": opt.get("greeks", {}).get("theta"),
                    "vega": opt.get("greeks", {}).get("vega"),
                    "iv": opt.get("greeks", {}).get("mid_iv"),
                })
        return options
    
    def get_option_expirations(self, symbol: str) -> List[str]:
        """Get available option expiration dates"""
        result = self._get("/v1/markets/options/expirations", {"symbol": symbol})
        if result and "expirations" in result:
            exp = result["expirations"].get("date", [])
            if isinstance(exp, str):
                return [exp]
            return exp
        return []
    
    def get_timesales(self, symbol: str, interval: str = "1min", 
                      start: str = None, end: str = None) -> List[Dict]:
        """Get intraday time and sales data"""
        params = {"symbol": symbol, "interval": interval}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        
        result = self._get("/v1/markets/timesales", params)
        bars = []
        
        if result and "series" in result:
            data = result["series"].get("data", [])
            if isinstance(data, dict):
                data = [data]
            
            for bar in data:
                bars.append({
                    "time": bar.get("time"),
                    "timestamp": bar.get("timestamp"),
                    "open": bar.get("open"),
                    "high": bar.get("high"),
                    "low": bar.get("low"),
                    "close": bar.get("close"),
                    "volume": bar.get("volume"),
                    "vwap": bar.get("vwap"),
                })
        return bars
    
    def get_clock(self) -> Optional[Dict]:
        """Get market clock/status"""
        result = self._get("/v1/markets/clock")
        if result and "clock" in result:
            clock = result["clock"]
            return {
                "state": clock.get("state"),  # open, closed, premarket, postmarket
                "timestamp": clock.get("timestamp"),
                "next_state": clock.get("next_state"),
                "next_change": clock.get("next_change"),
            }
        return None

    # ==================== ORDERS ====================
    
    def place_option_order(self, option_symbol: str, side: str, quantity: int,
                           order_type: str = "market", limit_price: float = None,
                           stop_price: float = None, duration: str = "day") -> Optional[Dict]:
        """
        Place an option order
        
        Args:
            option_symbol: Full OCC option symbol (e.g., AAPL240119C00150000)
            side: "buy_to_open", "buy_to_close", "sell_to_open", "sell_to_close"
            quantity: Number of contracts
            order_type: "market", "limit", "stop", "stop_limit"
            limit_price: Limit price (required for limit orders)
            stop_price: Stop price (required for stop orders)
            duration: "day", "gtc", "pre", "post"
        """
        data = {
            "class": "option",
            "symbol": option_symbol[:option_symbol.index("2") if "2" in option_symbol else len(option_symbol)].rstrip("0123456789"),  # Extract underlying
            "option_symbol": option_symbol,
            "side": side,
            "quantity": quantity,
            "type": order_type,
            "duration": duration,
        }
        
        if order_type in ("limit", "stop_limit") and limit_price:
            data["price"] = round(limit_price, 2)
        if order_type in ("stop", "stop_limit") and stop_price:
            data["stop"] = round(stop_price, 2)
        
        result = self._post(f"/v1/accounts/{self.config.account_id}/orders", data)
        
        if result and "order" in result:
            order = result["order"]
            logger.info(f"✅ Order placed: {side} {quantity}x {option_symbol} - ID: {order.get('id')}")
            return {
                "id": order.get("id"),
                "status": order.get("status"),
            }
        else:
            logger.error(f"❌ Order failed: {result}")
            return None
    
    def place_market_buy(self, option_symbol: str, quantity: int) -> Optional[Dict]:
        """Quick helper for market buy to open"""
        return self.place_option_order(
            option_symbol=option_symbol,
            side="buy_to_open",
            quantity=quantity,
            order_type="market"
        )
    
    def place_market_sell(self, option_symbol: str, quantity: int) -> Optional[Dict]:
        """Quick helper for market sell to close"""
        return self.place_option_order(
            option_symbol=option_symbol,
            side="sell_to_close",
            quantity=quantity,
            order_type="market"
        )
    
    def place_limit_sell(self, option_symbol: str, quantity: int, 
                         limit_price: float) -> Optional[Dict]:
        """Place limit sell order (for take profit)"""
        return self.place_option_order(
            option_symbol=option_symbol,
            side="sell_to_close",
            quantity=quantity,
            order_type="limit",
            limit_price=limit_price
        )
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order"""
        result = self._delete(f"/v1/accounts/{self.config.account_id}/orders/{order_id}")
        if result and result.get("order", {}).get("status") == "ok":
            logger.info(f"✅ Order {order_id} cancelled")
            return True
        logger.error(f"❌ Failed to cancel order {order_id}")
        return False
    
    def modify_order(self, order_id: str, order_type: str = None,
                     limit_price: float = None, stop_price: float = None) -> bool:
        """Modify an existing order"""
        data = {}
        if order_type:
            data["type"] = order_type
        if limit_price:
            data["price"] = round(limit_price, 2)
        if stop_price:
            data["stop"] = round(stop_price, 2)
        
        result = self._post(
            f"/v1/accounts/{self.config.account_id}/orders/{order_id}",
            data
        )
        
        if result and "order" in result:
            logger.info(f"✅ Order {order_id} modified")
            return True
        return False

    # ==================== HELPERS ====================
    
    def find_best_option(self, symbol: str, option_type: str, 
                         target_delta: float = 0.40,
                         min_volume: int = 50,
                         min_oi: int = 100,
                         max_spread_pct: float = 0.10,
                         days_to_expiry: Tuple[int, int] = (3, 14)) -> Optional[Dict]:
        """
        Find the best option contract matching criteria
        
        Args:
            symbol: Underlying symbol
            option_type: "call" or "put"
            target_delta: Target delta (0.30-0.50 recommended)
            min_volume: Minimum option volume
            min_oi: Minimum open interest
            max_spread_pct: Maximum bid-ask spread as percentage
            days_to_expiry: (min_days, max_days) tuple
        """
        # Get expirations
        expirations = self.get_option_expirations(symbol)
        if not expirations:
            logger.warning(f"No expirations found for {symbol}")
            return None
        
        # Filter to valid expiration range
        today = datetime.now().date()
        valid_expirations = []
        for exp in expirations:
            exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
            days = (exp_date - today).days
            if days_to_expiry[0] <= days <= days_to_expiry[1]:
                valid_expirations.append(exp)
        
        if not valid_expirations:
            # Fall back to nearest expiration
            valid_expirations = [expirations[0]]
        
        # Search through expirations for best option
        best_option = None
        best_score = -1
        
        for exp in valid_expirations[:2]:  # Check first 2 valid expirations
            chain = self.get_option_chain(symbol, exp)
            
            for opt in chain:
                # Filter by type
                if opt["option_type"] != option_type:
                    continue
                
                # Check volume
                vol = opt.get("volume") or 0
                if vol < min_volume:
                    continue
                
                # Check open interest
                oi = opt.get("open_interest") or 0
                if oi < min_oi:
                    continue
                
                # Check spread
                bid = opt.get("bid") or 0
                ask = opt.get("ask") or 0
                if bid <= 0 or ask <= 0:
                    continue
                
                spread_pct = (ask - bid) / ask
                if spread_pct > max_spread_pct:
                    continue
                
                # Check delta (if available)
                delta = abs(opt.get("delta") or 0)
                
                # Score this option
                # Prefer: delta close to target, high volume, tight spread
                delta_score = max(0, 1 - abs(delta - target_delta) * 2)
                volume_score = min(1, vol / 1000)
                spread_score = 1 - spread_pct
                
                score = delta_score * 0.4 + volume_score * 0.3 + spread_score * 0.3
                
                if score > best_score:
                    best_score = score
                    best_option = opt
        
        return best_option
    
    def get_option_quote(self, option_symbol: str) -> Optional[Dict]:
        """Get quote for a specific option symbol"""
        return self.get_quote(option_symbol)
    
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        clock = self.get_clock()
        if clock:
            return clock.get("state") == "open"
        return False
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            balance = self.get_account_balance()
            if balance:
                logger.info(f"✅ Tradier connected - Account equity: ${balance.get('total_equity', 0):,.2f}")
                return True
        except Exception as e:
            logger.error(f"❌ Tradier connection failed: {e}")
        return False
