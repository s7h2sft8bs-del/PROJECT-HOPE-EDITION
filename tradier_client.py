"""
PROJECT HOPE V2 - Tradier Client
Enhanced with Greeks analysis, IV rank calculation, and smarter option selection
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests

from config import TradierConfig, TradingConfig

logger = logging.getLogger(__name__)


class TradierClient:
    """Tradier API wrapper with enhanced Greeks and IV analysis"""
    
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
        self.min_request_interval = 0.1
        
        # IV history cache for IV rank calculation
        self._iv_cache: Dict[str, List[float]] = {}
    
    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _get(self, endpoint: str, params: dict = None) -> Optional[dict]:
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
        result = self._get(f"/v1/accounts/{self.config.account_id}/orders")
        if result and "orders" in result:
            orders = result["orders"]
            if orders == "null" or orders is None:
                return []
            if isinstance(orders, dict) and "order" in orders:
                order_list = orders["order"]
                if isinstance(order_list, dict):
                    order_list = [order_list]
                return [o for o in order_list if o.get("status") == status]
        return []

    # ==================== MARKET DATA ====================
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
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
                    "close": quote.get("close"),
                    "volume": quote.get("volume"),
                    "average_volume": quote.get("average_volume"),
                    "change": quote.get("change"),
                    "change_pct": quote.get("change_percentage"),
                }
        return None
    
    def get_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
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
    
    def get_option_chain(self, symbol: str, expiration: str = None, 
                         greeks: bool = True) -> List[Dict]:
        """Get option chain with full Greeks data"""
        params = {"symbol": symbol, "greeks": str(greeks).lower()}
        if expiration:
            params["expiration"] = expiration
        
        result = self._get("/v1/markets/options/chains", params)
        options = []
        
        if result and "options" in result:
            chain = result["options"].get("option", [])
            if isinstance(chain, dict):
                chain = [chain]
            
            for opt in chain:
                greeks_data = opt.get("greeks", {}) or {}
                options.append({
                    "symbol": opt.get("symbol"),
                    "underlying": opt.get("underlying"),
                    "strike": opt.get("strike"),
                    "expiration": opt.get("expiration_date"),
                    "option_type": opt.get("option_type"),
                    "last": opt.get("last"),
                    "bid": opt.get("bid"),
                    "ask": opt.get("ask"),
                    "volume": opt.get("volume"),
                    "open_interest": opt.get("open_interest"),
                    # Full Greeks
                    "delta": greeks_data.get("delta", 0),
                    "gamma": greeks_data.get("gamma", 0),
                    "theta": greeks_data.get("theta", 0),
                    "vega": greeks_data.get("vega", 0),
                    "rho": greeks_data.get("rho", 0),
                    "iv": greeks_data.get("mid_iv", 0),  # Implied volatility
                    "phi": greeks_data.get("phi", 0),
                })
        return options
    
    def get_option_expirations(self, symbol: str) -> List[str]:
        result = self._get("/v1/markets/options/expirations", {"symbol": symbol})
        if result and "expirations" in result:
            exp = result["expirations"]
            if exp and "date" in exp:
                dates = exp["date"]
                if isinstance(dates, str):
                    return [dates]
                return dates
        return []
    
    def get_historical(self, symbol: str, interval: str = "daily",
                       start: str = None, end: str = None) -> List[Dict]:
        """Get historical price data"""
        params = {"symbol": symbol, "interval": interval}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        
        result = self._get("/v1/markets/history", params)
        bars = []
        
        if result and "history" in result and result["history"]:
            day_data = result["history"].get("day", [])
            if isinstance(day_data, dict):
                day_data = [day_data]
            for d in day_data:
                bars.append({
                    "date": d.get("date"),
                    "open": d.get("open"),
                    "high": d.get("high"),
                    "low": d.get("low"),
                    "close": d.get("close"),
                    "volume": d.get("volume"),
                })
        return bars
    
    def get_clock(self) -> Optional[Dict]:
        result = self._get("/v1/markets/clock")
        if result and "clock" in result:
            return result["clock"]
        return None

    # ==================== GREEKS & IV ANALYSIS ====================
    
    def calculate_iv_rank(self, symbol: str) -> float:
        """
        Calculate IV Rank (0-100)
        Compares current IV to 52-week IV range
        Low IV Rank = options are cheap
        High IV Rank = options are expensive
        """
        try:
            # Get current ATM option IV
            current_iv = self._get_current_iv(symbol)
            if current_iv <= 0:
                return 50.0  # Default to middle
            
            # Get historical data to estimate IV range
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            history = self.get_historical(symbol, start=start_date, end=end_date)
            if len(history) < 30:
                return 50.0
            
            # Estimate historical volatility from price data
            closes = [bar["close"] for bar in history if bar.get("close")]
            if len(closes) < 30:
                return 50.0
            
            # Calculate rolling 30-day HV
            import math
            hvs = []
            for i in range(30, len(closes)):
                window = closes[i-30:i]
                returns = [math.log(window[j]/window[j-1]) for j in range(1, len(window))]
                if returns:
                    hv = (sum(r**2 for r in returns) / len(returns)) ** 0.5 * (252 ** 0.5)
                    hvs.append(hv)
            
            if not hvs:
                return 50.0
            
            # IV Rank = (Current IV - 52wk Low) / (52wk High - 52wk Low) * 100
            iv_low = min(hvs)
            iv_high = max(hvs)
            
            if iv_high == iv_low:
                return 50.0
            
            iv_rank = ((current_iv - iv_low) / (iv_high - iv_low)) * 100
            return max(0, min(100, iv_rank))
            
        except Exception as e:
            logger.error(f"IV rank calc error for {symbol}: {e}")
            return 50.0
    
    def _get_current_iv(self, symbol: str) -> float:
        """Get current ATM implied volatility"""
        try:
            # Get stock price
            quote = self.get_quote(symbol)
            if not quote:
                return 0
            price = quote.get("last", 0)
            if price <= 0:
                return 0
            
            # Get nearest expiration
            expirations = self.get_option_expirations(symbol)
            if not expirations:
                return 0
            
            # Find expiration 7-14 days out
            today = datetime.now().date()
            target_exp = None
            for exp in expirations:
                exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                days = (exp_date - today).days
                if 5 <= days <= 21:
                    target_exp = exp
                    break
            
            if not target_exp:
                target_exp = expirations[0] if expirations else None
            
            if not target_exp:
                return 0
            
            # Get ATM options
            chain = self.get_option_chain(symbol, target_exp)
            
            # Find option closest to ATM
            best_iv = 0
            best_distance = float('inf')
            
            for opt in chain:
                strike = opt.get("strike", 0)
                iv = opt.get("iv", 0) or 0
                if iv > 0:
                    distance = abs(strike - price)
                    if distance < best_distance:
                        best_distance = distance
                        best_iv = iv
            
            return best_iv
            
        except Exception as e:
            logger.error(f"Current IV error for {symbol}: {e}")
            return 0
    
    def analyze_option_greeks(self, option: dict, stock_price: float) -> dict:
        """
        Analyze option Greeks and return quality assessment
        Returns dict with scores and warnings
        """
        analysis = {
            "score": 0,
            "warnings": [],
            "delta_ok": False,
            "theta_ok": False,
            "iv_ok": False,
            "spread_ok": False,
        }
        
        delta = abs(option.get("delta", 0))
        theta = option.get("theta", 0)
        iv = option.get("iv", 0) or 0
        bid = option.get("bid", 0)
        ask = option.get("ask", 0)
        option_price = (bid + ask) / 2 if bid and ask else option.get("last", 0)
        
        # Delta check (0.25 - 0.55 ideal)
        if 0.25 <= delta <= 0.55:
            analysis["delta_ok"] = True
            analysis["score"] += 25
            if 0.35 <= delta <= 0.45:
                analysis["score"] += 10  # Sweet spot bonus
        else:
            analysis["warnings"].append(f"Delta {delta:.2f} outside 0.25-0.55")
        
        # Theta check (not bleeding too fast)
        if option_price > 0 and theta != 0:
            theta_pct = abs(theta) / option_price
            if theta_pct < 0.05:  # Less than 5% daily decay
                analysis["theta_ok"] = True
                analysis["score"] += 20
            else:
                analysis["warnings"].append(f"Theta decay {theta_pct*100:.1f}%/day too high")
        else:
            analysis["theta_ok"] = True
            analysis["score"] += 15
        
        # IV check
        if iv > 0:
            if 0.15 <= iv <= 0.80:
                analysis["iv_ok"] = True
                analysis["score"] += 20
            elif iv > 0.80:
                analysis["warnings"].append(f"IV {iv*100:.0f}% very high - expensive")
            else:
                analysis["warnings"].append(f"IV {iv*100:.0f}% very low")
        else:
            analysis["iv_ok"] = True
            analysis["score"] += 10
        
        # Spread check
        if bid > 0 and ask > 0:
            spread_pct = (ask - bid) / ask
            if spread_pct < 0.05:
                analysis["spread_ok"] = True
                analysis["score"] += 25
            elif spread_pct < 0.10:
                analysis["spread_ok"] = True
                analysis["score"] += 15
            else:
                analysis["warnings"].append(f"Spread {spread_pct*100:.1f}% too wide")
        
        return analysis

    # ==================== ENHANCED OPTION SELECTION ====================
    
    def find_best_option(self, symbol: str, option_type: str,
                         trading_config: TradingConfig,
                         days_to_expiry: Tuple[int, int] = (3, 14)) -> Optional[Dict]:
        """
        Find best option with full Greeks analysis
        Returns option dict with Greeks quality score
        """
        # Get stock price
        quote = self.get_quote(symbol)
        if not quote:
            return None
        stock_price = quote.get("last", 0)
        if stock_price <= 0:
            return None
        
        # Get expirations
        expirations = self.get_option_expirations(symbol)
        if not expirations:
            logger.warning(f"No expirations found for {symbol}")
            return None
        
        # Filter valid expirations
        today = datetime.now().date()
        valid_expirations = []
        for exp in expirations:
            exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
            days = (exp_date - today).days
            if days_to_expiry[0] <= days <= days_to_expiry[1]:
                valid_expirations.append((exp, days))
        
        if not valid_expirations:
            # Fallback to nearest
            for exp in expirations[:2]:
                exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                days = (exp_date - today).days
                if days >= 1:
                    valid_expirations.append((exp, days))
        
        if not valid_expirations:
            return None
        
        best_option = None
        best_total_score = -1
        
        for exp, days in valid_expirations[:3]:
            chain = self.get_option_chain(symbol, exp)
            
            for opt in chain:
                if opt["option_type"] != option_type:
                    continue
                
                # Basic filters
                vol = opt.get("volume") or 0
                oi = opt.get("open_interest") or 0
                bid = opt.get("bid") or 0
                ask = opt.get("ask") or 0
                
                if vol < trading_config.min_option_volume:
                    continue
                if oi < trading_config.min_open_interest:
                    continue
                if bid <= 0 or ask <= 0:
                    continue
                
                spread_pct = (ask - bid) / ask
                if spread_pct > trading_config.max_spread_pct:
                    continue
                
                # Delta filter
                delta = abs(opt.get("delta", 0))
                if delta < trading_config.min_delta or delta > trading_config.max_delta:
                    continue
                
                # Greeks analysis
                greeks_analysis = self.analyze_option_greeks(opt, stock_price)
                
                # Calculate total score
                delta_score = max(0, 1 - abs(delta - trading_config.target_delta) * 3) * 30
                volume_score = min(20, (vol / 500) * 20)
                oi_score = min(15, (oi / 1000) * 15)
                spread_score = (1 - spread_pct) * 20
                greeks_score = greeks_analysis["score"] * 0.15  # Scale to ~15 pts
                
                total_score = delta_score + volume_score + oi_score + spread_score + greeks_score
                
                if total_score > best_total_score:
                    best_total_score = total_score
                    opt["greeks_analysis"] = greeks_analysis
                    opt["selection_score"] = total_score
                    opt["days_to_expiry"] = days
                    best_option = opt
        
        if best_option:
            logger.info(
                f"🎯 Best option for {symbol}: "
                f"Strike ${best_option['strike']} "
                f"Exp {best_option['expiration']} "
                f"Δ={abs(best_option.get('delta',0)):.2f} "
                f"θ={best_option.get('theta',0):.3f} "
                f"IV={best_option.get('iv',0)*100:.0f}% "
                f"Score={best_total_score:.0f}"
            )
        
        return best_option

    # ==================== ORDER EXECUTION ====================
    
    def place_option_order(self, option_symbol: str, side: str, quantity: int,
                           order_type: str = "market", limit_price: float = None,
                           stop_price: float = None, duration: str = "day") -> Optional[Dict]:
        # Extract underlying from option symbol
        underlying = ""
        for i, c in enumerate(option_symbol):
            if c.isdigit():
                underlying = option_symbol[:i]
                break
        if not underlying:
            underlying = option_symbol[:4].rstrip("0123456789")
        
        data = {
            "class": "option",
            "symbol": underlying,
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
            return {"id": order.get("id"), "status": order.get("status")}
        else:
            logger.error(f"❌ Order failed: {result}")
            return None
    
    def place_market_buy(self, option_symbol: str, quantity: int) -> Optional[Dict]:
        return self.place_option_order(option_symbol, "buy_to_open", quantity, "market")
    
    def place_market_sell(self, option_symbol: str, quantity: int) -> Optional[Dict]:
        return self.place_option_order(option_symbol, "sell_to_close", quantity, "market")
    
    def place_limit_sell(self, option_symbol: str, quantity: int,
                         limit_price: float) -> Optional[Dict]:
        return self.place_option_order(option_symbol, "sell_to_close", quantity, "limit", limit_price)
    
    def cancel_order(self, order_id: str) -> bool:
        result = self._delete(f"/v1/accounts/{self.config.account_id}/orders/{order_id}")
        if result and result.get("order", {}).get("status") == "ok":
            logger.info(f"✅ Order {order_id} cancelled")
            return True
        logger.error(f"❌ Failed to cancel order {order_id}")
        return False
    
    def is_market_open(self) -> bool:
        clock = self.get_clock()
        if clock:
            return clock.get("state") == "open"
        return False
    
    def test_connection(self) -> bool:
        try:
            balance = self.get_account_balance()
            if balance:
                logger.info(f"✅ Tradier connected - Account equity: ${balance.get('total_equity', 0):,.2f}")
                return True
        except Exception as e:
            logger.error(f"❌ Tradier connection failed: {e}")
        return False
