"""Technical indicators for trading strategies."""

import numpy as np
import pandas as pd
from typing import List, Optional, Union
from decimal import Decimal


class TechnicalIndicators:
    """Collection of technical indicators for trading strategies."""
    
    @staticmethod
    def sma(data: List[float], period: int) -> List[float]:
        """Simple Moving Average."""
        if len(data) < period:
            return []
        
        result = []
        for i in range(period - 1, len(data)):
            avg = sum(data[i - period + 1:i + 1]) / period
            result.append(avg)
        
        return result
    
    @staticmethod
    def ema(data: List[float], period: int) -> List[float]:
        """Exponential Moving Average."""
        if len(data) < period:
            return []
        
        multiplier = 2 / (period + 1)
        result = []
        
        # Start with SMA for first value
        sma_first = sum(data[:period]) / period
        result.append(sma_first)
        
        # Calculate EMA for remaining values
        for i in range(period, len(data)):
            ema_value = (data[i] * multiplier) + (result[-1] * (1 - multiplier))
            result.append(ema_value)
        
        return result
    
    @staticmethod
    def rsi(data: List[float], period: int = 14) -> List[float]:
        """Relative Strength Index."""
        if len(data) < period + 1:
            return []
        
        gains = []
        losses = []
        
        # Calculate price changes
        for i in range(1, len(data)):
            change = data[i] - data[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        result = []
        
        # Calculate initial average gain and loss
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        if avg_loss == 0:
            result.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi_value = 100 - (100 / (1 + rs))
            result.append(rsi_value)
        
        # Calculate subsequent RSI values
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                result.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi_value = 100 - (100 / (1 + rs))
                result.append(rsi_value)
        
        return result
    
    @staticmethod
    def macd(data: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> dict:
        """MACD (Moving Average Convergence Divergence)."""
        if len(data) < slow_period:
            return {'macd': [], 'signal': [], 'histogram': []}
        
        fast_ema = TechnicalIndicators.ema(data, fast_period)
        slow_ema = TechnicalIndicators.ema(data, slow_period)
        
        # Align the EMAs (slow EMA starts later)
        offset = slow_period - fast_period
        fast_ema_aligned = fast_ema[offset:]
        
        # Calculate MACD line
        macd_line = [fast - slow for fast, slow in zip(fast_ema_aligned, slow_ema)]
        
        # Calculate signal line (EMA of MACD)
        signal_line = TechnicalIndicators.ema(macd_line, signal_period)
        
        # Calculate histogram
        histogram = []
        signal_offset = len(macd_line) - len(signal_line)
        for i in range(len(signal_line)):
            histogram.append(macd_line[i + signal_offset] - signal_line[i])
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def bollinger_bands(data: List[float], period: int = 20, std_dev: float = 2) -> dict:
        """Bollinger Bands."""
        if len(data) < period:
            return {'upper': [], 'middle': [], 'lower': []}
        
        middle_band = TechnicalIndicators.sma(data, period)
        
        upper_band = []
        lower_band = []
        
        for i in range(period - 1, len(data)):
            window = data[i - period + 1:i + 1]
            std = np.std(window)
            sma_value = middle_band[i - period + 1]
            
            upper_band.append(sma_value + (std_dev * std))
            lower_band.append(sma_value - (std_dev * std))
        
        return {
            'upper': upper_band,
            'middle': middle_band,
            'lower': lower_band
        }
    
    @staticmethod
    def stochastic(high: List[float], low: List[float], close: List[float], 
                   k_period: int = 14, d_period: int = 3) -> dict:
        """Stochastic Oscillator."""
        if len(high) < k_period or len(low) < k_period or len(close) < k_period:
            return {'%K': [], '%D': []}
        
        k_values = []
        
        for i in range(k_period - 1, len(close)):
            highest_high = max(high[i - k_period + 1:i + 1])
            lowest_low = min(low[i - k_period + 1:i + 1])
            
            if highest_high == lowest_low:
                k_value = 50  # Avoid division by zero
            else:
                k_value = ((close[i] - lowest_low) / (highest_high - lowest_low)) * 100
            
            k_values.append(k_value)
        
        # Calculate %D (SMA of %K)
        d_values = TechnicalIndicators.sma(k_values, d_period)
        
        return {
            '%K': k_values,
            '%D': d_values
        }
    
    @staticmethod
    def atr(high: List[float], low: List[float], close: List[float], period: int = 14) -> List[float]:
        """Average True Range."""
        if len(high) < 2 or len(low) < 2 or len(close) < 2:
            return []
        
        true_ranges = []
        
        for i in range(1, len(close)):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i - 1])
            tr3 = abs(low[i] - close[i - 1])
            
            true_range = max(tr1, tr2, tr3)
            true_ranges.append(true_range)
        
        # Calculate ATR using SMA of true ranges
        atr_values = TechnicalIndicators.sma(true_ranges, period)
        
        return atr_values
    
    @staticmethod
    def williams_r(high: List[float], low: List[float], close: List[float], period: int = 14) -> List[float]:
        """Williams %R."""
        if len(high) < period or len(low) < period or len(close) < period:
            return []
        
        williams_r_values = []
        
        for i in range(period - 1, len(close)):
            highest_high = max(high[i - period + 1:i + 1])
            lowest_low = min(low[i - period + 1:i + 1])
            
            if highest_high == lowest_low:
                wr_value = -50  # Avoid division by zero
            else:
                wr_value = ((highest_high - close[i]) / (highest_high - lowest_low)) * -100
            
            williams_r_values.append(wr_value)
        
        return williams_r_values


# Convenience functions for direct access
def sma(data: List[float], period: int) -> List[float]:
    """Simple Moving Average."""
    return TechnicalIndicators.sma(data, period)


def ema(data: List[float], period: int) -> List[float]:
    """Exponential Moving Average."""
    return TechnicalIndicators.ema(data, period)


def rsi(data: List[float], period: int = 14) -> List[float]:
    """Relative Strength Index."""
    return TechnicalIndicators.rsi(data, period)


def macd(data: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> dict:
    """MACD (Moving Average Convergence Divergence)."""
    return TechnicalIndicators.macd(data, fast_period, slow_period, signal_period)


def bollinger_bands(data: List[float], period: int = 20, std_dev: float = 2) -> dict:
    """Bollinger Bands."""
    return TechnicalIndicators.bollinger_bands(data, period, std_dev)


def stochastic(high: List[float], low: List[float], close: List[float], 
               k_period: int = 14, d_period: int = 3) -> dict:
    """Stochastic Oscillator."""
    return TechnicalIndicators.stochastic(high, low, close, k_period, d_period)


def atr(high: List[float], low: List[float], close: List[float], period: int = 14) -> List[float]:
    """Average True Range."""
    return TechnicalIndicators.atr(high, low, close, period)


def williams_r(high: List[float], low: List[float], close: List[float], period: int = 14) -> List[float]:
    """Williams %R."""
    return TechnicalIndicators.williams_r(high, low, close, period)