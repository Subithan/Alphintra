"""
Market data access and indicator calculations for trading strategies.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from decimal import Decimal
import pandas as pd
import numpy as np


class OHLCV:
    """Represents a single OHLCV bar."""
    
    def __init__(self, timestamp: datetime, open_price: float, high: float, 
                 low: float, close: float, volume: float):
        self.timestamp = timestamp
        self.open = open_price
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume
        }


class MarketData:
    """
    Provides access to market data and common calculations.
    """
    
    def __init__(self, data_provider=None):
        self.data_provider = data_provider
        self._data_cache: Dict[str, pd.DataFrame] = {}
        self._current_bar_index: Dict[str, int] = {}
        self.current_time: Optional[datetime] = None
        
    def set_current_time(self, timestamp: datetime):
        """Set the current timestamp for backtesting."""
        self.current_time = timestamp
        
    def load_data(self, symbol: str, start_date: datetime = None, 
                  end_date: datetime = None, timeframe: str = "1d") -> pd.DataFrame:
        """
        Load historical data for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSD', 'AAPL')
            start_date: Start date for data
            end_date: End date for data
            timeframe: Data timeframe ('1m', '5m', '1h', '1d', etc.)
            
        Returns:
            DataFrame with OHLCV data
        """
        cache_key = f"{symbol},{timeframe}"
        
        if cache_key not in self._data_cache:
            if self.data_provider:
                data = self.data_provider.get_data(symbol, start_date, end_date, timeframe)
            else:
                # Generate sample data for testing
                data = self._generate_sample_data(symbol, start_date, end_date, timeframe)
            
            self._data_cache[cache_key] = data
            self._current_bar_index[cache_key] = 0
        
        return self._data_cache[cache_key]
    
    def get_current_bar(self, symbol: str, timeframe: str = "1d") -> Optional[OHLCV]:
        """Get the current OHLCV bar for a symbol."""
        cache_key = f"{symbol},{timeframe}"
        
        if cache_key not in self._data_cache:
            return None
        
        data = self._data_cache[cache_key]
        current_index = self._current_bar_index.get(cache_key, 0)
        
        if current_index >= len(data):
            return None
        
        row = data.iloc[current_index]
        return OHLCV(
            timestamp=row.name,
            open_price=row['open'],
            high=row['high'],
            low=row['low'],
            close=row['close'],
            volume=row['volume']
        )
    
    def get_current_price(self, symbol: str, timeframe: str = "1d") -> Optional[float]:
        """Get the current price (close price of current bar)."""
        bar = self.get_current_bar(symbol, timeframe)
        return bar.close if bar else None
    
    def get_bars(self, symbol: str, count: int, timeframe: str = "1d") -> List[OHLCV]:
        """Get the last N bars for a symbol."""
        cache_key = f"{symbol},{timeframe}"
        
        if cache_key not in self._data_cache:
            return []
        
        data = self._data_cache[cache_key]
        current_index = self._current_bar_index.get(cache_key, 0)
        
        start_index = max(0, current_index - count + 1)
        end_index = current_index + 1
        
        bars = []
        for i in range(start_index, end_index):
            if i < len(data):
                row = data.iloc[i]
                bars.append(OHLCV(
                    timestamp=row.name,
                    open_price=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=row['volume']
                ))
        
        return bars
    
    def get_prices(self, symbol: str, count: int, price_type: str = "close", 
                   timeframe: str = "1d") -> List[float]:
        """
        Get a list of prices.
        
        Args:
            symbol: Trading symbol
            count: Number of prices to retrieve
            price_type: Type of price ('open', 'high', 'low', 'close')
            timeframe: Data timeframe
            
        Returns:
            List of prices
        """
        bars = self.get_bars(symbol, count, timeframe)
        
        prices = []
        for bar in bars:
            if price_type == "open":
                prices.append(bar.open)
            elif price_type == "high":
                prices.append(bar.high)
            elif price_type == "low":
                prices.append(bar.low)
            elif price_type == "close":
                prices.append(bar.close)
            elif price_type == "volume":
                prices.append(bar.volume)
            else:
                prices.append(bar.close)
        
        return prices
    
    def advance_bar(self, symbol: str, timeframe: str = "1d"):
        """Advance to the next bar (used in backtesting)."""
        cache_key = f"{symbol},{timeframe}"
        if cache_key in self._current_bar_index:
            self._current_bar_index[cache_key] += 1
    
    # Technical Indicators
    def sma(self, symbol: str, period: int, timeframe: str = "1d") -> Optional[float]:
        """Simple Moving Average."""
        prices = self.get_prices(symbol, period, "close", timeframe)
        
        if len(prices) < period:
            return None
        
        return sum(prices[-period:]) / period
    
    def ema(self, symbol: str, period: int, timeframe: str = "1d") -> Optional[float]:
        """Exponential Moving Average."""
        prices = self.get_prices(symbol, period * 2, "close", timeframe)  # Get more data for EMA
        
        if len(prices) < period:
            return None
        
        # Calculate EMA
        multiplier = 2 / (period + 1)
        ema_values = [prices[0]]  # Start with first price
        
        for price in prices[1:]:
            ema_value = (price * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(ema_value)
        
        return ema_values[-1]
    
    def rsi(self, symbol: str, period: int = 14, timeframe: str = "1d") -> Optional[float]:
        """Relative Strength Index."""
        prices = self.get_prices(symbol, period + 1, "close", timeframe)
        
        if len(prices) < period + 1:
            return None
        
        # Calculate price changes
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # Separate gains and losses
        gains = [change if change > 0 else 0 for change in changes]
        losses = [-change if change < 0 else 0 for change in changes]
        
        # Calculate average gain and loss
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def bollinger_bands(self, symbol: str, period: int = 20, std_dev: float = 2.0,
                       timeframe: str = "1d") -> Optional[Dict[str, float]]:
        """Bollinger Bands."""
        prices = self.get_prices(symbol, period, "close", timeframe)
        
        if len(prices) < period:
            return None
        
        sma = sum(prices[-period:]) / period
        
        # Calculate standard deviation
        variance = sum((price - sma) ** 2 for price in prices[-period:]) / period
        std = variance ** 0.5
        
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        
        return {
            "upper": upper_band,
            "middle": sma,
            "lower": lower_band,
            "bandwidth": (upper_band - lower_band) / sma
        }
    
    def macd(self, symbol: str, fast_period: int = 12, slow_period: int = 26,
             signal_period: int = 9, timeframe: str = "1d") -> Optional[Dict[str, float]]:
        """MACD (Moving Average Convergence Divergence)."""
        # Need enough data for slow EMA
        required_bars = slow_period * 2
        
        if not hasattr(self, '_macd_cache'):
            self._macd_cache = {}
        
        cache_key = f"{symbol},{timeframe},{fast_period},{slow_period},{signal_period}"
        
        # Get historical MACD values for signal calculation
        if cache_key not in self._macd_cache:
            self._macd_cache[cache_key] = []
        
        fast_ema = self.ema(symbol, fast_period, timeframe)
        slow_ema = self.ema(symbol, slow_period, timeframe)
        
        if fast_ema is None or slow_ema is None:
            return None
        
        macd_line = fast_ema - slow_ema
        
        # Add to cache for signal calculation
        self._macd_cache[cache_key].append(macd_line)
        
        # Keep only necessary values
        if len(self._macd_cache[cache_key]) > signal_period * 2:
            self._macd_cache[cache_key] = self._macd_cache[cache_key][-signal_period * 2:]
        
        # Calculate signal line (EMA of MACD)
        if len(self._macd_cache[cache_key]) < signal_period:
            signal_line = macd_line  # Not enough data for signal
        else:
            macd_values = self._macd_cache[cache_key][-signal_period:]
            signal_line = sum(macd_values) / len(macd_values)  # Simple average for now
        
        histogram = macd_line - signal_line
        
        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }
    
    def _generate_sample_data(self, symbol: str, start_date: datetime = None,
                             end_date: datetime = None, timeframe: str = "1d") -> pd.DataFrame:
        """Generate sample data for testing purposes."""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)
        if end_date is None:
            end_date = datetime.now()
        
        # Generate date range
        if timeframe == "1d":
            freq = "D"
        elif timeframe == "1h":
            freq = "H"
        elif timeframe == "1m":
            freq = "T"
        else:
            freq = "D"
        
        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
        
        # Generate realistic price data using random walk
        np.random.seed(hash(symbol) % 2**32)  # Consistent seed based on symbol
        
        base_price = 100.0
        if "BTC" in symbol.upper():
            base_price = 45000.0
        elif "ETH" in symbol.upper():
            base_price = 3000.0
        elif "AAPL" in symbol.upper():
            base_price = 150.0
        
        # Generate price movements
        returns = np.random.normal(0.0005, 0.02, len(date_range))  # Daily return ~0.05%, volatility ~2%
        prices = [base_price]
        
        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(max(new_price, 0.01))  # Ensure positive prices
        
        # Generate OHLCV data
        data = []
        for i, (timestamp, price) in enumerate(zip(date_range, prices)):
            # Generate intraday high/low
            volatility = abs(np.random.normal(0, 0.01))
            high = price * (1 + volatility)
            low = price * (1 - volatility)
            
            # Ensure OHLC consistency
            open_price = prices[i-1] if i > 0 else price
            close_price = price
            
            # Adjust for consistency
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            
            # Generate volume
            volume = abs(np.random.normal(1000000, 200000))
            
            data.append({
                "open": open_price,
                "high": high,
                "low": low,
                "close": close_price,
                "volume": volume
            })
        
        df = pd.DataFrame(data, index=date_range)
        return df


class Indicator:
    """Base class for custom indicators."""
    
    def __init__(self, name: str):
        self.name = name
        self.data: List[float] = []
        
    def update(self, value: float):
        """Update indicator with new value."""
        self.data.append(value)
        
    def get_value(self) -> Optional[float]:
        """Get current indicator value."""
        return self.data[-1] if self.data else None
    
    def get_values(self, count: int) -> List[float]:
        """Get last N indicator values."""
        return self.data[-count:] if len(self.data) >= count else self.data


class TechnicalIndicators:
    """
    Collection of technical indicators for strategies.
    """
    
    @staticmethod
    def sma(prices: List[float], period: int) -> Optional[float]:
        """Simple Moving Average."""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
    
    @staticmethod
    def ema(prices: List[float], period: int) -> Optional[float]:
        """Exponential Moving Average."""
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """Relative Strength Index."""
        if len(prices) < period + 1:
            return None
        
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [max(0, change) for change in changes]
        losses = [max(0, -change) for change in changes]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def stochastic(highs: List[float], lows: List[float], closes: List[float],
                   k_period: int = 14, d_period: int = 3) -> Optional[Dict[str, float]]:
        """Stochastic Oscillator."""
        if len(closes) < k_period:
            return None
        
        # Calculate %K
        recent_high = max(highs[-k_period:])
        recent_low = min(lows[-k_period:])
        current_close = closes[-1]
        
        if recent_high == recent_low:
            k_percent = 50.0
        else:
            k_percent = ((current_close - recent_low) / (recent_high - recent_low)) * 100
        
        return {
            "k": k_percent,
            "d": k_percent  # Simplified - should be SMA of %K
        }