"""
Advanced Technical Indicators for ML Feature Engineering
Alphintra Trading Platform - Phase 4
"""

import numpy as np
import pandas as pd
import talib
from typing import Dict, List, Optional, Tuple
import asyncio
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class IndicatorType(Enum):
    """Enumeration of indicator types for categorization"""
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    OVERLAP = "overlap"
    PATTERN = "pattern"


@dataclass
class IndicatorConfig:
    """Configuration for technical indicators"""
    name: str
    type: IndicatorType
    period: int
    enabled: bool = True
    params: Optional[Dict] = None


class TechnicalIndicators:
    """
    Advanced technical indicators calculator with ML-optimized features
    Designed for high-frequency feature engineering
    """
    
    def __init__(self):
        self.indicators_config = self._initialize_indicators()
        self.cache = {}
        
    def _initialize_indicators(self) -> List[IndicatorConfig]:
        """Initialize default indicator configurations"""
        return [
            # Trend Indicators
            IndicatorConfig("SMA", IndicatorType.TREND, 10),
            IndicatorConfig("SMA", IndicatorType.TREND, 20),
            IndicatorConfig("SMA", IndicatorType.TREND, 50),
            IndicatorConfig("EMA", IndicatorType.TREND, 12),
            IndicatorConfig("EMA", IndicatorType.TREND, 26),
            IndicatorConfig("MACD", IndicatorType.TREND, 12, params={"fast": 12, "slow": 26, "signal": 9}),
            IndicatorConfig("ADX", IndicatorType.TREND, 14),
            IndicatorConfig("AROON", IndicatorType.TREND, 14),
            IndicatorConfig("PARABOLIC_SAR", IndicatorType.TREND, 0, params={"acceleration": 0.02, "maximum": 0.2}),
            
            # Momentum Indicators
            IndicatorConfig("RSI", IndicatorType.MOMENTUM, 14),
            IndicatorConfig("RSI", IndicatorType.MOMENTUM, 7),
            IndicatorConfig("STOCH", IndicatorType.MOMENTUM, 14, params={"fastk": 5, "slowk": 3}),
            IndicatorConfig("WILLIAMS_R", IndicatorType.MOMENTUM, 14),
            IndicatorConfig("CCI", IndicatorType.MOMENTUM, 20),
            IndicatorConfig("MFI", IndicatorType.MOMENTUM, 14),
            IndicatorConfig("ROC", IndicatorType.MOMENTUM, 10),
            IndicatorConfig("MOMENTUM", IndicatorType.MOMENTUM, 10),
            
            # Volatility Indicators
            IndicatorConfig("BBANDS", IndicatorType.VOLATILITY, 20, params={"std": 2}),
            IndicatorConfig("ATR", IndicatorType.VOLATILITY, 14),
            IndicatorConfig("NATR", IndicatorType.VOLATILITY, 14),
            IndicatorConfig("TRANGE", IndicatorType.VOLATILITY, 1),
            
            # Volume Indicators
            IndicatorConfig("OBV", IndicatorType.VOLUME, 1),
            IndicatorConfig("AD", IndicatorType.VOLUME, 1),
            IndicatorConfig("ADOSC", IndicatorType.VOLUME, 3, params={"fast": 3, "slow": 10}),
            IndicatorConfig("CHAIKIN_MF", IndicatorType.VOLUME, 20),
        ]
    
    async def compute_all_indicators(self, 
                                   ohlcv_data: pd.DataFrame,
                                   symbol: str = None) -> Dict[str, np.ndarray]:
        """
        Compute all enabled technical indicators for the given OHLCV data
        
        Args:
            ohlcv_data: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
            symbol: Symbol identifier for caching
            
        Returns:
            Dictionary mapping indicator names to their values
        """
        try:
            # Validate input data
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in ohlcv_data.columns for col in required_columns):
                raise ValueError(f"OHLCV data must contain columns: {required_columns}")
            
            if len(ohlcv_data) < 100:  # Minimum data points for reliable indicators
                logger.warning(f"Limited data points ({len(ohlcv_data)}) for indicator calculation")
            
            # Extract OHLCV arrays
            open_prices = ohlcv_data['open'].values.astype(np.float64)
            high_prices = ohlcv_data['high'].values.astype(np.float64)
            low_prices = ohlcv_data['low'].values.astype(np.float64)
            close_prices = ohlcv_data['close'].values.astype(np.float64)
            volume = ohlcv_data['volume'].values.astype(np.float64)
            
            indicators = {}
            
            # Compute indicators in parallel for different categories
            tasks = [
                self._compute_trend_indicators(open_prices, high_prices, low_prices, close_prices),
                self._compute_momentum_indicators(high_prices, low_prices, close_prices),
                self._compute_volatility_indicators(high_prices, low_prices, close_prices),
                self._compute_volume_indicators(high_prices, low_prices, close_prices, volume),
                self._compute_overlap_indicators(close_prices),
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Merge all indicator results
            for result in results:
                indicators.update(result)
            
            # Add custom ML-specific features
            ml_features = await self._compute_ml_features(ohlcv_data)
            indicators.update(ml_features)
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error computing indicators: {str(e)}")
            raise
    
    async def _compute_trend_indicators(self, open_prices, high_prices, low_prices, close_prices) -> Dict:
        """Compute trend-following indicators"""
        indicators = {}
        
        try:
            # Moving Averages
            indicators['sma_10'] = talib.SMA(close_prices, timeperiod=10)
            indicators['sma_20'] = talib.SMA(close_prices, timeperiod=20)
            indicators['sma_50'] = talib.SMA(close_prices, timeperiod=50)
            indicators['ema_12'] = talib.EMA(close_prices, timeperiod=12)
            indicators['ema_26'] = talib.EMA(close_prices, timeperiod=26)
            
            # MACD
            macd, macd_signal, macd_hist = talib.MACD(close_prices, fastperiod=12, slowperiod=26, signalperiod=9)
            indicators['macd'] = macd
            indicators['macd_signal'] = macd_signal
            indicators['macd_histogram'] = macd_hist
            
            # ADX (Average Directional Index)
            indicators['adx'] = talib.ADX(high_prices, low_prices, close_prices, timeperiod=14)
            indicators['plus_di'] = talib.PLUS_DI(high_prices, low_prices, close_prices, timeperiod=14)
            indicators['minus_di'] = talib.MINUS_DI(high_prices, low_prices, close_prices, timeperiod=14)
            
            # Aroon
            aroon_down, aroon_up = talib.AROON(high_prices, low_prices, timeperiod=14)
            indicators['aroon_up'] = aroon_up
            indicators['aroon_down'] = aroon_down
            indicators['aroon_osc'] = talib.AROONOSC(high_prices, low_prices, timeperiod=14)
            
            # Parabolic SAR
            indicators['sar'] = talib.SAR(high_prices, low_prices, acceleration=0.02, maximum=0.2)
            
            # Trend strength indicators
            indicators['price_vs_sma20'] = (close_prices / indicators['sma_20']) - 1
            indicators['sma_slope_20'] = np.gradient(indicators['sma_20'])
            
        except Exception as e:
            logger.error(f"Error computing trend indicators: {str(e)}")
            
        return indicators
    
    async def _compute_momentum_indicators(self, high_prices, low_prices, close_prices) -> Dict:
        """Compute momentum oscillators"""
        indicators = {}
        
        try:
            # RSI (Relative Strength Index)
            indicators['rsi_14'] = talib.RSI(close_prices, timeperiod=14)
            indicators['rsi_7'] = talib.RSI(close_prices, timeperiod=7)
            
            # Stochastic Oscillator
            slowk, slowd = talib.STOCH(high_prices, low_prices, close_prices, 
                                     fastk_period=5, slowk_period=3, slowk_matype=0,
                                     slowd_period=3, slowd_matype=0)
            indicators['stoch_k'] = slowk
            indicators['stoch_d'] = slowd
            
            # Williams %R
            indicators['williams_r'] = talib.WILLR(high_prices, low_prices, close_prices, timeperiod=14)
            
            # CCI (Commodity Channel Index)
            indicators['cci'] = talib.CCI(high_prices, low_prices, close_prices, timeperiod=20)
            
            # MFI (Money Flow Index)
            # Note: MFI needs volume, will be computed in volume indicators
            
            # ROC (Rate of Change)
            indicators['roc_10'] = talib.ROC(close_prices, timeperiod=10)
            indicators['roc_5'] = talib.ROC(close_prices, timeperiod=5)
            
            # Momentum
            indicators['momentum_10'] = talib.MOM(close_prices, timeperiod=10)
            
            # Custom momentum features
            indicators['rsi_divergence'] = self._calculate_rsi_divergence(close_prices, indicators['rsi_14'])
            indicators['momentum_acceleration'] = np.gradient(np.gradient(close_prices))
            
        except Exception as e:
            logger.error(f"Error computing momentum indicators: {str(e)}")
            
        return indicators
    
    async def _compute_volatility_indicators(self, high_prices, low_prices, close_prices) -> Dict:
        """Compute volatility indicators"""
        indicators = {}
        
        try:
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close_prices, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
            indicators['bb_upper'] = bb_upper
            indicators['bb_middle'] = bb_middle
            indicators['bb_lower'] = bb_lower
            indicators['bb_width'] = (bb_upper - bb_lower) / bb_middle
            indicators['bb_position'] = (close_prices - bb_lower) / (bb_upper - bb_lower)
            
            # ATR (Average True Range)
            indicators['atr'] = talib.ATR(high_prices, low_prices, close_prices, timeperiod=14)
            indicators['natr'] = talib.NATR(high_prices, low_prices, close_prices, timeperiod=14)
            
            # True Range
            indicators['trange'] = talib.TRANGE(high_prices, low_prices, close_prices)
            
            # Custom volatility features
            indicators['volatility_ratio'] = indicators['atr'] / close_prices
            indicators['high_low_ratio'] = (high_prices - low_prices) / close_prices
            indicators['price_range_position'] = (close_prices - low_prices) / (high_prices - low_prices)
            
            # Rolling volatility
            returns = np.diff(close_prices) / close_prices[:-1]
            indicators['realized_vol_20'] = pd.Series(returns).rolling(20).std().values
            
        except Exception as e:
            logger.error(f"Error computing volatility indicators: {str(e)}")
            
        return indicators
    
    async def _compute_volume_indicators(self, high_prices, low_prices, close_prices, volume) -> Dict:
        """Compute volume-based indicators"""
        indicators = {}
        
        try:
            # On-Balance Volume
            indicators['obv'] = talib.OBV(close_prices, volume)
            
            # Accumulation/Distribution Line
            indicators['ad'] = talib.AD(high_prices, low_prices, close_prices, volume)
            
            # Accumulation/Distribution Oscillator
            indicators['adosc'] = talib.ADOSC(high_prices, low_prices, close_prices, volume, fastperiod=3, slowperiod=10)
            
            # Money Flow Index
            indicators['mfi'] = talib.MFI(high_prices, low_prices, close_prices, volume, timeperiod=14)
            
            # Volume-weighted features
            indicators['vwap'] = self._calculate_vwap(high_prices, low_prices, close_prices, volume)
            indicators['volume_ratio'] = volume / np.mean(volume[-20:])  # Volume vs 20-period average
            indicators['price_volume_correlation'] = self._rolling_correlation(close_prices, volume, 20)
            
        except Exception as e:
            logger.error(f"Error computing volume indicators: {str(e)}")
            
        return indicators
    
    async def _compute_overlap_indicators(self, close_prices) -> Dict:
        """Compute price overlap studies"""
        indicators = {}
        
        try:
            # Triangular Moving Average
            indicators['trima'] = talib.TRIMA(close_prices, timeperiod=30)
            
            # Weighted Moving Average
            indicators['wma'] = talib.WMA(close_prices, timeperiod=30)
            
            # Double Exponential Moving Average
            indicators['dema'] = talib.DEMA(close_prices, timeperiod=30)
            
            # Triple Exponential Moving Average
            indicators['tema'] = talib.TEMA(close_prices, timeperiod=30)
            
            # Kaufman Adaptive Moving Average
            indicators['kama'] = talib.KAMA(close_prices, timeperiod=30)
            
            # MESA Adaptive Moving Average
            mama, fama = talib.MAMA(close_prices, fastlimit=0.5, slowlimit=0.05)
            indicators['mama'] = mama
            indicators['fama'] = fama
            
        except Exception as e:
            logger.error(f"Error computing overlap indicators: {str(e)}")
            
        return indicators
    
    async def _compute_ml_features(self, ohlcv_data: pd.DataFrame) -> Dict:
        """Compute ML-specific features for better model performance"""
        indicators = {}
        
        try:
            close_prices = ohlcv_data['close'].values
            high_prices = ohlcv_data['high'].values
            low_prices = ohlcv_data['low'].values
            volume = ohlcv_data['volume'].values
            
            # Statistical features
            indicators['returns'] = np.diff(close_prices) / close_prices[:-1]
            indicators['log_returns'] = np.diff(np.log(close_prices))
            
            # Multi-timeframe features
            for period in [5, 10, 20, 50]:
                indicators[f'return_{period}d'] = (close_prices / np.roll(close_prices, period)) - 1
                indicators[f'volatility_{period}d'] = pd.Series(indicators['returns']).rolling(period).std().values
                indicators[f'max_drawdown_{period}d'] = self._calculate_rolling_max_drawdown(close_prices, period)
            
            # Market microstructure features
            indicators['bid_ask_spread_proxy'] = (high_prices - low_prices) / close_prices
            indicators['price_impact'] = np.abs(indicators['returns']) / (volume / np.mean(volume))
            
            # Fractal features
            indicators['hurst_exponent'] = self._calculate_hurst_exponent(close_prices)
            indicators['fractal_dimension'] = 2 - indicators['hurst_exponent']
            
            # Seasonal features
            if 'timestamp' in ohlcv_data.columns:
                timestamps = pd.to_datetime(ohlcv_data['timestamp'])
                indicators['hour_of_day'] = timestamps.dt.hour
                indicators['day_of_week'] = timestamps.dt.dayofweek
                indicators['month_of_year'] = timestamps.dt.month
                indicators['quarter'] = timestamps.dt.quarter
            
            # Regime detection features
            indicators['volatility_regime'] = self._detect_volatility_regime(close_prices)
            indicators['trend_regime'] = self._detect_trend_regime(close_prices)
            
        except Exception as e:
            logger.error(f"Error computing ML features: {str(e)}")
            
        return indicators
    
    def _calculate_rsi_divergence(self, prices: np.ndarray, rsi: np.ndarray, window: int = 20) -> np.ndarray:
        """Calculate RSI divergence signal"""
        try:
            price_trend = np.gradient(pd.Series(prices).rolling(window).mean().values)
            rsi_trend = np.gradient(pd.Series(rsi).rolling(window).mean().values)
            
            # Divergence occurs when price and RSI trends are opposite
            divergence = np.where((price_trend > 0) & (rsi_trend < 0), 1,  # Bearish divergence
                                np.where((price_trend < 0) & (rsi_trend > 0), -1, 0))  # Bullish divergence
            
            return divergence
        except:
            return np.zeros_like(prices)
    
    def _calculate_vwap(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """Calculate Volume Weighted Average Price"""
        try:
            typical_price = (high + low + close) / 3
            vwap = np.cumsum(typical_price * volume) / np.cumsum(volume)
            return vwap
        except:
            return np.full_like(close, np.nan)
    
    def _rolling_correlation(self, x: np.ndarray, y: np.ndarray, window: int) -> np.ndarray:
        """Calculate rolling correlation between two series"""
        try:
            df = pd.DataFrame({'x': x, 'y': y})
            correlation = df['x'].rolling(window).corr(df['y']).values
            return correlation
        except:
            return np.full_like(x, np.nan)
    
    def _calculate_rolling_max_drawdown(self, prices: np.ndarray, window: int) -> np.ndarray:
        """Calculate rolling maximum drawdown"""
        try:
            df = pd.DataFrame({'price': prices})
            rolling_max = df['price'].rolling(window).max()
            drawdown = (df['price'] - rolling_max) / rolling_max
            max_drawdown = drawdown.rolling(window).min().values
            return max_drawdown
        except:
            return np.full_like(prices, np.nan)
    
    def _calculate_hurst_exponent(self, prices: np.ndarray, lags: List[int] = None) -> float:
        """Calculate Hurst exponent for fractal analysis"""
        try:
            if lags is None:
                lags = range(2, min(100, len(prices) // 4))
            
            # Calculate log returns
            log_returns = np.diff(np.log(prices))
            
            # Calculate RS statistic for different lags
            rs_values = []
            for lag in lags:
                if lag >= len(log_returns):
                    continue
                    
                # Divide returns into segments
                segments = [log_returns[i:i+lag] for i in range(0, len(log_returns), lag) 
                           if i+lag <= len(log_returns)]
                
                rs_list = []
                for segment in segments:
                    if len(segment) < lag:
                        continue
                    
                    # Calculate mean and cumulative deviations
                    mean_return = np.mean(segment)
                    cumulative_deviations = np.cumsum(segment - mean_return)
                    
                    # Calculate range and standard deviation
                    R = np.max(cumulative_deviations) - np.min(cumulative_deviations)
                    S = np.std(segment)
                    
                    if S > 0:
                        rs_list.append(R / S)
                
                if rs_list:
                    rs_values.append(np.mean(rs_list))
            
            if len(rs_values) < 2:
                return 0.5  # Default value for insufficient data
            
            # Linear regression of log(RS) vs log(lag)
            log_lags = np.log(lags[:len(rs_values)])
            log_rs = np.log(rs_values)
            
            # Remove any invalid values
            valid_idx = np.isfinite(log_lags) & np.isfinite(log_rs)
            if np.sum(valid_idx) < 2:
                return 0.5
            
            hurst = np.polyfit(log_lags[valid_idx], log_rs[valid_idx], 1)[0]
            
            # Ensure Hurst exponent is in valid range
            return np.clip(hurst, 0.0, 1.0)
            
        except:
            return 0.5  # Default value for any errors
    
    def _detect_volatility_regime(self, prices: np.ndarray, window: int = 50) -> np.ndarray:
        """Detect volatility regime (high/low volatility periods)"""
        try:
            returns = np.diff(prices) / prices[:-1]
            rolling_vol = pd.Series(returns).rolling(window).std().values
            vol_median = np.nanmedian(rolling_vol)
            
            # High volatility regime = 1, Low volatility regime = 0
            regime = np.where(rolling_vol > vol_median, 1, 0)
            return np.concatenate([[0], regime])  # Pad for length consistency
        except:
            return np.zeros_like(prices)
    
    def _detect_trend_regime(self, prices: np.ndarray, window: int = 50) -> np.ndarray:
        """Detect trend regime (trending/ranging markets)"""
        try:
            # Calculate ADX-like trend strength
            high = prices  # Simplified - using close as proxy
            low = prices
            
            atr = pd.Series(np.abs(np.diff(prices))).rolling(window).mean().values
            price_change = np.abs(prices - np.roll(prices, window))
            
            trend_strength = price_change / (atr * window)
            trend_median = np.nanmedian(trend_strength)
            
            # Trending regime = 1, Ranging regime = 0
            regime = np.where(trend_strength > trend_median, 1, 0)
            return regime
        except:
            return np.zeros_like(prices)
    
    def get_feature_importance_scores(self, indicators: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Calculate feature importance scores based on various criteria"""
        importance_scores = {}
        
        for name, values in indicators.items():
            try:
                # Skip if all values are NaN or constant
                if np.all(np.isnan(values)) or np.var(values) == 0:
                    importance_scores[name] = 0.0
                    continue
                
                # Calculate importance based on multiple criteria
                variance_score = np.var(values[~np.isnan(values)])
                autocorr_score = self._calculate_autocorrelation(values)
                stability_score = 1 / (1 + np.sum(np.isnan(values)) / len(values))
                
                # Combine scores (weights can be adjusted)
                combined_score = (0.4 * variance_score + 
                                0.3 * autocorr_score + 
                                0.3 * stability_score)
                
                importance_scores[name] = combined_score
                
            except Exception as e:
                logger.warning(f"Error calculating importance for {name}: {str(e)}")
                importance_scores[name] = 0.0
        
        # Normalize scores
        max_score = max(importance_scores.values()) if importance_scores else 1.0
        if max_score > 0:
            importance_scores = {k: v / max_score for k, v in importance_scores.items()}
        
        return importance_scores
    
    def _calculate_autocorrelation(self, values: np.ndarray, lag: int = 1) -> float:
        """Calculate autocorrelation for a given lag"""
        try:
            valid_values = values[~np.isnan(values)]
            if len(valid_values) < lag + 1:
                return 0.0
            
            correlation = np.corrcoef(valid_values[:-lag], valid_values[lag:])[0, 1]
            return abs(correlation) if not np.isnan(correlation) else 0.0
        except:
            return 0.0


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_technical_indicators():
        """Test the technical indicators calculator"""
        
        # Generate sample OHLCV data
        np.random.seed(42)
        n_points = 1000
        
        # Simulate realistic price data
        returns = np.random.normal(0.001, 0.02, n_points)
        prices = 100 * np.exp(np.cumsum(returns))
        
        # Add some noise to create OHLCV
        noise = np.random.normal(0, 0.5, n_points)
        
        sample_data = pd.DataFrame({
            'open': prices + noise,
            'high': prices + abs(noise) + np.random.uniform(0, 2, n_points),
            'low': prices - abs(noise) - np.random.uniform(0, 2, n_points),
            'close': prices,
            'volume': np.random.uniform(1000, 10000, n_points),
            'timestamp': pd.date_range(start='2023-01-01', periods=n_points, freq='1min')
        })
        
        # Initialize indicators calculator
        indicators_calc = TechnicalIndicators()
        
        # Compute all indicators
        print("Computing technical indicators...")
        indicators = await indicators_calc.compute_all_indicators(sample_data, "TEST_SYMBOL")
        
        print(f"Computed {len(indicators)} indicators:")
        for name, values in indicators.items():
            valid_count = np.sum(~np.isnan(values))
            print(f"  {name}: {valid_count}/{len(values)} valid values")
        
        # Calculate feature importance
        importance_scores = indicators_calc.get_feature_importance_scores(indicators)
        
        print("\nTop 10 most important features:")
        sorted_features = sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)
        for name, score in sorted_features[:10]:
            print(f"  {name}: {score:.4f}")
    
    # Run the test
    asyncio.run(test_technical_indicators())