"""
PROJECT HOPE V2 - WebSocket Streaming Client
Real-time market data via Tradier WebSocket API
Provides tick-by-tick trade, quote, and summary data
"""

import asyncio
import json
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional
import requests

from config import TradierConfig

logger = logging.getLogger(__name__)


@dataclass
class Tick:
    """Single market data tick"""
    symbol: str
    price: float
    size: int
    volume: int  # cumulative volume
    bid: float
    ask: float
    timestamp: datetime
    tick_type: str  # "trade", "quote", "summary"
    high: float = 0.0
    low: float = 0.0
    open: float = 0.0
    prev_close: float = 0.0


@dataclass
class CandleBar:
    """OHLCV candle bar built from ticks"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    tick_count: int = 0
    vwap_numerator: float = 0.0  # sum of price * volume
    
    @property
    def typical_price(self) -> float:
        return (self.high + self.low + self.close) / 3


class StreamingClient:
    """
    Tradier WebSocket streaming client
    Builds real-time candles from tick data
    """
    
    def __init__(self, config: TradierConfig):
        self.config = config
        self.session_id: Optional[str] = None
        self.ws = None
        self.running = False
        self._thread: Optional[threading.Thread] = None
        
        # Callbacks
        self._on_tick: Optional[Callable] = None
        self._on_candle: Optional[Callable] = None
        self._on_summary: Optional[Callable] = None
        
        # Candle building (1-minute candles)
        self._current_candles: Dict[str, CandleBar] = {}
        self._candle_interval = 60  # 1-minute candles
        self._last_candle_time: Dict[str, datetime] = {}
        
        # Tick storage (last 100 per symbol for analysis)
        self._ticks: Dict[str, deque] = {}
        self._max_ticks = 200
        
        # 5-minute candles for multi-timeframe
        self._5min_candles: Dict[str, deque] = {}
        self._current_5min_candles: Dict[str, CandleBar] = {}
        self._max_candles = 100
        
        # 1-minute candle history
        self._1min_candles: Dict[str, deque] = {}
        
        # Connection state
        self.connected = False
        self.reconnect_count = 0
        self.max_reconnects = 50
        self.last_data_time = 0
        
        # Summary data (open, high, low, prev close)
        self.summaries: Dict[str, dict] = {}
        
        # Latest quotes
        self.latest_quotes: Dict[str, dict] = {}
    
    def create_session(self) -> bool:
        """Create streaming session with Tradier"""
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Accept": "application/json"
            }
            response = requests.post(
                self.config.stream_session_url,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            if "stream" in data:
                self.session_id = data["stream"]["sessionid"]
                logger.info(f"✅ Streaming session created: {self.session_id[:8]}...")
                return True
            else:
                logger.error(f"❌ No stream data in response: {data}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to create streaming session: {e}")
            return False
    
    def start(self, symbols: List[str], 
              on_tick: Callable = None,
              on_candle: Callable = None,
              on_summary: Callable = None):
        """Start streaming in background thread"""
        self._on_tick = on_tick
        self._on_candle = on_candle
        self._on_summary = on_summary
        
        # Initialize storage for all symbols
        for sym in symbols:
            if sym not in self._ticks:
                self._ticks[sym] = deque(maxlen=self._max_ticks)
            if sym not in self._1min_candles:
                self._1min_candles[sym] = deque(maxlen=self._max_candles)
            if sym not in self._5min_candles:
                self._5min_candles[sym] = deque(maxlen=self._max_candles)
        
        self.running = True
        self._symbols = symbols
        self._thread = threading.Thread(
            target=self._run_stream_loop,
            args=(symbols,),
            daemon=True
        )
        self._thread.start()
        logger.info(f"🔌 WebSocket stream started for {len(symbols)} symbols")
    
    def stop(self):
        """Stop streaming"""
        self.running = False
        self.connected = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("🔌 WebSocket stream stopped")
    
    def _run_stream_loop(self, symbols: List[str]):
        """Main stream loop with reconnection logic"""
        while self.running and self.reconnect_count < self.max_reconnects:
            try:
                asyncio.run(self._connect_and_stream(symbols))
            except Exception as e:
                logger.error(f"❌ Stream error: {e}")
            
            if self.running:
                self.reconnect_count += 1
                wait_time = min(30, 2 ** min(self.reconnect_count, 5))
                logger.warning(f"🔄 Reconnecting in {wait_time}s (attempt {self.reconnect_count})")
                time.sleep(wait_time)
                
                # Get new session
                self.create_session()
        
        if self.reconnect_count >= self.max_reconnects:
            logger.error("❌ Max reconnection attempts reached")
    
    async def _connect_and_stream(self, symbols: List[str]):
        """Connect to WebSocket and stream data"""
        try:
            import websockets
        except ImportError:
            logger.error("❌ websockets package not installed. pip install websockets")
            return
        
        if not self.session_id:
            if not self.create_session():
                return
        
        uri = self.config.ws_url
        logger.info(f"🔌 Connecting to {uri}")
        
        async with websockets.connect(uri, ssl=True, compression=None) as ws:
            self.ws = ws
            self.connected = True
            self.reconnect_count = 0
            logger.info("✅ WebSocket connected")
            
            # Subscribe to symbols
            symbol_str = ",".join(symbols)
            payload = json.dumps({
                "symbols": symbols,
                "filter": ["trade", "quote", "summary"],
                "sessionid": self.session_id,
                "linebreak": True
            })
            await ws.send(payload)
            logger.info(f"📡 Subscribed to {len(symbols)} symbols")
            
            # Receive loop
            async for message in ws:
                if not self.running:
                    break
                
                self.last_data_time = time.time()
                
                try:
                    data = json.loads(message)
                    self._process_message(data)
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        
        self.connected = False
    
    def _process_message(self, data: dict):
        """Process incoming WebSocket message"""
        msg_type = data.get("type")
        symbol = data.get("symbol")
        
        if not symbol or not msg_type:
            return
        
        if msg_type == "trade":
            self._process_trade(data)
        elif msg_type == "quote":
            self._process_quote(data)
        elif msg_type == "summary":
            self._process_summary(data)
    
    def _process_trade(self, data: dict):
        """Process trade tick - builds candles"""
        symbol = data["symbol"]
        price = float(data.get("price", 0) or data.get("last", 0))
        size = int(data.get("size", 0))
        cvol = int(data.get("cvol", 0))
        
        if price <= 0:
            return
        
        now = datetime.now()
        
        # Get current bid/ask from latest quote
        latest = self.latest_quotes.get(symbol, {})
        bid = latest.get("bid", price)
        ask = latest.get("ask", price)
        
        # Get summary data
        summary = self.summaries.get(symbol, {})
        
        tick = Tick(
            symbol=symbol,
            price=price,
            size=size,
            volume=cvol,
            bid=bid,
            ask=ask,
            timestamp=now,
            tick_type="trade",
            high=summary.get("high", price),
            low=summary.get("low", price),
            open=summary.get("open", price),
            prev_close=summary.get("prev_close", 0)
        )
        
        # Store tick
        if symbol not in self._ticks:
            self._ticks[symbol] = deque(maxlen=self._max_ticks)
        self._ticks[symbol].append(tick)
        
        # Build candles
        self._update_candle(symbol, tick, self._current_candles, self._1min_candles, 60)
        self._update_candle(symbol, tick, self._current_5min_candles, self._5min_candles, 300)
        
        # Callback
        if self._on_tick:
            try:
                self._on_tick(tick)
            except Exception as e:
                logger.error(f"Tick callback error: {e}")
    
    def _process_quote(self, data: dict):
        """Process quote update (bid/ask)"""
        symbol = data["symbol"]
        self.latest_quotes[symbol] = {
            "bid": float(data.get("bid", 0)),
            "ask": float(data.get("ask", 0)),
            "bidsize": int(data.get("bidsz", 0)),
            "asksize": int(data.get("asksz", 0)),
        }
    
    def _process_summary(self, data: dict):
        """Process summary (open, high, low, prev close)"""
        symbol = data["symbol"]
        self.summaries[symbol] = {
            "open": float(data.get("open", 0)),
            "high": float(data.get("high", 0)),
            "low": float(data.get("low", 0)),
            "prev_close": float(data.get("prevClose", 0)),
        }
        
        if self._on_summary:
            try:
                self._on_summary(symbol, self.summaries[symbol])
            except Exception as e:
                logger.error(f"Summary callback error: {e}")
    
    def _update_candle(self, symbol: str, tick: Tick,
                       current_candles: dict, candle_history: dict, 
                       interval_seconds: int):
        """Update or create candle from tick"""
        now = tick.timestamp
        
        # Round down to candle period
        total_seconds = now.hour * 3600 + now.minute * 60 + now.second
        candle_start_seconds = (total_seconds // interval_seconds) * interval_seconds
        candle_time = now.replace(
            hour=candle_start_seconds // 3600,
            minute=(candle_start_seconds % 3600) // 60,
            second=0,
            microsecond=0
        )
        
        if symbol in current_candles:
            candle = current_candles[symbol]
            
            if candle.timestamp == candle_time:
                # Update existing candle
                candle.high = max(candle.high, tick.price)
                candle.low = min(candle.low, tick.price)
                candle.close = tick.price
                candle.volume = tick.volume  # cumulative
                candle.tick_count += 1
                candle.vwap_numerator += tick.price * tick.size
            else:
                # New candle period - save old candle
                if symbol not in candle_history:
                    candle_history[symbol] = deque(maxlen=self._max_candles)
                candle_history[symbol].append(candle)
                
                # Fire candle callback
                if self._on_candle and interval_seconds == 60:
                    try:
                        self._on_candle(candle)
                    except Exception as e:
                        logger.error(f"Candle callback error: {e}")
                
                # Create new candle
                current_candles[symbol] = CandleBar(
                    symbol=symbol,
                    timestamp=candle_time,
                    open=tick.price,
                    high=tick.price,
                    low=tick.price,
                    close=tick.price,
                    volume=tick.volume,
                    tick_count=1,
                    vwap_numerator=tick.price * tick.size
                )
        else:
            # First candle for this symbol
            current_candles[symbol] = CandleBar(
                symbol=symbol,
                timestamp=candle_time,
                open=tick.price,
                high=tick.price,
                low=tick.price,
                close=tick.price,
                volume=tick.volume,
                tick_count=1,
                vwap_numerator=tick.price * tick.size
            )
            if symbol not in candle_history:
                candle_history[symbol] = deque(maxlen=self._max_candles)
    
    # ==================== DATA ACCESS ====================
    
    def get_latest_price(self, symbol: str) -> float:
        """Get latest price for symbol"""
        ticks = self._ticks.get(symbol)
        if ticks and len(ticks) > 0:
            return ticks[-1].price
        return 0.0
    
    def get_latest_tick(self, symbol: str) -> Optional[Tick]:
        """Get latest tick"""
        ticks = self._ticks.get(symbol)
        if ticks and len(ticks) > 0:
            return ticks[-1]
        return None
    
    def get_ticks(self, symbol: str, count: int = 50) -> List[Tick]:
        """Get recent ticks"""
        ticks = self._ticks.get(symbol)
        if not ticks:
            return []
        return list(ticks)[-count:]
    
    def get_1min_candles(self, symbol: str, count: int = 50) -> List[CandleBar]:
        """Get 1-minute candle history"""
        candles = list(self._1min_candles.get(symbol, []))
        # Include current forming candle
        if symbol in self._current_candles:
            candles.append(self._current_candles[symbol])
        return candles[-count:]
    
    def get_5min_candles(self, symbol: str, count: int = 50) -> List[CandleBar]:
        """Get 5-minute candle history"""
        candles = list(self._5min_candles.get(symbol, []))
        if symbol in self._current_5min_candles:
            candles.append(self._current_5min_candles[symbol])
        return candles[-count:]
    
    def get_bid_ask(self, symbol: str) -> tuple:
        """Get current bid/ask"""
        quote = self.latest_quotes.get(symbol, {})
        return quote.get("bid", 0), quote.get("ask", 0)
    
    def get_spread_pct(self, symbol: str) -> float:
        """Get bid-ask spread as percentage"""
        bid, ask = self.get_bid_ask(symbol)
        if ask > 0:
            return (ask - bid) / ask
        return 1.0
    
    def get_summary(self, symbol: str) -> dict:
        """Get daily summary (open, high, low, prev_close)"""
        return self.summaries.get(symbol, {})
    
    def get_tick_count(self, symbol: str) -> int:
        """Get number of ticks received"""
        return len(self._ticks.get(symbol, []))
    
    def get_cumulative_volume(self, symbol: str) -> int:
        """Get latest cumulative volume"""
        ticks = self._ticks.get(symbol)
        if ticks and len(ticks) > 0:
            return ticks[-1].volume
        return 0
    
    def is_healthy(self) -> bool:
        """Check if stream is healthy"""
        if not self.connected:
            return False
        # Check for stale data (no data for 30 seconds during market hours)
        if self.last_data_time > 0:
            stale_seconds = time.time() - self.last_data_time
            if stale_seconds > 30:
                return False
        return True
