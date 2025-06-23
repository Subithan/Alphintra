"""
Generative AI Strategy Synthesis Engine
Alphintra Trading Platform - Phase 5

Uses Large Language Models and generative AI to automatically synthesize, 
optimize, and evolve trading strategies based on market conditions and objectives.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import time
import uuid
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import ast
import inspect

# AI/ML libraries
import openai
import anthropic
import google.generativeai as genai
from transformers import pipeline
import torch

# Strategy execution
import aiohttp
import aioredis

# Monitoring
from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Types of trading strategies"""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    ARBITRAGE = "arbitrage"
    STATISTICAL_ARBITRAGE = "statistical_arbitrage"
    MARKET_MAKING = "market_making"
    TREND_FOLLOWING = "trend_following"
    PAIRS_TRADING = "pairs_trading"
    VOLATILITY = "volatility"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    MULTI_FACTOR = "multi_factor"
    CUSTOM = "custom"


class AIModel(Enum):
    """Supported AI models"""
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    GEMINI_PRO = "gemini-pro"
    CODELLAMA = "codellama"
    MIXTRAL = "mixtral"


class MarketRegime(Enum):
    """Market regime types"""
    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    CRISIS = "crisis"
    RECOVERY = "recovery"


@dataclass
class StrategyObjective:
    """Trading strategy objective"""
    target_return: float
    max_drawdown: float
    sharpe_ratio_target: float
    max_positions: int
    holding_period_min: int
    holding_period_max: int
    risk_tolerance: float
    market_neutrality: float
    preferred_assets: List[str]
    excluded_assets: List[str]
    strategy_types: List[StrategyType]
    additional_constraints: Dict[str, Any]


@dataclass
class MarketContext:
    """Current market context for strategy generation"""
    regime: MarketRegime
    volatility_level: float
    trend_strength: float
    correlation_environment: str
    liquidity_conditions: str
    sector_rotation: Dict[str, float]
    economic_indicators: Dict[str, Any]
    sentiment_scores: Dict[str, float]
    unusual_patterns: List[str]
    risk_factors: List[str]


@dataclass
class GeneratedStrategy:
    """Generated trading strategy"""
    strategy_id: str
    name: str
    description: str
    strategy_type: StrategyType
    code: str
    parameters: Dict[str, Any]
    expected_performance: Dict[str, float]
    risk_metrics: Dict[str, float]
    market_conditions: List[str]
    confidence_score: float
    backtest_results: Optional[Dict[str, Any]]
    ai_model_used: AIModel
    generation_timestamp: datetime
    last_updated: datetime


@dataclass
class StrategyEvolution:
    """Strategy evolution tracking"""
    original_strategy_id: str
    evolved_strategy_id: str
    evolution_type: str
    changes_made: List[str]
    performance_improvement: float
    confidence_change: float
    evolution_timestamp: datetime


