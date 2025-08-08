"""
Real-time signal processing service for live strategy execution.
"""

import asyncio
import logging
import json
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
from enum import Enum

import redis.asyncio as redis
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.execution import ExecutionSignal, StrategyExecution
from app.models.strategy import Strategy
from app.services.live_execution_engine import live_execution_engine, SignalData
from app.services.market_data_service import market_data_service, Tick, Quote, Bar
from app.database.connection import get_db_session


class SignalPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProcessingMode(Enum):
    REAL_TIME = "real_time"
    BATCH = "batch"
    STREAM = "stream"


@dataclass
class SignalContext:
    """Context information for signal processing."""
    strategy_execution_id: int
    symbol: str
    timeframe: str
    timestamp: datetime
    market_data: Dict[str, Any]
    historical_data: List[Dict[str, Any]]
    indicators: Dict[str, Any]
    features: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class ProcessedSignal:
    """Processed signal with enhanced information."""
    original_signal: SignalData
    processed_at: datetime
    processing_latency_ms: int
    confidence_score: float
    risk_score: float
    market_regime: str
    correlation_score: float
    execution_recommendation: str
    enhanced_metadata: Dict[str, Any]


@dataclass
class SignalStatistics:
    """Signal processing statistics."""
    total_signals: int
    processed_signals: int
    processing_errors: int
    avg_processing_time_ms: float
    signal_rate_per_minute: float
    confidence_distribution: Dict[str, int]
    symbol_distribution: Dict[str, int]


