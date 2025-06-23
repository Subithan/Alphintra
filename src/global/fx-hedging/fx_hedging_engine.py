"""
FX Hedging Engine
Alphintra Trading Platform - Phase 5
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import uuid
from concurrent.futures import ThreadPoolExecutor

# Financial calculations
from scipy.optimize import minimize
import scipy.stats as stats

# Market data
import yfinance as yf
import aiohttp
import aioredis

# Monitoring
from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


class Currency(Enum):
    """Major currency enumeration"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CHF = "CHF"
    CAD = "CAD"
    AUD = "AUD"
    NZD = "NZD"
    SGD = "SGD"
    HKD = "HKD"
    CNY = "CNY"
    KRW = "KRW"


class HedgeType(Enum):
    """FX hedge type enumeration"""
    FORWARD = "forward"
    SPOT = "spot"
    OPTION = "option"
    SWAP = "swap"
    NDF = "ndf"  # Non-Deliverable Forward
    COLLAR = "collar"


class HedgeStrategy(Enum):
    """FX hedging strategy enumeration"""
    FULL_HEDGE = "full_hedge"
    PARTIAL_HEDGE = "partial_hedge"
    DYNAMIC_HEDGE = "dynamic_hedge"
    SELECTIVE_HEDGE = "selective_hedge"
    NO_HEDGE = "no_hedge"


@dataclass
class CurrencyExposure:
    """Currency exposure data structure"""
    base_currency: Currency
    exposure_currency: Currency
    exposure_amount: float
    market_value_base: float
    unrealized_pnl: float
    hedge_ratio: float
    last_updated: datetime


@dataclass
class FXRate:
    """FX rate data structure"""
    base_currency: Currency
    quote_currency: Currency
    bid: float
    ask: float
    mid: float
    timestamp: datetime
    source: str
    
    @property
    def spread(self) -> float:
        return self.ask - self.bid
    
    @property
    def spread_bps(self) -> float:
        return (self.spread / self.mid) * 10000


@dataclass
class HedgeInstrument:
    """FX hedge instrument data structure"""
    instrument_id: str
    hedge_type: HedgeType
    base_currency: Currency
    quote_currency: Currency
    notional_amount: float
    hedge_ratio: float
    maturity_date: Optional[datetime]
    strike_rate: Optional[float]
    premium: Optional[float]
    created_at: datetime
    
    # For options
    option_type: Optional[str] = None  # call/put
    volatility: Optional[float] = None
    
    # For forwards
    forward_rate: Optional[float] = None
    forward_points: Optional[float] = None


@dataclass
class HedgeRecommendation:
    """Hedge recommendation data structure"""
    recommendation_id: str
    exposure: CurrencyExposure
    recommended_strategy: HedgeStrategy
    recommended_instruments: List[HedgeInstrument]
    expected_cost: float
    expected_risk_reduction: float
    confidence_score: float
    reasoning: str
    created_at: datetime