class LLMProvider:
    """
    Manages connections to various Large Language Model providers
    """
    
    def __init__(self):
        self.clients = {}
        self.model_configs = {
            AIModel.GPT_4: {
                'provider': 'openai',
                'max_tokens': 4000,
                'temperature': 0.7,
                'top_p': 0.9
            },
            AIModel.CLAUDE_3_OPUS: {
                'provider': 'anthropic',
                'max_tokens': 4000,
                'temperature': 0.7
            },
            AIModel.GEMINI_PRO: {
                'provider': 'google',
                'max_tokens': 4000,
                'temperature': 0.7
            }
        }
        
        # Initialize clients
        self._initialize_clients()
        
        # Metrics
        self.llm_requests = Counter('llm_requests_total', 'LLM requests', ['model', 'task_type'])
        self.llm_latency = Histogram('llm_response_time_seconds', 'LLM response time', ['model'])
        self.llm_tokens = Counter('llm_tokens_used_total', 'LLM tokens used', ['model', 'type'])
    
    def _initialize_clients(self):
        """Initialize LLM clients"""
        try:
            # OpenAI client
            try:
                self.clients['openai'] = openai.AsyncOpenAI()
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {str(e)}")
            
            # Anthropic client
            try:
                self.clients['anthropic'] = anthropic.AsyncAnthropic()
                logger.info("Anthropic client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {str(e)}")
            
            # Google Generative AI
            try:
                genai.configure(api_key="your-google-api-key")  # Would use env var
                logger.info("Google Generative AI configured")
            except Exception as e:
                logger.warning(f"Failed to configure Google Generative AI: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error initializing LLM clients: {str(e)}")
    
    async def generate_response(self, model: AIModel, prompt: str, 
                              task_type: str = "strategy_generation") -> str:
        """Generate response from specified LLM"""
        try:
            start_time = time.time()
            config = self.model_configs[model]
            
            response = ""
            
            if config['provider'] == 'openai' and 'openai' in self.clients:
                response = await self._call_openai(model, prompt, config)
            elif config['provider'] == 'anthropic' and 'anthropic' in self.clients:
                response = await self._call_anthropic(model, prompt, config)
            elif config['provider'] == 'google':
                response = await self._call_google(model, prompt, config)
            else:
                # Fallback to mock response
                response = await self._generate_mock_response(prompt, task_type)
            
            # Update metrics
            response_time = time.time() - start_time
            self.llm_requests.labels(model=model.value, task_type=task_type).inc()
            self.llm_latency.labels(model=model.value).observe(response_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            # Return fallback mock response
            return await self._generate_mock_response(prompt, task_type)
    
    async def _call_openai(self, model: AIModel, prompt: str, config: Dict[str, Any]) -> str:
        """Call OpenAI API"""
        try:
            response = await self.clients['openai'].chat.completions.create(
                model=model.value,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=config['max_tokens'],
                temperature=config['temperature'],
                top_p=config['top_p']
            )
            
            content = response.choices[0].message.content
            
            # Update token metrics
            self.llm_tokens.labels(model=model.value, type='input').inc(response.usage.prompt_tokens)
            self.llm_tokens.labels(model=model.value, type='output').inc(response.usage.completion_tokens)
            
            return content
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise
    
    async def _call_anthropic(self, model: AIModel, prompt: str, config: Dict[str, Any]) -> str:
        """Call Anthropic API"""
        try:
            response = await self.clients['anthropic'].messages.create(
                model=model.value,
                max_tokens=config['max_tokens'],
                temperature=config['temperature'],
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            
            # Update token metrics
            self.llm_tokens.labels(model=model.value, type='input').inc(response.usage.input_tokens)
            self.llm_tokens.labels(model=model.value, type='output').inc(response.usage.output_tokens)
            
            return content
            
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {str(e)}")
            raise
    
    async def _call_google(self, model: AIModel, prompt: str, config: Dict[str, Any]) -> str:
        """Call Google Generative AI"""
        try:
            model_instance = genai.GenerativeModel(model.value)
            
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=config['max_tokens'],
                temperature=config['temperature']
            )
            
            response = await model_instance.generate_content_async(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error calling Google Generative AI: {str(e)}")
            raise
    
    async def _generate_mock_response(self, prompt: str, task_type: str) -> str:
        """Generate mock response for testing"""
        if task_type == "strategy_generation":
            return """
# AI-Generated Momentum Trading Strategy

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

class MomentumStrategy:
    def __init__(self, lookback_period: int = 20, momentum_threshold: float = 0.02):
        self.lookback_period = lookback_period
        self.momentum_threshold = momentum_threshold
        self.positions = {}
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # Calculate momentum indicator
        returns = data['close'].pct_change(self.lookback_period)
        
        # Generate buy/sell signals
        signals = pd.Series(0, index=data.index)
        signals[returns > self.momentum_threshold] = 1  # Buy
        signals[returns < -self.momentum_threshold] = -1  # Sell
        
        return signals
    
    def calculate_position_size(self, signal: int, volatility: float, portfolio_value: float) -> float:
        if signal == 0:
            return 0.0
        
        # Risk-adjusted position sizing
        max_risk_per_trade = 0.02  # 2% risk per trade
        position_size = (portfolio_value * max_risk_per_trade) / volatility
        
        return min(position_size, portfolio_value * 0.1)  # Max 10% per position
    
    def backtest_performance(self, data: pd.DataFrame) -> Dict[str, float]:
        signals = self.generate_signals(data)
        returns = data['close'].pct_change()
        
        strategy_returns = signals.shift(1) * returns
        cumulative_return = (1 + strategy_returns).cumprod().iloc[-1] - 1
        
        return {
            'total_return': cumulative_return,
            'sharpe_ratio': strategy_returns.mean() / strategy_returns.std() * np.sqrt(252),
            'max_drawdown': (strategy_returns.cumsum() - strategy_returns.cumsum().cummax()).min(),
            'win_rate': len(strategy_returns[strategy_returns > 0]) / len(strategy_returns[strategy_returns != 0])
        }
"""
        elif task_type == "strategy_optimization":
            return """
The strategy can be optimized by:
1. Dynamic lookback period adjustment based on volatility regime
2. Multi-timeframe momentum confirmation
3. Risk management improvements with volatility-adjusted position sizing
4. Market regime detection to avoid false signals during sideways markets
5. Portfolio correlation analysis to reduce concentration risk
"""
        else:
            return "Mock AI response for testing purposes."


class MarketAnalyzer:
    """
    Analyzes market conditions to provide context for strategy generation
    """
    
    def __init__(self):
        self.data_sources = []
        self.analysis_cache = {}
        
    async def analyze_current_market_context(self, symbols: List[str] = None) -> MarketContext:
        """Analyze current market conditions"""
        try:
            if symbols is None:
                symbols = ['SPY', 'QQQ', 'VIX', 'TLT', 'GLD']
            
            # Get market data (mock implementation)
            market_data = await self._fetch_market_data(symbols)
            
            # Analyze market regime
            regime = await self._detect_market_regime(market_data)
            
            # Calculate volatility
            volatility_level = await self._calculate_volatility_level(market_data)
            
            # Analyze trends
            trend_strength = await self._analyze_trend_strength(market_data)
            
            # Correlation analysis
            correlation_env = await self._analyze_correlation_environment(market_data)
            
            # Liquidity analysis
            liquidity_conditions = await self._analyze_liquidity_conditions(market_data)
            
            # Sector rotation
            sector_rotation = await self._analyze_sector_rotation()
            
            # Economic indicators
            economic_indicators = await self._get_economic_indicators()
            
            # Sentiment analysis
            sentiment_scores = await self._analyze_market_sentiment()
            
            # Pattern detection
            unusual_patterns = await self._detect_unusual_patterns(market_data)
            
            # Risk factor analysis
            risk_factors = await self._identify_risk_factors()
            
            return MarketContext(
                regime=regime,
                volatility_level=volatility_level,
                trend_strength=trend_strength,
                correlation_environment=correlation_env,
                liquidity_conditions=liquidity_conditions,
                sector_rotation=sector_rotation,
                economic_indicators=economic_indicators,
                sentiment_scores=sentiment_scores,
                unusual_patterns=unusual_patterns,
                risk_factors=risk_factors
            )
            
        except Exception as e:
            logger.error(f"Error analyzing market context: {str(e)}")
            # Return default context
            return MarketContext(
                regime=MarketRegime.SIDEWAYS,
                volatility_level=0.2,
                trend_strength=0.5,
                correlation_environment="normal",
                liquidity_conditions="adequate",
                sector_rotation={},
                economic_indicators={},
                sentiment_scores={},
                unusual_patterns=[],
                risk_factors=[]
            )
    
    async def _fetch_market_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """Fetch market data for analysis"""
        try:
            # Mock implementation - would fetch real data
            market_data = {}
            
            for symbol in symbols:
                # Generate mock price data
                dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
                np.random.seed(hash(symbol) % 2**32)
                
                price_data = {
                    'open': 100 + np.random.randn(len(dates)).cumsum() * 0.5,
                    'high': 100 + np.random.randn(len(dates)).cumsum() * 0.5 + 1,
                    'low': 100 + np.random.randn(len(dates)).cumsum() * 0.5 - 1,
                    'close': 100 + np.random.randn(len(dates)).cumsum() * 0.5,
                    'volume': np.random.randint(1000000, 10000000, len(dates))
                }
                
                market_data[symbol] = pd.DataFrame(price_data, index=dates)
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            return {}
    
    async def _detect_market_regime(self, market_data: Dict[str, pd.DataFrame]) -> MarketRegime:
        """Detect current market regime"""
        try:
            if 'SPY' in market_data:
                spy_data = market_data['SPY']
                
                # Simple regime detection based on recent performance
                recent_return = (spy_data['close'].iloc[-1] / spy_data['close'].iloc[-60] - 1)
                volatility = spy_data['close'].pct_change().rolling(20).std().iloc[-1]
                
                if recent_return > 0.1:
                    return MarketRegime.BULL_MARKET
                elif recent_return < -0.1:
                    return MarketRegime.BEAR_MARKET
                elif volatility > 0.025:
                    return MarketRegime.HIGH_VOLATILITY
                elif volatility < 0.01:
                    return MarketRegime.LOW_VOLATILITY
                else:
                    return MarketRegime.SIDEWAYS
            
            return MarketRegime.SIDEWAYS
            
        except Exception as e:
            logger.error(f"Error detecting market regime: {str(e)}")
            return MarketRegime.SIDEWAYS
    
    async def _calculate_volatility_level(self, market_data: Dict[str, pd.DataFrame]) -> float:
        """Calculate current volatility level"""
        try:
            if 'VIX' in market_data:
                return market_data['VIX']['close'].iloc[-1] / 100
            elif 'SPY' in market_data:
                return market_data['SPY']['close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252)
            
            return 0.2  # Default volatility
            
        except Exception as e:
            logger.error(f"Error calculating volatility level: {str(e)}")
            return 0.2
    
    async def _analyze_trend_strength(self, market_data: Dict[str, pd.DataFrame]) -> float:
        """Analyze trend strength"""
        try:
            if 'SPY' in market_data:
                spy_data = market_data['SPY']
                
                # Calculate trend strength using ADX-like measure
                high_low = spy_data['high'] - spy_data['low']
                high_close = abs(spy_data['high'] - spy_data['close'].shift(1))
                low_close = abs(spy_data['low'] - spy_data['close'].shift(1))
                
                true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                atr = true_range.rolling(14).mean()
                
                # Simple trend strength calculation
                price_change = spy_data['close'].diff(20)
                trend_strength = abs(price_change / atr).iloc[-1]
                
                return min(trend_strength / 10, 1.0)  # Normalize to 0-1
            
            return 0.5
            
        except Exception as e:
            logger.error(f"Error analyzing trend strength: {str(e)}")
            return 0.5
    
    async def _analyze_correlation_environment(self, market_data: Dict[str, pd.DataFrame]) -> str:
        """Analyze correlation environment"""
        try:
            if len(market_data) >= 2:
                # Calculate correlation between major assets
                returns_data = {}
                for symbol, data in market_data.items():
                    returns_data[symbol] = data['close'].pct_change()
                
                returns_df = pd.DataFrame(returns_data).dropna()
                correlation_matrix = returns_df.corr()
                
                # Average absolute correlation (excluding diagonal)
                avg_correlation = correlation_matrix.abs().values[
                    ~np.eye(correlation_matrix.shape[0], dtype=bool)
                ].mean()
                
                if avg_correlation > 0.7:
                    return "high_correlation"
                elif avg_correlation > 0.4:
                    return "normal"
                else:
                    return "low_correlation"
            
            return "normal"
            
        except Exception as e:
            logger.error(f"Error analyzing correlation environment: {str(e)}")
            return "normal"
    
    async def _analyze_liquidity_conditions(self, market_data: Dict[str, pd.DataFrame]) -> str:
        """Analyze market liquidity conditions"""
        try:
            # Simple liquidity analysis based on volume
            if 'SPY' in market_data:
                spy_data = market_data['SPY']
                recent_volume = spy_data['volume'].iloc[-10:].mean()
                historical_volume = spy_data['volume'].iloc[-100:-10].mean()
                
                volume_ratio = recent_volume / historical_volume
                
                if volume_ratio > 1.2:
                    return "high_liquidity"
                elif volume_ratio < 0.8:
                    return "low_liquidity"
                else:
                    return "adequate"
            
            return "adequate"
            
        except Exception as e:
            logger.error(f"Error analyzing liquidity conditions: {str(e)}")
            return "adequate"
    
    async def _analyze_sector_rotation(self) -> Dict[str, float]:
        """Analyze sector rotation patterns"""
        try:
            # Mock sector performance data
            sectors = ['Technology', 'Healthcare', 'Financials', 'Energy', 'Industrials', 'Consumer']
            performance = np.random.uniform(-0.05, 0.05, len(sectors))
            
            return dict(zip(sectors, performance))
            
        except Exception as e:
            logger.error(f"Error analyzing sector rotation: {str(e)}")
            return {}
    
    async def _get_economic_indicators(self) -> Dict[str, Any]:
        """Get current economic indicators"""
        try:
            # Mock economic indicators
            return {
                'gdp_growth': 2.5,
                'inflation_rate': 3.2,
                'unemployment_rate': 4.1,
                'interest_rate': 5.25,
                'yield_curve_slope': 0.8
            }
            
        except Exception as e:
            logger.error(f"Error getting economic indicators: {str(e)}")
            return {}
    
    async def _analyze_market_sentiment(self) -> Dict[str, float]:
        """Analyze market sentiment from various sources"""
        try:
            # Mock sentiment scores
            return {
                'fear_greed_index': 0.45,
                'put_call_ratio': 0.8,
                'insider_trading': 0.6,
                'news_sentiment': 0.55,
                'social_sentiment': 0.52
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market sentiment: {str(e)}")
            return {}
    
    async def _detect_unusual_patterns(self, market_data: Dict[str, pd.DataFrame]) -> List[str]:
        """Detect unusual market patterns"""
        try:
            patterns = []
            
            # Simple pattern detection
            if 'SPY' in market_data:
                spy_data = market_data['SPY']
                
                # Check for unusual volume
                recent_volume = spy_data['volume'].iloc[-1]
                avg_volume = spy_data['volume'].rolling(20).mean().iloc[-1]
                
                if recent_volume > avg_volume * 2:
                    patterns.append("unusual_volume_spike")
                
                # Check for large price moves
                daily_return = spy_data['close'].pct_change().iloc[-1]
                if abs(daily_return) > 0.03:
                    patterns.append("large_price_movement")
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting unusual patterns: {str(e)}")
            return []
    
    async def _identify_risk_factors(self) -> List[str]:
        """Identify current market risk factors"""
        try:
            # Mock risk factors
            risk_factors = []
            
            # Random risk factor selection for demo
            potential_risks = [
                "geopolitical_tension",
                "inflation_concerns",
                "interest_rate_volatility",
                "credit_stress",
                "liquidity_concerns",
                "regulatory_changes"
            ]
            
            # Randomly select 1-3 risk factors
            import random
            num_risks = random.randint(1, 3)
            risk_factors = random.sample(potential_risks, num_risks)
            
            return risk_factors
            
        except Exception as e:
            logger.error(f"Error identifying risk factors: {str(e)}")
            return []


class PromptEngineering:
    """
    Manages prompt engineering for strategy generation
    """
    
    def __init__(self):
        self.prompt_templates = {
            'strategy_generation': self._load_strategy_generation_template(),
            'strategy_optimization': self._load_strategy_optimization_template(),
            'risk_analysis': self._load_risk_analysis_template(),
            'market_adaptation': self._load_market_adaptation_template()
        }
    
    def create_strategy_generation_prompt(self, objective: StrategyObjective, 
                                        market_context: MarketContext) -> str:
        """Create prompt for strategy generation"""
        try:
            template = self.prompt_templates['strategy_generation']
            
            # Format the prompt with specific parameters
            prompt = template.format(
                target_return=objective.target_return * 100,
                max_drawdown=objective.max_drawdown * 100,
                sharpe_target=objective.sharpe_ratio_target,
                max_positions=objective.max_positions,
                market_regime=market_context.regime.value,
                volatility_level=market_context.volatility_level * 100,
                trend_strength=market_context.trend_strength,
                preferred_assets=", ".join(objective.preferred_assets),
                strategy_types=", ".join([st.value for st in objective.strategy_types]),
                risk_factors=", ".join(market_context.risk_factors),
                sentiment_summary=self._summarize_sentiment(market_context.sentiment_scores)
            )
            
            return prompt
            
        except Exception as e:
            logger.error(f"Error creating strategy generation prompt: {str(e)}")
            return self._get_fallback_prompt()
    
    def create_optimization_prompt(self, strategy: GeneratedStrategy, 
                                 performance_feedback: Dict[str, Any]) -> str:
        """Create prompt for strategy optimization"""
        try:
            template = self.prompt_templates['strategy_optimization']
            
            prompt = template.format(
                strategy_name=strategy.name,
                current_code=strategy.code,
                performance_issues=self._format_performance_issues(performance_feedback),
                target_improvements=self._format_target_improvements(performance_feedback)
            )
            
            return prompt
            
        except Exception as e:
            logger.error(f"Error creating optimization prompt: {str(e)}")
            return "Please optimize the provided trading strategy code to improve performance."
    
    def _load_strategy_generation_template(self) -> str:
        """Load strategy generation prompt template"""
        return """
You are an expert quantitative trading strategist and Python developer. Generate a complete, production-ready trading strategy based on the following requirements:

STRATEGY REQUIREMENTS:
- Target Annual Return: {target_return:.1f}%
- Maximum Drawdown: {max_drawdown:.1f}%
- Target Sharpe Ratio: {sharpe_target:.2f}
- Maximum Positions: {max_positions}
- Preferred Assets: {preferred_assets}
- Strategy Types: {strategy_types}

CURRENT MARKET CONTEXT:
- Market Regime: {market_regime}
- Volatility Level: {volatility_level:.1f}%
- Trend Strength: {trend_strength:.2f}
- Risk Factors: {risk_factors}
- Market Sentiment: {sentiment_summary}

REQUIREMENTS:
1. Generate complete Python code for a trading strategy class
2. Include proper risk management and position sizing
3. Implement signal generation logic appropriate for current market conditions
4. Add backtesting functionality
5. Include performance metrics calculation
6. Use proper error handling and logging
7. Code should be production-ready and well-documented

RESPONSE FORMAT:
Return only the Python code with comprehensive docstrings and comments. The strategy should inherit from a base Strategy class and implement required methods:
- generate_signals()
- calculate_position_size()
- manage_risk()
- backtest_performance()

Focus on strategies that work well in the current {market_regime} environment with {volatility_level:.1f}% volatility.
"""
    
    def _load_strategy_optimization_template(self) -> str:
        """Load strategy optimization prompt template"""
        return """
You are an expert quantitative analyst. Optimize the following trading strategy to address performance issues:

CURRENT STRATEGY: {strategy_name}

EXISTING CODE:
{current_code}

PERFORMANCE ISSUES IDENTIFIED:
{performance_issues}

TARGET IMPROVEMENTS:
{target_improvements}

OPTIMIZATION REQUIREMENTS:
1. Maintain the core strategy logic while improving performance
2. Address specific performance issues mentioned above
3. Enhance risk management if needed
4. Improve signal quality and reduce false positives
5. Optimize parameters based on market conditions
6. Add adaptive features if beneficial

Return the optimized Python code with clear comments explaining the improvements made.
"""
    
    def _load_risk_analysis_template(self) -> str:
        """Load risk analysis prompt template"""
        return """
Analyze the risk characteristics of the provided trading strategy and suggest improvements:

STRATEGY CODE:
{strategy_code}

ANALYSIS REQUIREMENTS:
1. Identify potential risk factors
2. Assess position sizing methodology
3. Evaluate stop-loss and risk management rules
4. Check for correlation risks
5. Assess market regime sensitivity
6. Recommend risk improvements

Provide detailed risk analysis and specific recommendations.
"""
    
    def _load_market_adaptation_template(self) -> str:
        """Load market adaptation prompt template"""
        return """
Adapt the trading strategy for changing market conditions:

CURRENT STRATEGY:
{strategy_code}

MARKET CHANGES:
{market_changes}

NEW MARKET CONTEXT:
{new_market_context}

ADAPTATION REQUIREMENTS:
1. Modify strategy parameters for new market conditions
2. Adjust risk management for new volatility regime
3. Update signal generation for new trend environment
4. Enhance position sizing for new correlation structure

Return adapted strategy code with explanations of changes made.
"""
    
    def _get_fallback_prompt(self) -> str:
        """Get fallback prompt if template fails"""
        return """
Generate a momentum-based trading strategy in Python that:
1. Uses 20-day momentum indicator
2. Implements 2% position sizing
3. Includes stop-loss at 5%
4. Has proper backtesting functionality
5. Calculates Sharpe ratio and drawdown

Return complete Python code with proper documentation.
"""
    
    def _summarize_sentiment(self, sentiment_scores: Dict[str, float]) -> str:
        """Summarize sentiment scores"""
        if not sentiment_scores:
            return "neutral"
        
        avg_sentiment = sum(sentiment_scores.values()) / len(sentiment_scores)
        
        if avg_sentiment > 0.6:
            return "bullish"
        elif avg_sentiment < 0.4:
            return "bearish"
        else:
            return "neutral"
    
    def _format_performance_issues(self, feedback: Dict[str, Any]) -> str:
        """Format performance issues for prompt"""
        issues = []
        
        if feedback.get('low_sharpe', False):
            issues.append("- Low Sharpe ratio indicating poor risk-adjusted returns")
        
        if feedback.get('high_drawdown', False):
            issues.append("- High maximum drawdown exceeding target limits")
        
        if feedback.get('low_win_rate', False):
            issues.append("- Low win rate suggesting poor signal quality")
        
        if feedback.get('high_turnover', False):
            issues.append("- High portfolio turnover increasing transaction costs")
        
        return "\n".join(issues) if issues else "No specific issues identified"
    
    def _format_target_improvements(self, feedback: Dict[str, Any]) -> str:
        """Format target improvements for prompt"""
        improvements = []
        
        if feedback.get('target_sharpe'):
            improvements.append(f"- Achieve Sharpe ratio of at least {feedback['target_sharpe']:.2f}")
        
        if feedback.get('target_drawdown'):
            improvements.append(f"- Reduce maximum drawdown to below {feedback['target_drawdown']:.1%}")
        
        if feedback.get('target_win_rate'):
            improvements.append(f"- Improve win rate to above {feedback['target_win_rate']:.1%}")
        
        return "\n".join(improvements) if improvements else "General performance improvement"


class StrategyValidator:
    """
    Validates and tests generated strategies
    """
    
    def __init__(self):
        self.validation_rules = self._load_validation_rules()
    
    async def validate_strategy_code(self, code: str) -> Dict[str, Any]:
        """Validate generated strategy code"""
        try:
            validation_result = {
                'is_valid': True,
                'syntax_errors': [],
                'security_issues': [],
                'performance_warnings': [],
                'missing_methods': [],
                'code_quality_score': 0.0
            }
            
            # Syntax validation
            syntax_check = await self._check_syntax(code)
            validation_result['syntax_errors'] = syntax_check['errors']
            validation_result['is_valid'] &= len(syntax_check['errors']) == 0
            
            # Security validation
            security_check = await self._check_security(code)
            validation_result['security_issues'] = security_check['issues']
            validation_result['is_valid'] &= len(security_check['issues']) == 0
            
            # Required methods validation
            methods_check = await self._check_required_methods(code)
            validation_result['missing_methods'] = methods_check['missing']
            validation_result['is_valid'] &= len(methods_check['missing']) == 0
            
            # Performance analysis
            performance_check = await self._check_performance_patterns(code)
            validation_result['performance_warnings'] = performance_check['warnings']
            
            # Code quality score
            validation_result['code_quality_score'] = await self._calculate_code_quality(code)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating strategy code: {str(e)}")
            return {
                'is_valid': False,
                'error': str(e),
                'code_quality_score': 0.0
            }
    
    async def _check_syntax(self, code: str) -> Dict[str, Any]:
        """Check Python syntax"""
        try:
            ast.parse(code)
            return {'errors': []}
        except SyntaxError as e:
            return {'errors': [f"Syntax error at line {e.lineno}: {e.msg}"]}
        except Exception as e:
            return {'errors': [f"Code parsing error: {str(e)}"]}
    
    async def _check_security(self, code: str) -> Dict[str, Any]:
        """Check for security issues"""
        issues = []
        
        # Check for dangerous imports
        dangerous_imports = ['os', 'subprocess', 'sys', 'eval', 'exec']
        for imp in dangerous_imports:
            if f"import {imp}" in code or f"from {imp}" in code:
                issues.append(f"Potentially dangerous import: {imp}")
        
        # Check for eval/exec usage
        if 'eval(' in code or 'exec(' in code:
            issues.append("Use of eval() or exec() is not allowed")
        
        # Check for file operations
        if 'open(' in code and 'w' in code:
            issues.append("File write operations detected")
        
        return {'issues': issues}
    
    async def _check_required_methods(self, code: str) -> Dict[str, Any]:
        """Check for required strategy methods"""
        required_methods = [
            'generate_signals',
            'calculate_position_size',
            'backtest_performance'
        ]
        
        missing_methods = []
        
        for method in required_methods:
            if f"def {method}" not in code:
                missing_methods.append(method)
        
        return {'missing': missing_methods}
    
    async def _check_performance_patterns(self, code: str) -> Dict[str, Any]:
        """Check for performance anti-patterns"""
        warnings = []
        
        # Check for loops that could be vectorized
        if 'for ' in code and '.iloc[' in code:
            warnings.append("Consider vectorizing loops for better performance")
        
        # Check for inefficient pandas operations
        if '.apply(' in code and 'lambda' in code:
            warnings.append("Consider using vectorized operations instead of apply with lambda")
        
        # Check for potential memory issues
        if '.dropna()' in code and 'inplace=False' not in code:
            warnings.append("Consider using inplace=True for memory efficiency")
        
        return {'warnings': warnings}
    
    async def _calculate_code_quality(self, code: str) -> float:
        """Calculate code quality score"""
        try:
            score = 1.0
            
            # Deduct points for various issues
            if 'TODO' in code or 'FIXME' in code:
                score -= 0.1
            
            if len(code.split('\n')) > 500:
                score -= 0.1  # Penalize very long code
            
            if '# ' not in code:
                score -= 0.2  # Penalize lack of comments
            
            if 'docstring' not in code and '"""' not in code:
                score -= 0.1  # Penalize lack of docstrings
            
            return max(0.0, score)
            
        except Exception as e:
            logger.error(f"Error calculating code quality: {str(e)}")
            return 0.5
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules configuration"""
        return {
            'max_code_length': 1000,
            'required_imports': ['pandas', 'numpy'],
            'forbidden_patterns': ['eval(', 'exec(', 'import os'],
            'required_methods': ['generate_signals', 'calculate_position_size', 'backtest_performance']
        }


class GenerativeStrategyEngine:
    """
    Main engine for generative AI strategy synthesis
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        
        # Core components
        self.llm_provider = LLMProvider()
        self.market_analyzer = MarketAnalyzer()
        self.prompt_engineer = PromptEngineering()
        self.validator = StrategyValidator()
        
        # Strategy storage
        self.generated_strategies = {}
        self.strategy_evolution_history = {}
        
        # Configuration
        self.default_models = [AIModel.GPT_4, AIModel.CLAUDE_3_SONNET]
        self.generation_timeout = 120  # seconds
        
        # Metrics
        self.strategies_generated = Counter('strategies_generated_total', 'Strategies generated', ['model', 'type'])
        self.strategies_validated = Counter('strategies_validated_total', 'Strategies validated', ['result'])
        self.generation_latency = Histogram('strategy_generation_duration_seconds', 'Generation duration')
        self.strategy_performance = Gauge('strategy_performance_score', 'Strategy performance', ['strategy_id'])
        
        logger.info("Generative Strategy Engine initialized")
    
    async def initialize(self):
        """Initialize the strategy engine"""
        try:
            # Initialize Redis connection
            self.redis_client = aioredis.from_url(self.redis_url)
            await self.redis_client.ping()
            
            logger.info("Generative strategy engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing generative strategy engine: {str(e)}")
            raise
    
    async def synthesize_strategy(self, objective: StrategyObjective, 
                                preferred_model: AIModel = None,
                                custom_context: Dict[str, Any] = None) -> GeneratedStrategy:
        """Main method to synthesize a new trading strategy"""
        try:
            start_time = time.time()
            
            logger.info(f"Synthesizing strategy with objective: {objective.target_return:.1%} return, "
                       f"{objective.max_drawdown:.1%} max drawdown")
            
            # Analyze current market context
            market_context = await self.market_analyzer.analyze_current_market_context()
            
            # Override with custom context if provided
            if custom_context:
                for key, value in custom_context.items():
                    if hasattr(market_context, key):
                        setattr(market_context, key, value)
            
            # Select AI model
            model = preferred_model or self._select_optimal_model(objective, market_context)
            
            # Generate strategy using ensemble approach
            strategy = await self._generate_strategy_with_ensemble(
                objective, market_context, model
            )
            
            # Validate generated strategy
            validation_result = await self.validator.validate_strategy_code(strategy.code)
            
            if not validation_result['is_valid']:
                # Attempt to fix issues and regenerate
                strategy = await self._fix_and_regenerate_strategy(
                    strategy, validation_result, objective, market_context, model
                )
            
            # Store strategy
            self.generated_strategies[strategy.strategy_id] = strategy
            
            # Cache strategy
            await self._cache_strategy(strategy)
            
            # Update metrics
            generation_time = time.time() - start_time
            self.strategies_generated.labels(
                model=model.value,
                type=strategy.strategy_type.value
            ).inc()
            self.generation_latency.observe(generation_time)
            self.strategy_performance.labels(strategy_id=strategy.strategy_id).set(strategy.confidence_score)
            
            logger.info(f"Strategy synthesized: {strategy.strategy_id} ({generation_time:.2f}s)")
            return strategy
            
        except Exception as e:
            logger.error(f"Error synthesizing strategy: {str(e)}")
            raise
    
    async def evolve_strategy(self, strategy_id: str, 
                            performance_feedback: Dict[str, Any]) -> GeneratedStrategy:
        """Evolve existing strategy based on performance feedback"""
        try:
            if strategy_id not in self.generated_strategies:
                raise ValueError(f"Strategy not found: {strategy_id}")
            
            original_strategy = self.generated_strategies[strategy_id]
            
            logger.info(f"Evolving strategy: {strategy_id}")
            
            # Create optimization prompt
            optimization_prompt = self.prompt_engineer.create_optimization_prompt(
                original_strategy, performance_feedback
            )
            
            # Generate evolved strategy
            model = original_strategy.ai_model_used
            evolved_code = await self.llm_provider.generate_response(
                model, optimization_prompt, "strategy_optimization"
            )
            
            # Create evolved strategy
            evolved_strategy = GeneratedStrategy(
                strategy_id=str(uuid.uuid4()),
                name=f"{original_strategy.name}_evolved",
                description=f"Evolved version of {original_strategy.name}",
                strategy_type=original_strategy.strategy_type,
                code=evolved_code,
                parameters=original_strategy.parameters.copy(),
                expected_performance=await self._estimate_performance(evolved_code),
                risk_metrics=await self._estimate_risk_metrics(evolved_code),
                market_conditions=original_strategy.market_conditions.copy(),
                confidence_score=min(original_strategy.confidence_score + 0.1, 1.0),
                backtest_results=None,
                ai_model_used=model,
                generation_timestamp=datetime.now(),
                last_updated=datetime.now()
            )
            
            # Validate evolved strategy
            validation_result = await self.validator.validate_strategy_code(evolved_strategy.code)
            
            if validation_result['is_valid']:
                # Store evolved strategy
                self.generated_strategies[evolved_strategy.strategy_id] = evolved_strategy
                
                # Track evolution
                evolution = StrategyEvolution(
                    original_strategy_id=strategy_id,
                    evolved_strategy_id=evolved_strategy.strategy_id,
                    evolution_type="performance_optimization",
                    changes_made=await self._identify_changes(original_strategy.code, evolved_strategy.code),
                    performance_improvement=0.05,  # Would calculate actual improvement
                    confidence_change=evolved_strategy.confidence_score - original_strategy.confidence_score,
                    evolution_timestamp=datetime.now()
                )
                
                self.strategy_evolution_history[evolved_strategy.strategy_id] = evolution
                
                logger.info(f"Strategy evolved successfully: {evolved_strategy.strategy_id}")
                return evolved_strategy
            else:
                logger.warning(f"Evolved strategy validation failed: {validation_result}")
                return original_strategy
                
        except Exception as e:
            logger.error(f"Error evolving strategy: {str(e)}")
            raise
    
    async def batch_generate_strategies(self, objectives: List[StrategyObjective],
                                      max_concurrent: int = 3) -> List[GeneratedStrategy]:
        """Generate multiple strategies concurrently"""
        try:
            logger.info(f"Batch generating {len(objectives)} strategies")
            
            # Create semaphore to limit concurrent generations
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def generate_single(objective):
                async with semaphore:
                    return await self.synthesize_strategy(objective)
            
            # Generate strategies concurrently
            tasks = [generate_single(obj) for obj in objectives]
            strategies = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions
            successful_strategies = [
                s for s in strategies if isinstance(s, GeneratedStrategy)
            ]
            
            logger.info(f"Batch generation completed: {len(successful_strategies)}/{len(objectives)} successful")
            return successful_strategies
            
        except Exception as e:
            logger.error(f"Error in batch strategy generation: {str(e)}")
            return []
    
    async def get_strategy_recommendations(self, portfolio_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get strategy recommendations based on portfolio context"""
        try:
            # Analyze current market conditions
            market_context = await self.market_analyzer.analyze_current_market_context()
            
            recommendations = []
            
            # Generate recommendations based on market regime
            if market_context.regime == MarketRegime.BULL_MARKET:
                recommendations.append({
                    'strategy_type': StrategyType.MOMENTUM,
                    'rationale': 'Bull market conditions favor momentum strategies',
                    'target_return': 0.15,
                    'risk_level': 'medium'
                })
                
            elif market_context.regime == MarketRegime.BEAR_MARKET:
                recommendations.append({
                    'strategy_type': StrategyType.MEAN_REVERSION,
                    'rationale': 'Bear market conditions favor mean reversion strategies',
                    'target_return': 0.08,
                    'risk_level': 'low'
                })
                
            elif market_context.regime == MarketRegime.HIGH_VOLATILITY:
                recommendations.append({
                    'strategy_type': StrategyType.VOLATILITY,
                    'rationale': 'High volatility environment suitable for volatility strategies',
                    'target_return': 0.12,
                    'risk_level': 'high'
                })
            
            # Add market making recommendation for low volatility
            if market_context.volatility_level < 0.15:
                recommendations.append({
                    'strategy_type': StrategyType.MARKET_MAKING,
                    'rationale': 'Low volatility environment suitable for market making',
                    'target_return': 0.10,
                    'risk_level': 'low'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting strategy recommendations: {str(e)}")
            return []
    
    def _select_optimal_model(self, objective: StrategyObjective, 
                            market_context: MarketContext) -> AIModel:
        """Select optimal AI model for strategy generation"""
        try:
            # Simple model selection logic
            if market_context.regime in [MarketRegime.CRISIS, MarketRegime.HIGH_VOLATILITY]:
                return AIModel.CLAUDE_3_OPUS  # More conservative for complex situations
            elif objective.target_return > 0.2:
                return AIModel.GPT_4  # More aggressive for high return targets
            else:
                return AIModel.CLAUDE_3_SONNET  # Balanced approach
                
        except Exception as e:
            logger.error(f"Error selecting optimal model: {str(e)}")
            return AIModel.GPT_4  # Default fallback
    
    async def _generate_strategy_with_ensemble(self, objective: StrategyObjective,
                                             market_context: MarketContext,
                                             primary_model: AIModel) -> GeneratedStrategy:
        """Generate strategy using ensemble approach"""
        try:
            # Create generation prompt
            prompt = self.prompt_engineer.create_strategy_generation_prompt(objective, market_context)
            
            # Generate strategy code
            strategy_code = await self.llm_provider.generate_response(
                primary_model, prompt, "strategy_generation"
            )
            
            # Extract strategy metadata from code
            strategy_name = await self._extract_strategy_name(strategy_code)
            strategy_type = await self._infer_strategy_type(strategy_code, objective.strategy_types)
            
            # Create strategy object
            strategy = GeneratedStrategy(
                strategy_id=str(uuid.uuid4()),
                name=strategy_name,
                description=f"AI-generated {strategy_type.value} strategy",
                strategy_type=strategy_type,
                code=strategy_code,
                parameters=await self._extract_parameters(strategy_code),
                expected_performance=await self._estimate_performance(strategy_code),
                risk_metrics=await self._estimate_risk_metrics(strategy_code),
                market_conditions=[market_context.regime.value],
                confidence_score=await self._calculate_confidence_score(strategy_code, market_context),
                backtest_results=None,
                ai_model_used=primary_model,
                generation_timestamp=datetime.now(),
                last_updated=datetime.now()
            )
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error generating strategy with ensemble: {str(e)}")
            raise
    
    async def _fix_and_regenerate_strategy(self, strategy: GeneratedStrategy,
                                         validation_result: Dict[str, Any],
                                         objective: StrategyObjective,
                                         market_context: MarketContext,
                                         model: AIModel) -> GeneratedStrategy:
        """Fix validation issues and regenerate strategy"""
        try:
            # Create fix prompt
            fix_prompt = f"""
Fix the following issues in this trading strategy code:

ISSUES TO FIX:
{', '.join(validation_result.get('syntax_errors', []))}
{', '.join(validation_result.get('security_issues', []))}
{', '.join(validation_result.get('missing_methods', []))}

ORIGINAL CODE:
{strategy.code}

Return the corrected code that addresses all issues while maintaining the strategy logic.
"""
            
            # Generate fixed code
            fixed_code = await self.llm_provider.generate_response(
                model, fix_prompt, "code_fixing"
            )
            
            # Update strategy with fixed code
            strategy.code = fixed_code
            strategy.last_updated = datetime.now()
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error fixing strategy: {str(e)}")
            return strategy
    
    async def _extract_strategy_name(self, code: str) -> str:
        """Extract strategy name from code"""
        try:
            # Look for class definition
            lines = code.split('\n')
            for line in lines:
                if 'class ' in line and 'Strategy' in line:
                    # Extract class name
                    class_name = line.split('class ')[1].split('(')[0].split(':')[0].strip()
                    return class_name
            
            return "Generated Strategy"
            
        except Exception as e:
            logger.error(f"Error extracting strategy name: {str(e)}")
            return "Generated Strategy"
    
    async def _infer_strategy_type(self, code: str, preferred_types: List[StrategyType]) -> StrategyType:
        """Infer strategy type from code"""
        try:
            code_lower = code.lower()
            
            # Check for strategy type indicators in code
            if 'momentum' in code_lower:
                return StrategyType.MOMENTUM
            elif 'mean_reversion' in code_lower or 'mean reversion' in code_lower:
                return StrategyType.MEAN_REVERSION
            elif 'arbitrage' in code_lower:
                return StrategyType.ARBITRAGE
            elif 'market_making' in code_lower or 'market making' in code_lower:
                return StrategyType.MARKET_MAKING
            elif 'trend' in code_lower:
                return StrategyType.TREND_FOLLOWING
            elif 'volatility' in code_lower:
                return StrategyType.VOLATILITY
            elif 'pairs' in code_lower:
                return StrategyType.PAIRS_TRADING
            
            # Default to first preferred type or momentum
            return preferred_types[0] if preferred_types else StrategyType.MOMENTUM
            
        except Exception as e:
            logger.error(f"Error inferring strategy type: {str(e)}")
            return StrategyType.MOMENTUM
    
    async def _extract_parameters(self, code: str) -> Dict[str, Any]:
        """Extract strategy parameters from code"""
        try:
            parameters = {}
            
            # Look for parameter definitions in __init__ method
            lines = code.split('\n')
            in_init = False
            
            for line in lines:
                if 'def __init__' in line:
                    in_init = True
                    continue
                elif in_init and line.strip().startswith('def '):
                    break
                elif in_init and '=' in line and 'self.' in line:
                    # Extract parameter
                    try:
                        param_line = line.strip()
                        if param_line.startswith('self.'):
                            param_name = param_line.split('self.')[1].split('=')[0].strip()
                            param_value = param_line.split('=')[1].strip()
                            
                            # Try to evaluate simple values
                            try:
                                parameters[param_name] = ast.literal_eval(param_value)
                            except:
                                parameters[param_name] = param_value
                    except:
                        continue
            
            return parameters
            
        except Exception as e:
            logger.error(f"Error extracting parameters: {str(e)}")
            return {}
    
    async def _estimate_performance(self, code: str) -> Dict[str, float]:
        """Estimate strategy performance metrics"""
        try:
            # Mock performance estimation based on strategy characteristics
            return {
                'expected_annual_return': 0.12,
                'expected_volatility': 0.18,
                'expected_sharpe_ratio': 0.67,
                'expected_max_drawdown': 0.08,
                'expected_win_rate': 0.55
            }
            
        except Exception as e:
            logger.error(f"Error estimating performance: {str(e)}")
            return {}
    
    async def _estimate_risk_metrics(self, code: str) -> Dict[str, float]:
        """Estimate strategy risk metrics"""
        try:
            # Mock risk estimation
            return {
                'var_95': 0.03,
                'var_99': 0.05,
                'beta': 0.8,
                'correlation_to_market': 0.6,
                'tail_risk': 0.02
            }
            
        except Exception as e:
            logger.error(f"Error estimating risk metrics: {str(e)}")
            return {}
    
    async def _calculate_confidence_score(self, code: str, market_context: MarketContext) -> float:
        """Calculate confidence score for generated strategy"""
        try:
            score = 0.7  # Base score
            
            # Adjust based on market context
            if market_context.regime in [MarketRegime.BULL_MARKET, MarketRegime.BEAR_MARKET]:
                score += 0.1  # Higher confidence in trending markets
            
            if market_context.volatility_level < 0.25:
                score += 0.1  # Higher confidence in stable volatility
            
            # Adjust based on code quality
            if 'def ' in code and 'class ' in code:
                score += 0.1  # Well-structured code
            
            if len(code) > 500:
                score += 0.1  # Comprehensive implementation
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {str(e)}")
            return 0.5
    
    async def _identify_changes(self, original_code: str, evolved_code: str) -> List[str]:
        """Identify changes between original and evolved strategy"""
        try:
            changes = []
            
            # Simple change detection
            if len(evolved_code) > len(original_code) * 1.1:
                changes.append("Significant code expansion")
            
            if 'volatility' in evolved_code and 'volatility' not in original_code:
                changes.append("Added volatility adjustment")
            
            if 'risk' in evolved_code and 'risk' not in original_code:
                changes.append("Enhanced risk management")
            
            return changes
            
        except Exception as e:
            logger.error(f"Error identifying changes: {str(e)}")
            return ["General optimization"]
    
    async def _cache_strategy(self, strategy: GeneratedStrategy):
        """Cache strategy in Redis"""
        try:
            if self.redis_client:
                strategy_data = asdict(strategy)
                # Convert datetime objects to strings for JSON serialization
                strategy_data['generation_timestamp'] = strategy.generation_timestamp.isoformat()
                strategy_data['last_updated'] = strategy.last_updated.isoformat()
                
                await self.redis_client.setex(
                    f"strategy:{strategy.strategy_id}",
                    86400,  # 24 hour TTL
                    json.dumps(strategy_data, default=str)
                )
                
        except Exception as e:
            logger.error(f"Error caching strategy: {str(e)}")
    
    async def get_strategy_status(self) -> Dict[str, Any]:
        """Get status of strategy generation engine"""
        try:
            return {
                'timestamp': datetime.now().isoformat(),
                'total_strategies_generated': len(self.generated_strategies),
                'strategies_by_type': self._count_strategies_by_type(),
                'evolution_history_count': len(self.strategy_evolution_history),
                'average_confidence_score': self._calculate_average_confidence(),
                'supported_models': [model.value for model in AIModel],
                'last_generation': max([s.generation_timestamp for s in self.generated_strategies.values()]).isoformat() if self.generated_strategies else None
            }
            
        except Exception as e:
            logger.error(f"Error getting strategy status: {str(e)}")
            return {'error': str(e)}
    
    def _count_strategies_by_type(self) -> Dict[str, int]:
        """Count strategies by type"""
        counts = {}
        for strategy in self.generated_strategies.values():
            strategy_type = strategy.strategy_type.value
            counts[strategy_type] = counts.get(strategy_type, 0) + 1
        return counts
    
    def _calculate_average_confidence(self) -> float:
        """Calculate average confidence score"""
        if not self.generated_strategies:
            return 0.0
        
        total_confidence = sum(s.confidence_score for s in self.generated_strategies.values())
        return total_confidence / len(self.generated_strategies)
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Generative strategy engine cleanup completed")
            
        except Exception as e:
            logger.error(f"Error in cleanup: {str(e)}")


# Example usage and testing
if __name__ == "__main__":
    async def test_generative_strategy_engine():
        """Test generative strategy engine"""
        
        # Initialize engine
        engine = GenerativeStrategyEngine()
        await engine.initialize()
        
        try:
            # Define strategy objective
            objective = StrategyObjective(
                target_return=0.15,
                max_drawdown=0.08,
                sharpe_ratio_target=1.0,
                max_positions=10,
                holding_period_min=1,
                holding_period_max=30,
                risk_tolerance=0.05,
                market_neutrality=0.0,
                preferred_assets=['SPY', 'QQQ', 'IWM'],
                excluded_assets=['SPXL', 'TQQQ'],
                strategy_types=[StrategyType.MOMENTUM, StrategyType.MEAN_REVERSION],
                additional_constraints={}
            )
            
            print("🤖 Testing Generative AI Strategy Engine...")
            
            # Generate strategy
            print("\n🎯 Generating trading strategy...")
            strategy = await engine.synthesize_strategy(objective)
            
            print(f"✅ Strategy Generated:")
            print(f"  ID: {strategy.strategy_id}")
            print(f"  Name: {strategy.name}")
            print(f"  Type: {strategy.strategy_type.value}")
            print(f"  Confidence: {strategy.confidence_score:.2f}")
            print(f"  Model Used: {strategy.ai_model_used.value}")
            
            print(f"\n📊 Expected Performance:")
            for metric, value in strategy.expected_performance.items():
                print(f"  {metric}: {value:.2f}")
            
            print(f"\n📝 Generated Code Preview:")
            code_lines = strategy.code.split('\n')[:15]
            for i, line in enumerate(code_lines, 1):
                print(f"  {i:2d}: {line}")
            print(f"  ... (showing first 15 lines of {len(strategy.code.split())} total lines)")
            
            # Get strategy recommendations
            print(f"\n💡 Getting strategy recommendations...")
            recommendations = await engine.get_strategy_recommendations({})
            
            print(f"📋 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec['strategy_type'].value}: {rec['rationale']}")
                print(f"     Target Return: {rec['target_return']:.1%}, Risk: {rec['risk_level']}")
            
            # Test strategy evolution
            print(f"\n🔄 Testing strategy evolution...")
            performance_feedback = {
                'low_sharpe': True,
                'target_sharpe': 1.2,
                'high_turnover': True
            }
            
            evolved_strategy = await engine.evolve_strategy(strategy.strategy_id, performance_feedback)
            
            print(f"🚀 Strategy Evolution:")
            print(f"  Original: {strategy.strategy_id}")
            print(f"  Evolved: {evolved_strategy.strategy_id}")
            print(f"  Confidence Change: {evolved_strategy.confidence_score - strategy.confidence_score:.2f}")
            
            # Get engine status
            print(f"\n📈 Engine Status:")
            status = await engine.get_strategy_status()
            print(f"  Total Strategies: {status['total_strategies_generated']}")
            print(f"  Average Confidence: {status['average_confidence_score']:.2f}")
            print(f"  Strategies by Type: {status['strategies_by_type']}")
            
            print(f"\n✅ Generative AI strategy engine test completed!")
            
        finally:
            # Cleanup
            await engine.cleanup()
    
    # Run the test
    asyncio.run(test_generative_strategy_engine())