class SignalProcessor:
    """Real-time signal processing and enhancement service."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.logger = logging.getLogger(__name__)
        self.redis_url = redis_url
        self.redis = None
        
        # Processing state
        self.processor_running = False
        self.processing_queues: Dict[str, asyncio.Queue] = defaultdict(lambda: asyncio.Queue())
        self.signal_buffers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Statistics tracking
        self.signal_stats: Dict[int, SignalStatistics] = {}
        self.processing_times: Dict[int, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Market regime detection
        self.market_regimes: Dict[str, str] = {}  # symbol -> regime
        self.regime_indicators: Dict[str, Dict] = defaultdict(dict)
        
        # Signal correlation tracking
        self.signal_correlations: Dict[Tuple[str, str], float] = {}
        
        # Configuration
        self.max_queue_size = 1000
        self.batch_size = 10
        self.processing_interval = 0.1  # 100ms
        self.confidence_threshold = 0.5
        self.correlation_window = 100
        
        # Signal enhancement callbacks
        self.signal_enhancers: List[Callable] = []
        self.signal_filters: List[Callable] = []
        self.signal_validators: List[Callable] = []
        
    async def initialize(self) -> None:
        """Initialize the signal processor."""
        
        # Connect to Redis
        self.redis = redis.from_url(self.redis_url)
        
        # Load active strategy executions
        await self._load_active_strategies()
        
        # Start processing loops
        if not self.processor_running:
            self.processor_running = True
            asyncio.create_task(self._signal_processing_loop())
            asyncio.create_task(self._batch_processing_loop())
            asyncio.create_task(self._market_regime_detection_loop())
            asyncio.create_task(self._statistics_collection_loop())
        
        self.logger.info("Signal processor initialized")
    
    async def _load_active_strategies(self) -> None:
        """Load active strategy executions for signal processing."""
        
        try:
            with get_db_session() as db:
                active_executions = db.query(StrategyExecution).filter(
                    StrategyExecution.status == "running"
                ).all()
                
                for execution in active_executions:
                    # Initialize statistics
                    self.signal_stats[execution.id] = SignalStatistics(
                        total_signals=0,
                        processed_signals=0,
                        processing_errors=0,
                        avg_processing_time_ms=0.0,
                        signal_rate_per_minute=0.0,
                        confidence_distribution={},
                        symbol_distribution={}
                    )
                
            self.logger.info(f"Loaded {len(active_executions)} active strategies for signal processing")
            
        except Exception as e:
            self.logger.error(f"Error loading active strategies: {e}")
    
    async def process_signal(
        self, 
        signal_data: SignalData, 
        priority: SignalPriority = SignalPriority.MEDIUM,
        processing_mode: ProcessingMode = ProcessingMode.REAL_TIME
    ) -> Optional[ProcessedSignal]:
        """Process a trading signal with enhancement and validation."""
        
        start_time = datetime.utcnow()
        
        try:
            # Update statistics
            if signal_data.strategy_execution_id in self.signal_stats:
                self.signal_stats[signal_data.strategy_execution_id].total_signals += 1
            
            # Create signal context
            context = await self._create_signal_context(signal_data)
            
            # Apply signal filters
            if not await self._apply_signal_filters(signal_data, context):
                self.logger.debug(f"Signal filtered out for {signal_data.symbol}")
                return None
            
            # Validate signal
            validation_result = await self._validate_signal(signal_data, context)
            if not validation_result["valid"]:
                self.logger.warning(f"Signal validation failed: {validation_result['errors']}")
                return None
            
            # Enhance signal
            enhanced_signal = await self._enhance_signal(signal_data, context)
            
            # Calculate processing latency
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Create processed signal
            processed_signal = ProcessedSignal(
                original_signal=signal_data,
                processed_at=datetime.utcnow(),
                processing_latency_ms=int(processing_time),
                confidence_score=enhanced_signal.get("confidence_score", 0.5),
                risk_score=enhanced_signal.get("risk_score", 0.5),
                market_regime=enhanced_signal.get("market_regime", "unknown"),
                correlation_score=enhanced_signal.get("correlation_score", 0.0),
                execution_recommendation=enhanced_signal.get("execution_recommendation", "proceed"),
                enhanced_metadata=enhanced_signal.get("metadata", {})
            )
            
            # Update processing statistics
            await self._update_processing_stats(signal_data.strategy_execution_id, processing_time)
            
            # Store processed signal
            await self._store_processed_signal(processed_signal)
            
            # Submit to execution engine if recommended
            if processed_signal.execution_recommendation == "proceed":
                await live_execution_engine.submit_signal(signal_data)
            
            return processed_signal
            
        except Exception as e:
            self.logger.error(f"Error processing signal: {e}")
            
            # Update error statistics
            if signal_data.strategy_execution_id in self.signal_stats:
                self.signal_stats[signal_data.strategy_execution_id].processing_errors += 1
            
            return None
    
    async def _create_signal_context(self, signal_data: SignalData) -> SignalContext:
        """Create context for signal processing."""
        
        try:
            # Get current market data
            current_quote = await market_data_service.get_current_quote(signal_data.symbol)
            market_data = {}
            
            if current_quote:
                market_data = {
                    "bid": float(current_quote.bid),
                    "ask": float(current_quote.ask),
                    "spread": float(current_quote.spread),
                    "timestamp": current_quote.timestamp.isoformat()
                }
            
            # Get historical data
            historical_data = await self._get_historical_context(
                signal_data.symbol, 
                signal_data.timeframe
            )
            
            # Calculate technical indicators
            indicators = await self._calculate_indicators(signal_data.symbol, historical_data)
            
            # Extract features for ML models
            features = await self._extract_features(signal_data, historical_data, indicators)
            
            return SignalContext(
                strategy_execution_id=signal_data.strategy_execution_id,
                symbol=signal_data.symbol,
                timeframe=signal_data.timeframe,
                timestamp=datetime.utcnow(),
                market_data=market_data,
                historical_data=historical_data,
                indicators=indicators,
                features=features,
                metadata=signal_data.metadata or {}
            )
            
        except Exception as e:
            self.logger.error(f"Error creating signal context: {e}")
            # Return minimal context
            return SignalContext(
                strategy_execution_id=signal_data.strategy_execution_id,
                symbol=signal_data.symbol,
                timeframe=signal_data.timeframe,
                timestamp=datetime.utcnow(),
                market_data={},
                historical_data=[],
                indicators={},
                features={},
                metadata={}
            )
    
    async def _get_historical_context(self, symbol: str, timeframe: str, lookback_periods: int = 100) -> List[Dict[str, Any]]:
        """Get historical market data for context."""
        
        try:
            # Get historical bars
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=lookback_periods)
            
            bars = await market_data_service.get_historical_bars(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                limit=lookback_periods
            )
            
            # Convert to dictionary format
            historical_data = []
            for bar in bars:
                historical_data.append({
                    "timestamp": bar.timestamp.isoformat(),
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": float(bar.volume)
                })
            
            return historical_data
            
        except Exception as e:
            self.logger.error(f"Error getting historical context: {e}")
            return []
    
    async def _calculate_indicators(self, symbol: str, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate technical indicators."""
        
        try:
            if len(historical_data) < 20:
                return {}
            
            # Extract price arrays
            closes = np.array([bar["close"] for bar in historical_data])
            highs = np.array([bar["high"] for bar in historical_data])
            lows = np.array([bar["low"] for bar in historical_data])
            volumes = np.array([bar["volume"] for bar in historical_data])
            
            indicators = {}
            
            # Moving Averages
            if len(closes) >= 20:
                indicators["sma_20"] = float(np.mean(closes[-20:]))
            if len(closes) >= 50:
                indicators["sma_50"] = float(np.mean(closes[-50:]))
            
            # RSI (simplified)
            if len(closes) >= 14:
                deltas = np.diff(closes)
                gains = np.where(deltas > 0, deltas, 0)
                losses = np.where(deltas < 0, -deltas, 0)
                
                avg_gain = np.mean(gains[-14:])
                avg_loss = np.mean(losses[-14:])
                
                if avg_loss != 0:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                    indicators["rsi"] = float(rsi)
            
            # Bollinger Bands
            if len(closes) >= 20:
                sma_20 = np.mean(closes[-20:])
                std_20 = np.std(closes[-20:])
                indicators["bb_upper"] = float(sma_20 + 2 * std_20)
                indicators["bb_lower"] = float(sma_20 - 2 * std_20)
                indicators["bb_middle"] = float(sma_20)
            
            # MACD (simplified)
            if len(closes) >= 26:
                ema_12 = closes[-12:].mean()  # Simplified EMA
                ema_26 = closes[-26:].mean()
                macd_line = ema_12 - ema_26
                indicators["macd"] = float(macd_line)
            
            # Volatility
            if len(closes) >= 20:
                returns = np.diff(np.log(closes[-20:]))
                volatility = np.std(returns) * np.sqrt(252)  # Annualized
                indicators["volatility"] = float(volatility)
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return {}
    
    async def _extract_features(
        self, 
        signal_data: SignalData, 
        historical_data: List[Dict[str, Any]], 
        indicators: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract features for ML models."""
        
        try:
            features = {}
            
            # Price-based features
            if historical_data:
                recent_prices = [bar["close"] for bar in historical_data[-10:]]
                if recent_prices:
                    features["price_momentum"] = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
                    features["price_volatility"] = float(np.std(recent_prices))
                    features["price_trend"] = 1 if recent_prices[-1] > recent_prices[-5] else -1
            
            # Technical indicator features
            for key, value in indicators.items():
                features[f"indicator_{key}"] = value
            
            # Market microstructure features
            current_price = await market_data_service.get_current_price(signal_data.symbol)
            if current_price and historical_data:
                last_close = historical_data[-1]["close"]
                features["price_gap"] = float((current_price - Decimal(str(last_close))) / Decimal(str(last_close)))
            
            # Time-based features
            now = datetime.utcnow()
            features["hour_of_day"] = now.hour
            features["day_of_week"] = now.weekday()
            features["month"] = now.month
            
            # Volume features
            if historical_data:
                recent_volumes = [bar["volume"] for bar in historical_data[-10:]]
                if recent_volumes:
                    features["volume_ratio"] = recent_volumes[-1] / np.mean(recent_volumes[:-1]) if len(recent_volumes) > 1 else 1.0
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error extracting features: {e}")
            return {}
    
    async def _apply_signal_filters(self, signal_data: SignalData, context: SignalContext) -> bool:
        """Apply signal filters to determine if signal should be processed."""
        
        try:
            # Market hours filter
            if not await self._is_market_open(signal_data.symbol):
                return False
            
            # Minimum confidence filter
            if signal_data.confidence and signal_data.confidence < self.confidence_threshold:
                return False
            
            # Spread filter (avoid wide spreads)
            if context.market_data:
                spread_pct = context.market_data.get("spread", 0) / context.market_data.get("ask", 1)
                if spread_pct > 0.01:  # 1% spread threshold
                    return False
            
            # Apply custom filters
            for filter_func in self.signal_filters:
                try:
                    if not await filter_func(signal_data, context):
                        return False
                except Exception as e:
                    self.logger.error(f"Error in signal filter: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying signal filters: {e}")
            return False
    
    async def _is_market_open(self, symbol: str) -> bool:
        """Check if market is open for the symbol."""
        
        # Simplified market hours check
        # In practice, this would check specific market hours for different exchanges
        now = datetime.utcnow()
        
        # Assume US market hours (9:30 AM - 4:00 PM ET)
        # Convert to UTC: 14:30 - 21:00 (EST) or 13:30 - 20:00 (EDT)
        market_open = 14 if now.month in [11, 12, 1, 2, 3] else 13  # EST vs EDT
        market_close = 21 if now.month in [11, 12, 1, 2, 3] else 20
        
        # Check if it's a weekday and within market hours
        if now.weekday() < 5:  # Monday = 0, Sunday = 6
            return market_open <= now.hour < market_close
        
        return False
    
    async def _validate_signal(self, signal_data: SignalData, context: SignalContext) -> Dict[str, Any]:
        """Validate signal data and context."""
        
        errors = []
        warnings = []
        
        try:
            # Basic validation
            if not signal_data.symbol:
                errors.append("Missing symbol")
            
            if not signal_data.action:
                errors.append("Missing action")
            
            if signal_data.action not in ["buy", "sell", "hold"]:
                errors.append("Invalid action")
            
            # Price validation
            if signal_data.price and signal_data.price <= 0:
                errors.append("Invalid price")
            
            # Quantity validation
            if signal_data.quantity and signal_data.quantity <= 0:
                errors.append("Invalid quantity")
            
            # Market data validation
            if not context.market_data:
                warnings.append("No current market data available")
            
            # Historical data validation
            if len(context.historical_data) < 10:
                warnings.append("Limited historical data")
            
            # Apply custom validators
            for validator_func in self.signal_validators:
                try:
                    result = await validator_func(signal_data, context)
                    if result.get("errors"):
                        errors.extend(result["errors"])
                    if result.get("warnings"):
                        warnings.extend(result["warnings"])
                except Exception as e:
                    self.logger.error(f"Error in signal validator: {e}")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            }
            
        except Exception as e:
            self.logger.error(f"Error validating signal: {e}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": []
            }
    
    async def _enhance_signal(self, signal_data: SignalData, context: SignalContext) -> Dict[str, Any]:
        """Enhance signal with additional information and analysis."""
        
        try:
            enhanced = {}
            
            # Calculate confidence score
            confidence_score = await self._calculate_confidence_score(signal_data, context)
            enhanced["confidence_score"] = confidence_score
            
            # Calculate risk score
            risk_score = await self._calculate_risk_score(signal_data, context)
            enhanced["risk_score"] = risk_score
            
            # Detect market regime
            market_regime = await self._detect_market_regime(signal_data.symbol, context)
            enhanced["market_regime"] = market_regime
            
            # Calculate correlation score
            correlation_score = await self._calculate_correlation_score(signal_data, context)
            enhanced["correlation_score"] = correlation_score
            
            # Generate execution recommendation
            execution_recommendation = await self._generate_execution_recommendation(
                signal_data, context, confidence_score, risk_score
            )
            enhanced["execution_recommendation"] = execution_recommendation
            
            # Apply signal enhancers
            for enhancer_func in self.signal_enhancers:
                try:
                    enhancement = await enhancer_func(signal_data, context)
                    enhanced.update(enhancement)
                except Exception as e:
                    self.logger.error(f"Error in signal enhancer: {e}")
            
            # Add metadata
            enhanced["metadata"] = {
                "processing_timestamp": datetime.utcnow().isoformat(),
                "market_data_timestamp": context.market_data.get("timestamp"),
                "indicator_count": len(context.indicators),
                "feature_count": len(context.features),
                "historical_data_points": len(context.historical_data)
            }
            
            return enhanced
            
        except Exception as e:
            self.logger.error(f"Error enhancing signal: {e}")
            return {}
    
    async def _calculate_confidence_score(self, signal_data: SignalData, context: SignalContext) -> float:
        """Calculate confidence score for the signal."""
        
        try:
            # Start with provided confidence or default
            base_confidence = signal_data.confidence or 0.5
            
            # Adjust based on market data quality
            market_data_quality = 1.0 if context.market_data else 0.5
            
            # Adjust based on historical data availability
            historical_data_quality = min(1.0, len(context.historical_data) / 50.0)
            
            # Adjust based on technical indicators
            indicator_agreement = await self._calculate_indicator_agreement(context.indicators, signal_data.action)
            
            # Adjust based on market regime
            regime_adjustment = 1.0
            market_regime = self.market_regimes.get(signal_data.symbol, "unknown")
            if market_regime == "trending" and signal_data.action != "hold":
                regime_adjustment = 1.1
            elif market_regime == "sideways" and signal_data.action == "hold":
                regime_adjustment = 1.1
            
            # Calculate weighted confidence
            confidence = base_confidence * market_data_quality * historical_data_quality * indicator_agreement * regime_adjustment
            
            # Cap between 0 and 1
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence score: {e}")
            return 0.5
    
    async def _calculate_indicator_agreement(self, indicators: Dict[str, Any], action: str) -> float:
        """Calculate how well technical indicators agree with the signal."""
        
        try:
            if not indicators:
                return 0.5
            
            agreements = []
            
            # RSI agreement
            if "rsi" in indicators:
                rsi = indicators["rsi"]
                if action == "buy" and rsi < 30:
                    agreements.append(1.0)  # Oversold, good for buying
                elif action == "sell" and rsi > 70:
                    agreements.append(1.0)  # Overbought, good for selling
                elif action == "hold" and 30 <= rsi <= 70:
                    agreements.append(1.0)  # Neutral zone
                else:
                    agreements.append(0.3)  # Disagreement
            
            # Moving average agreement
            if "sma_20" in indicators and "sma_50" in indicators:
                sma_20 = indicators["sma_20"]
                sma_50 = indicators["sma_50"]
                
                if action == "buy" and sma_20 > sma_50:
                    agreements.append(1.0)  # Uptrend
                elif action == "sell" and sma_20 < sma_50:
                    agreements.append(1.0)  # Downtrend
                else:
                    agreements.append(0.5)
            
            # MACD agreement
            if "macd" in indicators:
                macd = indicators["macd"]
                if action == "buy" and macd > 0:
                    agreements.append(1.0)
                elif action == "sell" and macd < 0:
                    agreements.append(1.0)
                else:
                    agreements.append(0.5)
            
            return np.mean(agreements) if agreements else 0.5
            
        except Exception as e:
            self.logger.error(f"Error calculating indicator agreement: {e}")
            return 0.5
    
    async def _calculate_risk_score(self, signal_data: SignalData, context: SignalContext) -> float:
        """Calculate risk score for the signal."""
        
        try:
            risk_factors = []
            
            # Volatility risk
            if "volatility" in context.indicators:
                volatility = context.indicators["volatility"]
                risk_factors.append(min(1.0, volatility / 0.5))  # Normalize by 50% volatility
            
            # Spread risk
            if context.market_data:
                spread_pct = context.market_data.get("spread", 0) / context.market_data.get("ask", 1)
                risk_factors.append(min(1.0, spread_pct * 100))  # Convert to percentage
            
            # Time risk (higher risk outside normal hours)
            now = datetime.utcnow()
            if not await self._is_market_open(signal_data.symbol):
                risk_factors.append(0.8)  # Higher risk after hours
            else:
                risk_factors.append(0.2)  # Lower risk during market hours
            
            # Market regime risk
            market_regime = self.market_regimes.get(signal_data.symbol, "unknown")
            if market_regime == "volatile":
                risk_factors.append(0.8)
            elif market_regime == "trending":
                risk_factors.append(0.3)
            else:
                risk_factors.append(0.5)
            
            return np.mean(risk_factors) if risk_factors else 0.5
            
        except Exception as e:
            self.logger.error(f"Error calculating risk score: {e}")
            return 0.5
    
    async def _detect_market_regime(self, symbol: str, context: SignalContext) -> str:
        """Detect current market regime for the symbol."""
        
        try:
            if len(context.historical_data) < 20:
                return "unknown"
            
            # Calculate volatility
            prices = [bar["close"] for bar in context.historical_data[-20:]]
            returns = np.diff(np.log(prices))
            volatility = np.std(returns)
            
            # Calculate trend strength
            trend_strength = abs(prices[-1] - prices[0]) / prices[0]
            
            # Classify regime
            if volatility > 0.02:  # High volatility threshold
                regime = "volatile"
            elif trend_strength > 0.05:  # Strong trend threshold
                regime = "trending"
            else:
                regime = "sideways"
            
            # Update regime cache
            self.market_regimes[symbol] = regime
            
            return regime
            
        except Exception as e:
            self.logger.error(f"Error detecting market regime: {e}")
            return "unknown"
    
    async def _calculate_correlation_score(self, signal_data: SignalData, context: SignalContext) -> float:
        """Calculate correlation score with other signals."""
        
        try:
            # Get recent signals for correlation analysis
            recent_signals = self.signal_buffers[signal_data.symbol]
            
            if len(recent_signals) < 2:
                return 0.0
            
            # Simple correlation based on signal direction agreement
            same_direction_count = 0
            total_signals = 0
            
            for recent_signal in list(recent_signals)[-10:]:  # Last 10 signals
                if recent_signal.action == signal_data.action:
                    same_direction_count += 1
                total_signals += 1
            
            correlation_score = same_direction_count / total_signals if total_signals > 0 else 0.0
            
            return correlation_score
            
        except Exception as e:
            self.logger.error(f"Error calculating correlation score: {e}")
            return 0.0
    
    async def _generate_execution_recommendation(
        self, 
        signal_data: SignalData, 
        context: SignalContext, 
        confidence_score: float, 
        risk_score: float
    ) -> str:
        """Generate execution recommendation based on signal analysis."""
        
        try:
            # High confidence, low risk = proceed
            if confidence_score > 0.7 and risk_score < 0.3:
                return "proceed"
            
            # Low confidence = reject
            if confidence_score < 0.3:
                return "reject"
            
            # High risk = defer
            if risk_score > 0.7:
                return "defer"
            
            # Medium confidence/risk = proceed with caution
            if confidence_score > 0.5 and risk_score < 0.6:
                return "proceed_cautious"
            
            # Default to defer for unclear cases
            return "defer"
            
        except Exception as e:
            self.logger.error(f"Error generating execution recommendation: {e}")
            return "defer"
    
    async def _signal_processing_loop(self) -> None:
        """Main signal processing loop."""
        
        while self.processor_running:
            try:
                # Process signals from all queues
                for queue_name, queue in self.processing_queues.items():
                    if not queue.empty():
                        try:
                            signal_data = await asyncio.wait_for(queue.get(), timeout=0.01)
                            await self.process_signal(signal_data)
                        except asyncio.TimeoutError:
                            continue
                
                await asyncio.sleep(self.processing_interval)
                
            except Exception as e:
                self.logger.error(f"Error in signal processing loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _batch_processing_loop(self) -> None:
        """Batch processing loop for efficiency."""
        
        while self.processor_running:
            try:
                # Collect signals for batch processing
                batch_signals = {}
                
                for queue_name, queue in self.processing_queues.items():
                    signals = []
                    for _ in range(self.batch_size):
                        try:
                            signal = queue.get_nowait()
                            signals.append(signal)
                        except asyncio.QueueEmpty:
                            break
                    
                    if signals:
                        batch_signals[queue_name] = signals
                
                # Process batches
                for queue_name, signals in batch_signals.items():
                    await self._process_signal_batch(signals)
                
                await asyncio.sleep(1.0)  # Batch every second
                
            except Exception as e:
                self.logger.error(f"Error in batch processing loop: {e}")
                await asyncio.sleep(5.0)
    
    async def _process_signal_batch(self, signals: List[SignalData]) -> None:
        """Process a batch of signals efficiently."""
        
        try:
            # Process signals concurrently
            tasks = [self.process_signal(signal) for signal in signals]
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            self.logger.error(f"Error processing signal batch: {e}")
    
    async def _market_regime_detection_loop(self) -> None:
        """Market regime detection loop."""
        
        while self.processor_running:
            try:
                # Update market regimes for all active symbols
                for symbol in self.market_regimes.keys():
                    # Get fresh historical data
                    historical_data = await self._get_historical_context(symbol, "1h", 50)
                    
                    if historical_data:
                        context = SignalContext(
                            strategy_execution_id=0,
                            symbol=symbol,
                            timeframe="1h",
                            timestamp=datetime.utcnow(),
                            market_data={},
                            historical_data=historical_data,
                            indicators={},
                            features={},
                            metadata={}
                        )
                        
                        regime = await self._detect_market_regime(symbol, context)
                        self.market_regimes[symbol] = regime
                
                await asyncio.sleep(300.0)  # Update every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error in market regime detection loop: {e}")
                await asyncio.sleep(300.0)
    
    async def _statistics_collection_loop(self) -> None:
        """Statistics collection loop."""
        
        while self.processor_running:
            try:
                # Update processing statistics
                for strategy_id, stats in self.signal_stats.items():
                    processing_times = self.processing_times[strategy_id]
                    
                    if processing_times:
                        stats.avg_processing_time_ms = float(np.mean(processing_times))
                    
                    # Calculate signal rate
                    # This would be more sophisticated in practice
                    stats.signal_rate_per_minute = stats.processed_signals / max(1, stats.total_signals) * 60
                
                await asyncio.sleep(60.0)  # Update every minute
                
            except Exception as e:
                self.logger.error(f"Error in statistics collection loop: {e}")
                await asyncio.sleep(60.0)
    
    async def _update_processing_stats(self, strategy_execution_id: int, processing_time_ms: float) -> None:
        """Update processing statistics."""
        
        if strategy_execution_id in self.signal_stats:
            self.signal_stats[strategy_execution_id].processed_signals += 1
            self.processing_times[strategy_execution_id].append(processing_time_ms)
    
    async def _store_processed_signal(self, processed_signal: ProcessedSignal) -> None:
        """Store processed signal for analysis."""
        
        try:
            # Store in signal buffer
            symbol = processed_signal.original_signal.symbol
            self.signal_buffers[symbol].append(processed_signal.original_signal)
            
            # Store in Redis for real-time access
            if self.redis:
                data = asdict(processed_signal)
                # Convert datetime and Decimal objects for JSON serialization
                for key, value in data.items():
                    if isinstance(value, datetime):
                        data[key] = value.isoformat()
                    elif hasattr(value, '__dict__'):
                        # Handle nested objects
                        data[key] = asdict(value) if hasattr(value, '__dict__') else str(value)
                
                await self.redis.setex(
                    f"processed_signal:{processed_signal.original_signal.strategy_execution_id}:{symbol}",
                    300,  # 5 minute expiry
                    json.dumps(data, default=str)
                )
                
        except Exception as e:
            self.logger.error(f"Error storing processed signal: {e}")
    
    def add_signal_enhancer(self, enhancer_func: Callable) -> None:
        """Add a custom signal enhancer function."""
        self.signal_enhancers.append(enhancer_func)
    
    def add_signal_filter(self, filter_func: Callable) -> None:
        """Add a custom signal filter function."""
        self.signal_filters.append(filter_func)
    
    def add_signal_validator(self, validator_func: Callable) -> None:
        """Add a custom signal validator function."""
        self.signal_validators.append(validator_func)
    
    async def get_processing_statistics(self, strategy_execution_id: Optional[int] = None) -> Dict[str, Any]:
        """Get signal processing statistics."""
        
        if strategy_execution_id:
            stats = self.signal_stats.get(strategy_execution_id)
            if stats:
                return asdict(stats)
            return {}
        else:
            # Return aggregated statistics
            total_stats = SignalStatistics(
                total_signals=sum(s.total_signals for s in self.signal_stats.values()),
                processed_signals=sum(s.processed_signals for s in self.signal_stats.values()),
                processing_errors=sum(s.processing_errors for s in self.signal_stats.values()),
                avg_processing_time_ms=np.mean([s.avg_processing_time_ms for s in self.signal_stats.values()]) if self.signal_stats else 0.0,
                signal_rate_per_minute=np.mean([s.signal_rate_per_minute for s in self.signal_stats.values()]) if self.signal_stats else 0.0,
                confidence_distribution={},
                symbol_distribution={}
            )
            
            return asdict(total_stats)
    
    async def cleanup(self) -> None:
        """Cleanup signal processor."""
        
        self.processor_running = False
        
        if self.redis:
            await self.redis.close()
        
        self.logger.info("Signal processor cleaned up")


# Global signal processor instance
signal_processor = SignalProcessor()