class FXDataProvider:
    """
    Provides real-time and historical FX data from multiple sources
    """
    
    def __init__(self):
        self.data_sources = {
            'bloomberg': 'https://api.bloomberg.com/fx',
            'reuters': 'https://api.refinitiv.com/fx',
            'yahoo': 'https://query1.finance.yahoo.com/v8/finance/chart',
            'alpha_vantage': 'https://www.alphavantage.co/query',
            'fixer': 'https://api.fixer.io/latest'
        }
        
        self.rate_cache = {}
        self.cache_duration = timedelta(seconds=30)  # Cache for 30 seconds
        
        # Metrics
        self.fx_data_requests = Counter('fx_data_requests_total', 'FX data requests', ['source', 'currency_pair'])
        self.fx_data_latency = Histogram('fx_data_latency_seconds', 'FX data retrieval latency', ['source'])
        
    async def get_fx_rate(self, base_currency: Currency, quote_currency: Currency) -> Optional[FXRate]:
        """Get current FX rate between two currencies"""
        try:
            currency_pair = f"{base_currency.value}{quote_currency.value}"
            
            # Check cache first
            cache_key = currency_pair
            if cache_key in self.rate_cache:
                cached_rate, cache_time = self.rate_cache[cache_key]
                if datetime.now() - cache_time < self.cache_duration:
                    return cached_rate
            
            # Fetch from multiple sources
            start_time = time.time()
            
            # Try primary source (Yahoo Finance for demo)
            rate = await self._fetch_from_yahoo(base_currency, quote_currency)
            
            if rate:
                # Cache the result
                self.rate_cache[cache_key] = (rate, datetime.now())
                
                # Update metrics
                latency = time.time() - start_time
                self.fx_data_latency.labels(source='yahoo').observe(latency)
                self.fx_data_requests.labels(
                    source='yahoo', 
                    currency_pair=currency_pair
                ).inc()
                
                return rate
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting FX rate for {base_currency.value}/{quote_currency.value}: {str(e)}")
            return None
    
    async def _fetch_from_yahoo(self, base_currency: Currency, quote_currency: Currency) -> Optional[FXRate]:
        """Fetch FX rate from Yahoo Finance"""
        try:
            # Handle special cases
            if base_currency == quote_currency:
                return FXRate(
                    base_currency=base_currency,
                    quote_currency=quote_currency,
                    bid=1.0,
                    ask=1.0,
                    mid=1.0,
                    timestamp=datetime.now(),
                    source='yahoo'
                )
            
            # Create currency pair symbol
            symbol = f"{base_currency.value}{quote_currency.value}=X"
            
            # Use synchronous yfinance (run in executor)
            loop = asyncio.get_event_loop()
            ticker_data = await loop.run_in_executor(
                None, 
                lambda: yf.Ticker(symbol).history(period="1d", interval="1m").tail(1)
            )
            
            if not ticker_data.empty:
                close_price = ticker_data['Close'].iloc[-1]
                
                # Estimate bid/ask spread (simplified)
                spread_bps = 5  # 5 basis points default spread
                spread = close_price * (spread_bps / 10000)
                
                return FXRate(
                    base_currency=base_currency,
                    quote_currency=quote_currency,
                    bid=close_price - spread/2,
                    ask=close_price + spread/2,
                    mid=close_price,
                    timestamp=datetime.now(),
                    source='yahoo'
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching from Yahoo Finance: {str(e)}")
            return None
    
    async def get_historical_rates(self, base_currency: Currency, quote_currency: Currency, 
                                 days: int = 30) -> pd.DataFrame:
        """Get historical FX rates"""
        try:
            symbol = f"{base_currency.value}{quote_currency.value}=X"
            
            # Use synchronous yfinance (run in executor)
            loop = asyncio.get_event_loop()
            historical_data = await loop.run_in_executor(
                None,
                lambda: yf.Ticker(symbol).history(period=f"{days}d")
            )
            
            return historical_data
            
        except Exception as e:
            logger.error(f"Error getting historical rates: {str(e)}")
            return pd.DataFrame()
    
    async def get_volatility(self, base_currency: Currency, quote_currency: Currency, 
                           days: int = 30) -> float:
        """Calculate FX volatility"""
        try:
            historical_data = await self.get_historical_rates(base_currency, quote_currency, days)
            
            if len(historical_data) > 1:
                # Calculate daily returns
                returns = historical_data['Close'].pct_change().dropna()
                
                # Annualized volatility
                volatility = returns.std() * np.sqrt(252)
                
                return volatility
            
            return 0.15  # Default 15% volatility
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {str(e)}")
            return 0.15


class ExposureCalculator:
    """
    Calculates currency exposures from portfolio positions
    """
    
    def __init__(self, base_currency: Currency = Currency.USD):
        self.base_currency = base_currency
        self.fx_data_provider = FXDataProvider()
        
    async def calculate_portfolio_exposures(self, portfolio: Dict[str, Any]) -> List[CurrencyExposure]:
        """Calculate all currency exposures in portfolio"""
        try:
            exposures = []
            currency_totals = {}
            
            # Analyze each position
            for symbol, position in portfolio.get('positions', {}).items():
                position_currency = self._get_position_currency(symbol)
                position_value = position['quantity'] * position['price']
                
                if position_currency in currency_totals:
                    currency_totals[position_currency] += position_value
                else:
                    currency_totals[position_currency] = position_value
            
            # Create exposure objects
            for currency, total_value in currency_totals.items():
                if currency != self.base_currency.value:
                    exposure_currency = Currency(currency)
                    
                    # Convert to base currency
                    fx_rate = await self.fx_data_provider.get_fx_rate(exposure_currency, self.base_currency)
                    base_value = total_value * fx_rate.mid if fx_rate else total_value
                    
                    exposure = CurrencyExposure(
                        base_currency=self.base_currency,
                        exposure_currency=exposure_currency,
                        exposure_amount=total_value,
                        market_value_base=base_value,
                        unrealized_pnl=0.0,  # Would calculate based on historical positions
                        hedge_ratio=0.0,
                        last_updated=datetime.now()
                    )
                    
                    exposures.append(exposure)
            
            return exposures
            
        except Exception as e:
            logger.error(f"Error calculating portfolio exposures: {str(e)}")
            return []
    
    def _get_position_currency(self, symbol: str) -> str:
        """Determine currency for a position symbol"""
        # Simplified currency mapping based on symbol
        currency_mapping = {
            # US stocks
            'AAPL': 'USD', 'GOOGL': 'USD', 'MSFT': 'USD', 'TSLA': 'USD',
            # European stocks
            'ASML': 'EUR', 'SAP': 'EUR', 'LVMH': 'EUR',
            # UK stocks
            'BARC': 'GBP', 'BP': 'GBP', 'LLOY': 'GBP',
            # Japanese stocks
            'TSM': 'JPY', 'SONY': 'JPY', 'NTT': 'JPY',
            # Default
            'default': 'USD'
        }
        
        return currency_mapping.get(symbol, 'USD')
    
    async def calculate_exposure_sensitivity(self, exposure: CurrencyExposure, 
                                           shock_size: float = 0.01) -> Dict[str, float]:
        """Calculate sensitivity of exposure to FX moves"""
        try:
            # Get current FX rate
            current_rate = await self.fx_data_provider.get_fx_rate(
                exposure.exposure_currency, 
                exposure.base_currency
            )
            
            if not current_rate:
                return {}
            
            # Calculate sensitivity metrics
            current_value = exposure.exposure_amount * current_rate.mid
            
            # Delta (change in value for 1% FX move)
            delta = exposure.exposure_amount * current_rate.mid * shock_size
            
            # Gamma (change in delta for 1% FX move) - simplified
            gamma = delta * shock_size
            
            # Value at Risk (1% move)
            var_1pct = abs(delta)
            
            return {
                'delta': delta,
                'gamma': gamma,
                'var_1pct': var_1pct,
                'current_value': current_value,
                'shock_size': shock_size
            }
            
        except Exception as e:
            logger.error(f"Error calculating exposure sensitivity: {str(e)}")
            return {}


class HedgeOptimizer:
    """
    Optimizes FX hedging strategies using portfolio optimization techniques
    """
    
    def __init__(self):
        self.fx_data_provider = FXDataProvider()
        
    async def optimize_hedge_strategy(self, exposures: List[CurrencyExposure], 
                                    risk_tolerance: float = 0.05) -> List[HedgeRecommendation]:
        """Optimize hedging strategy for given exposures"""
        try:
            recommendations = []
            
            for exposure in exposures:
                # Analyze individual exposure
                recommendation = await self._optimize_single_exposure(exposure, risk_tolerance)
                if recommendation:
                    recommendations.append(recommendation)
            
            # Portfolio-level optimization
            portfolio_recommendation = await self._optimize_portfolio_hedge(exposures, risk_tolerance)
            if portfolio_recommendation:
                recommendations.append(portfolio_recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error optimizing hedge strategy: {str(e)}")
            return []
    
    async def _optimize_single_exposure(self, exposure: CurrencyExposure, 
                                      risk_tolerance: float) -> Optional[HedgeRecommendation]:
        """Optimize hedging for single currency exposure"""
        try:
            # Get FX volatility
            volatility = await self.fx_data_provider.get_volatility(
                exposure.exposure_currency, 
                exposure.base_currency
            )
            
            # Calculate risk metrics
            exposure_var = exposure.market_value_base * volatility * np.sqrt(1/252)  # Daily VaR
            
            # Determine if hedging is needed
            if exposure_var / exposure.market_value_base < risk_tolerance:
                recommended_strategy = HedgeStrategy.NO_HEDGE
                hedge_ratio = 0.0
            elif exposure_var / exposure.market_value_base < risk_tolerance * 2:
                recommended_strategy = HedgeStrategy.PARTIAL_HEDGE
                hedge_ratio = 0.5
            else:
                recommended_strategy = HedgeStrategy.FULL_HEDGE
                hedge_ratio = 1.0
            
            # Generate hedge instruments
            instruments = []
            if hedge_ratio > 0:
                # Forward hedge
                forward_instrument = await self._create_forward_hedge(exposure, hedge_ratio)
                if forward_instrument:
                    instruments.append(forward_instrument)
                
                # Option hedge (for partial hedging)
                if recommended_strategy == HedgeStrategy.PARTIAL_HEDGE:
                    option_instrument = await self._create_option_hedge(exposure, hedge_ratio * 0.5)
                    if option_instrument:
                        instruments.append(option_instrument)
            
            # Calculate costs and benefits
            expected_cost = sum(instr.premium or 0 for instr in instruments)
            expected_risk_reduction = hedge_ratio * exposure_var
            
            # Confidence score based on volatility and liquidity
            confidence_score = min(1.0, 0.8 + (0.2 * (1 - min(volatility, 0.5) / 0.5)))
            
            return HedgeRecommendation(
                recommendation_id=str(uuid.uuid4()),
                exposure=exposure,
                recommended_strategy=recommended_strategy,
                recommended_instruments=instruments,
                expected_cost=expected_cost,
                expected_risk_reduction=expected_risk_reduction,
                confidence_score=confidence_score,
                reasoning=f"Volatility: {volatility:.2%}, VaR: {exposure_var:,.0f}, Risk tolerance: {risk_tolerance:.2%}",
                created_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error optimizing single exposure: {str(e)}")
            return None
    
    async def _optimize_portfolio_hedge(self, exposures: List[CurrencyExposure], 
                                      risk_tolerance: float) -> Optional[HedgeRecommendation]:
        """Optimize hedging at portfolio level"""
        try:
            if len(exposures) < 2:
                return None
            
            # Calculate correlation matrix
            correlation_matrix = await self._calculate_fx_correlations(exposures)
            
            # Portfolio optimization using mean-variance approach
            optimal_hedges = await self._solve_portfolio_optimization(exposures, correlation_matrix, risk_tolerance)
            
            # Create portfolio-level recommendation
            if optimal_hedges:
                # Create aggregated exposure
                total_exposure_value = sum(exp.market_value_base for exp in exposures)
                
                portfolio_exposure = CurrencyExposure(
                    base_currency=exposures[0].base_currency,
                    exposure_currency=Currency.USD,  # Multi-currency portfolio
                    exposure_amount=total_exposure_value,
                    market_value_base=total_exposure_value,
                    unrealized_pnl=sum(exp.unrealized_pnl for exp in exposures),
                    hedge_ratio=np.mean([hedge['ratio'] for hedge in optimal_hedges]),
                    last_updated=datetime.now()
                )
                
                # Generate portfolio hedge instruments
                portfolio_instruments = []
                for hedge in optimal_hedges:
                    instrument = await self._create_portfolio_hedge_instrument(hedge)
                    if instrument:
                        portfolio_instruments.append(instrument)
                
                return HedgeRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    exposure=portfolio_exposure,
                    recommended_strategy=HedgeStrategy.DYNAMIC_HEDGE,
                    recommended_instruments=portfolio_instruments,
                    expected_cost=sum(instr.premium or 0 for instr in portfolio_instruments),
                    expected_risk_reduction=sum(hedge['risk_reduction'] for hedge in optimal_hedges),
                    confidence_score=0.85,
                    reasoning="Portfolio-level optimization considering correlations",
                    created_at=datetime.now()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error optimizing portfolio hedge: {str(e)}")
            return None
    
    async def _create_forward_hedge(self, exposure: CurrencyExposure, hedge_ratio: float) -> Optional[HedgeInstrument]:
        """Create forward hedge instrument"""
        try:
            # Get current FX rate
            current_rate = await self.fx_data_provider.get_fx_rate(
                exposure.exposure_currency, 
                exposure.base_currency
            )
            
            if not current_rate:
                return None
            
            # Calculate forward rate (simplified)
            maturity_date = datetime.now() + timedelta(days=90)  # 3-month forward
            forward_points = 0.001  # Simplified forward points
            forward_rate = current_rate.mid + forward_points
            
            notional = exposure.exposure_amount * hedge_ratio
            
            return HedgeInstrument(
                instrument_id=f"FWD_{uuid.uuid4().hex[:8]}",
                hedge_type=HedgeType.FORWARD,
                base_currency=exposure.base_currency,
                quote_currency=exposure.exposure_currency,
                notional_amount=notional,
                hedge_ratio=hedge_ratio,
                maturity_date=maturity_date,
                strike_rate=None,
                premium=0.0,  # No premium for forwards
                created_at=datetime.now(),
                forward_rate=forward_rate,
                forward_points=forward_points
            )
            
        except Exception as e:
            logger.error(f"Error creating forward hedge: {str(e)}")
            return None
    
    async def _create_option_hedge(self, exposure: CurrencyExposure, hedge_ratio: float) -> Optional[HedgeInstrument]:
        """Create option hedge instrument"""
        try:
            # Get current FX rate and volatility
            current_rate = await self.fx_data_provider.get_fx_rate(
                exposure.exposure_currency, 
                exposure.base_currency
            )
            
            volatility = await self.fx_data_provider.get_volatility(
                exposure.exposure_currency, 
                exposure.base_currency
            )
            
            if not current_rate:
                return None
            
            # Option parameters
            maturity_date = datetime.now() + timedelta(days=30)  # 1-month option
            strike_rate = current_rate.mid * 1.02  # 2% out-of-the-money
            notional = exposure.exposure_amount * hedge_ratio
            
            # Calculate option premium using Black-Scholes (simplified)
            premium = self._calculate_option_premium(
                current_rate.mid, strike_rate, volatility, 30/365, 0.02  # 30 days, 2% risk-free rate
            )
            
            return HedgeInstrument(
                instrument_id=f"OPT_{uuid.uuid4().hex[:8]}",
                hedge_type=HedgeType.OPTION,
                base_currency=exposure.base_currency,
                quote_currency=exposure.exposure_currency,
                notional_amount=notional,
                hedge_ratio=hedge_ratio,
                maturity_date=maturity_date,
                strike_rate=strike_rate,
                premium=premium * notional,
                created_at=datetime.now(),
                option_type="put",  # Put option to hedge long exposure
                volatility=volatility
            )
            
        except Exception as e:
            logger.error(f"Error creating option hedge: {str(e)}")
            return None
    
    def _calculate_option_premium(self, spot: float, strike: float, volatility: float, 
                                time_to_expiry: float, risk_free_rate: float) -> float:
        """Calculate option premium using Black-Scholes formula"""
        try:
            from scipy.stats import norm
            
            d1 = (np.log(spot / strike) + (risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / (volatility * np.sqrt(time_to_expiry))
            d2 = d1 - volatility * np.sqrt(time_to_expiry)
            
            # Put option price
            put_price = strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) - spot * norm.cdf(-d1)
            
            return max(put_price, 0.001)  # Minimum premium
            
        except Exception as e:
            logger.error(f"Error calculating option premium: {str(e)}")
            return 0.01  # Default premium
    
    async def _calculate_fx_correlations(self, exposures: List[CurrencyExposure]) -> np.ndarray:
        """Calculate FX correlation matrix"""
        try:
            currencies = [exp.exposure_currency for exp in exposures]
            n = len(currencies)
            
            correlation_matrix = np.eye(n)
            
            for i in range(n):
                for j in range(i+1, n):
                    # Get historical data for both currencies
                    hist1 = await self.fx_data_provider.get_historical_rates(
                        currencies[i], exposures[0].base_currency, 30
                    )
                    hist2 = await self.fx_data_provider.get_historical_rates(
                        currencies[j], exposures[0].base_currency, 30
                    )
                    
                    if len(hist1) > 10 and len(hist2) > 10:
                        # Calculate correlation
                        returns1 = hist1['Close'].pct_change().dropna()
                        returns2 = hist2['Close'].pct_change().dropna()
                        
                        # Align dates
                        common_dates = returns1.index.intersection(returns2.index)
                        if len(common_dates) > 5:
                            corr = returns1[common_dates].corr(returns2[common_dates])
                            correlation_matrix[i, j] = correlation_matrix[j, i] = corr
                    else:
                        # Default correlation
                        correlation_matrix[i, j] = correlation_matrix[j, i] = 0.3
            
            return correlation_matrix
            
        except Exception as e:
            logger.error(f"Error calculating FX correlations: {str(e)}")
            # Return identity matrix as fallback
            return np.eye(len(exposures))
    
    async def _solve_portfolio_optimization(self, exposures: List[CurrencyExposure], 
                                          correlation_matrix: np.ndarray, 
                                          risk_tolerance: float) -> List[Dict[str, Any]]:
        """Solve portfolio optimization for hedge ratios"""
        try:
            from scipy.optimize import minimize
            
            n = len(exposures)
            exposure_values = [exp.market_value_base for exp in exposures]
            
            # Get volatilities
            volatilities = []
            for exp in exposures:
                vol = await self.fx_data_provider.get_volatility(
                    exp.exposure_currency, exp.base_currency
                )
                volatilities.append(vol)
            
            volatilities = np.array(volatilities)
            
            # Objective function: minimize portfolio variance
            def objective(hedge_ratios):
                # Portfolio variance with hedging
                portfolio_var = 0
                for i in range(n):
                    for j in range(n):
                        weight_i = exposure_values[i] / sum(exposure_values)
                        weight_j = exposure_values[j] / sum(exposure_values)
                        unhedged_var_i = (1 - hedge_ratios[i]) * volatilities[i]
                        unhedged_var_j = (1 - hedge_ratios[j]) * volatilities[j]
                        portfolio_var += weight_i * weight_j * unhedged_var_i * unhedged_var_j * correlation_matrix[i, j]
                
                return portfolio_var
            
            # Constraints
            constraints = []
            
            # Hedge ratios between 0 and 1
            bounds = [(0, 1) for _ in range(n)]
            
            # Risk tolerance constraint
            def risk_constraint(hedge_ratios):
                portfolio_var = objective(hedge_ratios)
                return risk_tolerance - np.sqrt(portfolio_var)
            
            constraints.append({'type': 'ineq', 'fun': risk_constraint})
            
            # Initial guess
            x0 = np.array([0.5] * n)
            
            # Solve optimization
            result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
            
            if result.success:
                optimal_hedges = []
                for i, hedge_ratio in enumerate(result.x):
                    if hedge_ratio > 0.01:  # Only include significant hedges
                        optimal_hedges.append({
                            'exposure_index': i,
                            'currency': exposures[i].exposure_currency,
                            'ratio': hedge_ratio,
                            'risk_reduction': hedge_ratio * exposure_values[i] * volatilities[i]
                        })
                
                return optimal_hedges
            
            return []
            
        except Exception as e:
            logger.error(f"Error solving portfolio optimization: {str(e)}")
            return []
    
    async def _create_portfolio_hedge_instrument(self, hedge: Dict[str, Any]) -> Optional[HedgeInstrument]:
        """Create hedge instrument for portfolio optimization result"""
        try:
            # Create a forward instrument for the optimized hedge
            currency = hedge['currency']
            hedge_ratio = hedge['ratio']
            
            return HedgeInstrument(
                instrument_id=f"PRTF_{uuid.uuid4().hex[:8]}",
                hedge_type=HedgeType.FORWARD,
                base_currency=Currency.USD,  # Assuming USD base
                quote_currency=currency,
                notional_amount=hedge['risk_reduction'] / hedge_ratio,
                hedge_ratio=hedge_ratio,
                maturity_date=datetime.now() + timedelta(days=60),
                strike_rate=None,
                premium=0.0,
                created_at=datetime.now(),
                forward_rate=1.0  # Simplified
            )
            
        except Exception as e:
            logger.error(f"Error creating portfolio hedge instrument: {str(e)}")
            return None


class FXHedgingEngine:
    """
    Main FX hedging engine that coordinates all hedging activities
    """
    
    def __init__(self, base_currency: Currency = Currency.USD):
        self.base_currency = base_currency
        self.fx_data_provider = FXDataProvider()
        self.exposure_calculator = ExposureCalculator(base_currency)
        self.hedge_optimizer = HedgeOptimizer()
        
        # Active hedges tracking
        self.active_hedges = {}
        self.hedge_performance = {}
        
        # Risk limits
        self.risk_limits = {
            'max_single_exposure': 10000000,  # $10M
            'max_total_exposure': 50000000,   # $50M
            'max_daily_var': 1000000,         # $1M
            'max_hedge_cost': 0.02            # 2% of exposure
        }
        
        # Metrics
        self.hedge_executions = Counter('hedge_executions_total', 'Hedge executions', ['currency', 'hedge_type'])
        self.hedge_costs = Histogram('hedge_costs', 'Hedge costs in basis points', ['currency'])
        self.fx_exposure_gauge = Gauge('fx_exposure_total', 'Total FX exposure', ['currency'])
        
        logger.info(f"FX Hedging Engine initialized with base currency: {base_currency.value}")
    
    async def analyze_and_hedge_portfolio(self, portfolio: Dict[str, Any], 
                                        risk_tolerance: float = 0.05) -> Dict[str, Any]:
        """Main method to analyze portfolio and execute hedging strategy"""
        try:
            start_time = time.time()
            
            logger.info("Starting FX hedging analysis for portfolio")
            
            # Step 1: Calculate exposures
            exposures = await self.exposure_calculator.calculate_portfolio_exposures(portfolio)
            
            if not exposures:
                return {'success': True, 'message': 'No FX exposures found', 'hedges': []}
            
            # Step 2: Check risk limits
            risk_check = await self._check_risk_limits(exposures)
            if not risk_check['compliant']:
                logger.warning(f"Risk limit breach detected: {risk_check['violations']}")
            
            # Step 3: Optimize hedging strategy
            recommendations = await self.hedge_optimizer.optimize_hedge_strategy(exposures, risk_tolerance)
            
            # Step 4: Execute recommended hedges
            executed_hedges = []
            for recommendation in recommendations:
                if self._should_execute_hedge(recommendation):
                    hedge_result = await self._execute_hedge(recommendation)
                    if hedge_result['success']:
                        executed_hedges.append(hedge_result)
            
            # Step 5: Update tracking and metrics
            await self._update_hedge_tracking(executed_hedges)
            await self._update_metrics(exposures, executed_hedges)
            
            processing_time = time.time() - start_time
            
            result = {
                'success': True,
                'processing_time': processing_time,
                'exposures_analyzed': len(exposures),
                'recommendations_generated': len(recommendations),
                'hedges_executed': len(executed_hedges),
                'total_exposure_value': sum(exp.market_value_base for exp in exposures),
                'total_hedge_cost': sum(hedge['cost'] for hedge in executed_hedges),
                'risk_compliance': risk_check,
                'exposures': [asdict(exp) for exp in exposures],
                'recommendations': [asdict(rec) for rec in recommendations],
                'executed_hedges': executed_hedges
            }
            
            logger.info(f"FX hedging analysis completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error in FX hedging analysis: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_hedge_performance(self, hedge_id: str = None) -> Dict[str, Any]:
        """Get performance metrics for hedges"""
        try:
            if hedge_id:
                # Return specific hedge performance
                if hedge_id in self.hedge_performance:
                    return self.hedge_performance[hedge_id]
                else:
                    return {'error': 'Hedge not found'}
            else:
                # Return overall hedge performance
                total_hedges = len(self.active_hedges)
                total_cost = sum(hedge.get('cost', 0) for hedge in self.active_hedges.values())
                total_pnl = sum(perf.get('pnl', 0) for perf in self.hedge_performance.values())
                
                return {
                    'total_active_hedges': total_hedges,
                    'total_hedge_cost': total_cost,
                    'total_hedge_pnl': total_pnl,
                    'net_hedge_result': total_pnl - total_cost,
                    'hedge_effectiveness': (total_pnl / total_cost) if total_cost > 0 else 0,
                    'individual_hedges': self.hedge_performance
                }
                
        except Exception as e:
            logger.error(f"Error getting hedge performance: {str(e)}")
            return {'error': str(e)}
    
    async def update_hedge_positions(self) -> Dict[str, Any]:
        """Update all hedge positions with current market data"""
        try:
            logger.info("Updating hedge positions")
            
            updated_hedges = []
            
            for hedge_id, hedge_data in self.active_hedges.items():
                try:
                    # Get current FX rate
                    instrument = hedge_data['instrument']
                    current_rate = await self.fx_data_provider.get_fx_rate(
                        Currency(instrument.quote_currency), 
                        Currency(instrument.base_currency)
                    )
                    
                    if current_rate:
                        # Calculate current P&L
                        if instrument.hedge_type == HedgeType.FORWARD:
                            forward_pnl = self._calculate_forward_pnl(instrument, current_rate)
                            self.hedge_performance[hedge_id] = {
                                'pnl': forward_pnl,
                                'current_rate': current_rate.mid,
                                'entry_rate': instrument.forward_rate,
                                'last_updated': datetime.now().isoformat()
                            }
                        elif instrument.hedge_type == HedgeType.OPTION:
                            option_pnl = self._calculate_option_pnl(instrument, current_rate)
                            self.hedge_performance[hedge_id] = {
                                'pnl': option_pnl,
                                'current_rate': current_rate.mid,
                                'strike_rate': instrument.strike_rate,
                                'premium_paid': instrument.premium,
                                'last_updated': datetime.now().isoformat()
                            }
                        
                        updated_hedges.append(hedge_id)
                
                except Exception as e:
                    logger.error(f"Error updating hedge {hedge_id}: {str(e)}")
            
            return {
                'success': True,
                'updated_hedges': len(updated_hedges),
                'hedge_ids': updated_hedges
            }
            
        except Exception as e:
            logger.error(f"Error updating hedge positions: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _check_risk_limits(self, exposures: List[CurrencyExposure]) -> Dict[str, Any]:
        """Check if exposures comply with risk limits"""
        try:
            violations = []
            
            # Check individual exposure limits
            for exposure in exposures:
                if exposure.market_value_base > self.risk_limits['max_single_exposure']:
                    violations.append(f"Single exposure limit exceeded for {exposure.exposure_currency.value}: "
                                   f"{exposure.market_value_base:,.0f} > {self.risk_limits['max_single_exposure']:,.0f}")
            
            # Check total exposure
            total_exposure = sum(abs(exp.market_value_base) for exp in exposures)
            if total_exposure > self.risk_limits['max_total_exposure']:
                violations.append(f"Total exposure limit exceeded: "
                               f"{total_exposure:,.0f} > {self.risk_limits['max_total_exposure']:,.0f}")
            
            # Check daily VaR (simplified)
            daily_var = await self._calculate_portfolio_var(exposures)
            if daily_var > self.risk_limits['max_daily_var']:
                violations.append(f"Daily VaR limit exceeded: "
                               f"{daily_var:,.0f} > {self.risk_limits['max_daily_var']:,.0f}")
            
            return {
                'compliant': len(violations) == 0,
                'violations': violations,
                'total_exposure': total_exposure,
                'daily_var': daily_var
            }
            
        except Exception as e:
            logger.error(f"Error checking risk limits: {str(e)}")
            return {'compliant': False, 'error': str(e)}
    
    async def _calculate_portfolio_var(self, exposures: List[CurrencyExposure], 
                                     confidence_level: float = 0.95) -> float:
        """Calculate portfolio Value at Risk"""
        try:
            if not exposures:
                return 0.0
            
            # Get volatilities
            vars = []
            for exposure in exposures:
                volatility = await self.fx_data_provider.get_volatility(
                    exposure.exposure_currency, exposure.base_currency
                )
                # Daily VaR = exposure * volatility * z-score
                z_score = stats.norm.ppf(confidence_level)
                daily_vol = volatility / np.sqrt(252)
                var = exposure.market_value_base * daily_vol * z_score
                vars.append(var)
            
            # For simplicity, assume zero correlation (conservative)
            portfolio_var = np.sqrt(sum(var**2 for var in vars))
            
            return portfolio_var
            
        except Exception as e:
            logger.error(f"Error calculating portfolio VaR: {str(e)}")
            return 0.0
    
    def _should_execute_hedge(self, recommendation: HedgeRecommendation) -> bool:
        """Determine if hedge should be executed"""
        try:
            # Check confidence threshold
            if recommendation.confidence_score < 0.6:
                return False
            
            # Check cost threshold
            if recommendation.expected_cost > recommendation.exposure.market_value_base * self.risk_limits['max_hedge_cost']:
                return False
            
            # Check if no hedge is recommended
            if recommendation.recommended_strategy == HedgeStrategy.NO_HEDGE:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error determining hedge execution: {str(e)}")
            return False
    
    async def _execute_hedge(self, recommendation: HedgeRecommendation) -> Dict[str, Any]:
        """Execute hedge recommendation"""
        try:
            executed_instruments = []
            total_cost = 0
            
            for instrument in recommendation.recommended_instruments:
                # Simulate hedge execution
                execution_result = await self._execute_hedge_instrument(instrument)
                
                if execution_result['success']:
                    executed_instruments.append(execution_result)
                    total_cost += execution_result['cost']
                    
                    # Store active hedge
                    self.active_hedges[execution_result['hedge_id']] = {
                        'instrument': instrument,
                        'recommendation': recommendation,
                        'execution_time': datetime.now(),
                        'cost': execution_result['cost']
                    }
                    
                    # Update metrics
                    self.hedge_executions.labels(
                        currency=instrument.quote_currency.value,
                        hedge_type=instrument.hedge_type.value
                    ).inc()
                    
                    self.hedge_costs.labels(
                        currency=instrument.quote_currency.value
                    ).observe(execution_result['cost'] / instrument.notional_amount * 10000)  # bps
            
            return {
                'success': True,
                'hedge_id': recommendation.recommendation_id,
                'instruments_executed': len(executed_instruments),
                'total_cost': total_cost,
                'strategy': recommendation.recommended_strategy.value,
                'execution_details': executed_instruments
            }
            
        except Exception as e:
            logger.error(f"Error executing hedge: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _execute_hedge_instrument(self, instrument: HedgeInstrument) -> Dict[str, Any]:
        """Execute individual hedge instrument"""
        try:
            # Simulate execution with realistic costs
            execution_cost = 0
            
            if instrument.hedge_type == HedgeType.FORWARD:
                # Forward execution cost (bid-ask spread)
                execution_cost = instrument.notional_amount * 0.0001  # 1 bp
                
            elif instrument.hedge_type == HedgeType.OPTION:
                # Option execution cost (premium + bid-ask)
                execution_cost = instrument.premium + (instrument.notional_amount * 0.0002)  # Premium + 2 bps
                
            elif instrument.hedge_type == HedgeType.SPOT:
                # Spot execution cost
                execution_cost = instrument.notional_amount * 0.00005  # 0.5 bps
            
            return {
                'success': True,
                'hedge_id': instrument.instrument_id,
                'instrument_type': instrument.hedge_type.value,
                'notional': instrument.notional_amount,
                'cost': execution_cost,
                'execution_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing hedge instrument: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_forward_pnl(self, instrument: HedgeInstrument, current_rate: FXRate) -> float:
        """Calculate P&L for forward instrument"""
        try:
            # Forward P&L = notional * (current_rate - forward_rate)
            rate_diff = current_rate.mid - instrument.forward_rate
            pnl = instrument.notional_amount * rate_diff
            
            return pnl
            
        except Exception as e:
            logger.error(f"Error calculating forward P&L: {str(e)}")
            return 0.0
    
    def _calculate_option_pnl(self, instrument: HedgeInstrument, current_rate: FXRate) -> float:
        """Calculate P&L for option instrument"""
        try:
            # Option P&L = intrinsic_value - premium_paid
            if instrument.option_type == "put":
                intrinsic_value = max(0, instrument.strike_rate - current_rate.mid) * instrument.notional_amount
            else:  # call
                intrinsic_value = max(0, current_rate.mid - instrument.strike_rate) * instrument.notional_amount
            
            pnl = intrinsic_value - instrument.premium
            
            return pnl
            
        except Exception as e:
            logger.error(f"Error calculating option P&L: {str(e)}")
            return 0.0
    
    async def _update_hedge_tracking(self, executed_hedges: List[Dict[str, Any]]):
        """Update hedge tracking data"""
        try:
            for hedge in executed_hedges:
                hedge_id = hedge['hedge_id']
                # Initialize performance tracking
                if hedge_id not in self.hedge_performance:
                    self.hedge_performance[hedge_id] = {
                        'pnl': 0.0,
                        'created_at': datetime.now().isoformat(),
                        'last_updated': datetime.now().isoformat()
                    }
            
        except Exception as e:
            logger.error(f"Error updating hedge tracking: {str(e)}")
    
    async def _update_metrics(self, exposures: List[CurrencyExposure], executed_hedges: List[Dict[str, Any]]):
        """Update Prometheus metrics"""
        try:
            # Update exposure metrics
            for exposure in exposures:
                self.fx_exposure_gauge.labels(
                    currency=exposure.exposure_currency.value
                ).set(exposure.market_value_base)
            
        except Exception as e:
            logger.error(f"Error updating metrics: {str(e)}")


# Risk monitoring and alerting
class FXRiskMonitor:
    """
    Monitors FX risk and sends alerts when thresholds are breached
    """
    
    def __init__(self, hedging_engine: FXHedgingEngine):
        self.hedging_engine = hedging_engine
        self.alert_thresholds = {
            'exposure_limit': 0.8,  # 80% of max exposure
            'var_limit': 0.9,       # 90% of max VaR
            'hedge_cost_limit': 0.15  # 15% of exposure value
        }
        
        # Metrics
        self.risk_alerts = Counter('fx_risk_alerts_total', 'FX risk alerts', ['alert_type'])
        
    async def monitor_risk(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor FX risk and generate alerts"""
        try:
            alerts = []
            
            # Calculate current exposures
            exposures = await self.hedging_engine.exposure_calculator.calculate_portfolio_exposures(portfolio)
            
            # Check exposure limits
            total_exposure = sum(abs(exp.market_value_base) for exp in exposures)
            exposure_threshold = self.hedging_engine.risk_limits['max_total_exposure'] * self.alert_thresholds['exposure_limit']
            
            if total_exposure > exposure_threshold:
                alert = {
                    'type': 'exposure_warning',
                    'message': f"Total FX exposure approaching limit: {total_exposure:,.0f}",
                    'severity': 'warning',
                    'timestamp': datetime.now().isoformat()
                }
                alerts.append(alert)
                self.risk_alerts.labels(alert_type='exposure_warning').inc()
            
            # Check VaR limits
            portfolio_var = await self.hedging_engine._calculate_portfolio_var(exposures)
            var_threshold = self.hedging_engine.risk_limits['max_daily_var'] * self.alert_thresholds['var_limit']
            
            if portfolio_var > var_threshold:
                alert = {
                    'type': 'var_warning',
                    'message': f"Portfolio VaR approaching limit: {portfolio_var:,.0f}",
                    'severity': 'warning',
                    'timestamp': datetime.now().isoformat()
                }
                alerts.append(alert)
                self.risk_alerts.labels(alert_type='var_warning').inc()
            
            # Check hedge performance
            hedge_performance = await self.hedging_engine.get_hedge_performance()
            if hedge_performance.get('hedge_effectiveness', 0) < -0.2:  # 20% loss
                alert = {
                    'type': 'hedge_performance',
                    'message': f"Hedge performance deteriorating: {hedge_performance.get('hedge_effectiveness', 0):.2%}",
                    'severity': 'critical',
                    'timestamp': datetime.now().isoformat()
                }
                alerts.append(alert)
                self.risk_alerts.labels(alert_type='hedge_performance').inc()
            
            return {
                'risk_level': self._calculate_risk_level(total_exposure, portfolio_var),
                'alerts': alerts,
                'total_exposure': total_exposure,
                'portfolio_var': portfolio_var,
                'hedge_performance': hedge_performance
            }
            
        except Exception as e:
            logger.error(f"Error monitoring FX risk: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_risk_level(self, total_exposure: float, portfolio_var: float) -> str:
        """Calculate overall risk level"""
        try:
            exposure_ratio = total_exposure / self.hedging_engine.risk_limits['max_total_exposure']
            var_ratio = portfolio_var / self.hedging_engine.risk_limits['max_daily_var']
            
            max_ratio = max(exposure_ratio, var_ratio)
            
            if max_ratio < 0.5:
                return 'low'
            elif max_ratio < 0.8:
                return 'medium'
            elif max_ratio < 1.0:
                return 'high'
            else:
                return 'critical'
                
        except Exception as e:
            logger.error(f"Error calculating risk level: {str(e)}")
            return 'unknown'


# Main example usage
async def main():
    """Example usage of FX Hedging Engine"""
    try:
        # Initialize FX hedging engine
        fx_engine = FXHedgingEngine(Currency.USD)
        
        # Initialize risk monitor
        risk_monitor = FXRiskMonitor(fx_engine)
        
        # Sample portfolio with international positions
        sample_portfolio = {
            'positions': {
                'AAPL': {'quantity': 1000, 'price': 150.0},  # USD
                'ASML': {'quantity': 500, 'price': 800.0},   # EUR
                'TSM': {'quantity': 2000, 'price': 100.0},   # USD (but Taiwan exposure)
                'LVMH': {'quantity': 100, 'price': 700.0},   # EUR
                'SONY': {'quantity': 1000, 'price': 110.0}   # JPY
            }
        }
        
        print("🌍 FX Hedging Engine Demo")
        print("=" * 50)
        
        # Analyze and hedge portfolio
        print("\n📊 Analyzing portfolio FX exposures...")
        hedging_result = await fx_engine.analyze_and_hedge_portfolio(
            sample_portfolio, 
            risk_tolerance=0.03  # 3% risk tolerance
        )
        
        print(f"✅ Analysis completed in {hedging_result['processing_time']:.2f}s")
        print(f"📈 Exposures analyzed: {hedging_result['exposures_analyzed']}")
        print(f"💡 Recommendations generated: {hedging_result['recommendations_generated']}")
        print(f"🛡️ Hedges executed: {hedging_result['hedges_executed']}")
        print(f"💰 Total exposure value: ${hedging_result['total_exposure_value']:,.0f}")
        print(f"💸 Total hedge cost: ${hedging_result['total_hedge_cost']:,.0f}")
        
        # Monitor risk
        print("\n🔍 Monitoring FX risk...")
        risk_status = await risk_monitor.monitor_risk(sample_portfolio)
        print(f"⚠️ Risk level: {risk_status['risk_level'].upper()}")
        print(f"📊 Total exposure: ${risk_status['total_exposure']:,.0f}")
        print(f"📈 Portfolio VaR: ${risk_status['portfolio_var']:,.0f}")
        
        if risk_status['alerts']:
            print(f"🚨 Alerts generated: {len(risk_status['alerts'])}")
            for alert in risk_status['alerts']:
                print(f"  - {alert['type']}: {alert['message']}")
        
        # Update hedge positions
        print("\n🔄 Updating hedge positions...")
        update_result = await fx_engine.update_hedge_positions()
        print(f"✅ Updated {update_result['updated_hedges']} hedge positions")
        
        # Get hedge performance
        print("\n📈 Hedge performance summary:")
        performance = await fx_engine.get_hedge_performance()
        print(f"💼 Active hedges: {performance['total_active_hedges']}")
        print(f"💰 Total hedge cost: ${performance['total_hedge_cost']:,.0f}")
        print(f"📊 Total hedge P&L: ${performance['total_hedge_pnl']:,.0f}")
        print(f"🎯 Hedge effectiveness: {performance['hedge_effectiveness']:.2%}")
        
        print("\n✅ FX Hedging Engine demo completed!")
        
    except Exception as e:
        logger.error(f"Error in FX hedging demo: {str(e)}")
        print(f"❌ Demo failed: {str(e)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
