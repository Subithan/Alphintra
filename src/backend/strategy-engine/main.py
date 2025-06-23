import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd
import asyncpg
import redis.asyncio as redis
from kafka import KafkaConsumer, KafkaProducer
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
import ta
import ccxt.async_support as ccxt
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://alphintra:alphintra@localhost:5432/alphintra")
TIMESCALE_URL = os.getenv("TIMESCALE_URL", "postgresql://tsuser:tspass@localhost:5433/alphintra_ts")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

# Global connections
db_pool = None
ts_pool = None
redis_client = None
kafka_consumer = None
kafka_producer = None
exchange_clients = {}

class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"

class StrategyType(Enum):
    DCA = "dca"
    GRID = "grid"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    ARBITRAGE = "arbitrage"
    ML_BASED = "ml_based"

@dataclass
class TradingSignal:
    strategy_id: int
    symbol: str
    signal_type: SignalType
    strength: float  # 0-1
    confidence: float  # 0-1
    price: Optional[float] = None
    quantity: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

@dataclass
class MarketData:
    symbol: str
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    exchange: str

class BaseStrategy:
    """Base class for all trading strategies"""
    
    def __init__(self, strategy_id: int, config: Dict[str, Any]):
        self.strategy_id = strategy_id
        self.config = config
        self.is_active = True
        self.last_signal_time = None
        
    async def generate_signal(self, market_data: List[MarketData]) -> Optional[TradingSignal]:
        """Generate trading signal based on market data"""
        raise NotImplementedError
    
    async def update_config(self, new_config: Dict[str, Any]):
        """Update strategy configuration"""
        self.config.update(new_config)
    
    def validate_signal(self, signal: TradingSignal) -> bool:
        """Validate generated signal"""
        return (
            0 <= signal.strength <= 1 and
            0 <= signal.confidence <= 1 and
            signal.signal_type in SignalType
        )

class DCAStrategy(BaseStrategy):
    """Dollar Cost Averaging Strategy"""
    
    async def generate_signal(self, market_data: List[MarketData]) -> Optional[TradingSignal]:
        if not market_data:
            return None
            
        latest_data = market_data[-1]
        
        # DCA: Buy at regular intervals regardless of price
        interval_minutes = self.config.get('interval_minutes', 60)
        buy_amount = self.config.get('buy_amount', 100)
        
        if (self.last_signal_time is None or 
            (datetime.utcnow() - self.last_signal_time).total_seconds() >= interval_minutes * 60):
            
            self.last_signal_time = datetime.utcnow()
            
            return TradingSignal(
                strategy_id=self.strategy_id,
                symbol=latest_data.symbol,
                signal_type=SignalType.BUY,
                strength=0.8,
                confidence=0.9,
                price=latest_data.close_price,
                quantity=buy_amount / latest_data.close_price,
                metadata={'strategy_type': 'dca', 'interval_minutes': interval_minutes},
                timestamp=datetime.utcnow()
            )
        
        return None

class GridStrategy(BaseStrategy):
    """Grid Trading Strategy"""
    
    async def generate_signal(self, market_data: List[MarketData]) -> Optional[TradingSignal]:
        if len(market_data) < 2:
            return None
            
        latest_data = market_data[-1]
        previous_data = market_data[-2]
        
        grid_size = self.config.get('grid_size', 0.01)  # 1% grid
        base_price = self.config.get('base_price', latest_data.close_price)
        
        price_change = (latest_data.close_price - base_price) / base_price
        
        # Buy when price drops by grid_size
        if price_change <= -grid_size:
            return TradingSignal(
                strategy_id=self.strategy_id,
                symbol=latest_data.symbol,
                signal_type=SignalType.BUY,
                strength=min(abs(price_change) / grid_size, 1.0),
                confidence=0.8,
                price=latest_data.close_price,
                metadata={'strategy_type': 'grid', 'price_change': price_change},
                timestamp=datetime.utcnow()
            )
        
        # Sell when price rises by grid_size
        elif price_change >= grid_size:
            return TradingSignal(
                strategy_id=self.strategy_id,
                symbol=latest_data.symbol,
                signal_type=SignalType.SELL,
                strength=min(price_change / grid_size, 1.0),
                confidence=0.8,
                price=latest_data.close_price,
                metadata={'strategy_type': 'grid', 'price_change': price_change},
                timestamp=datetime.utcnow()
            )
        
        return None

class MomentumStrategy(BaseStrategy):
    """Momentum Trading Strategy using technical indicators"""
    
    async def generate_signal(self, market_data: List[MarketData]) -> Optional[TradingSignal]:
        if len(market_data) < 50:  # Need enough data for indicators
            return None
        
        # Convert to DataFrame for technical analysis
        df = pd.DataFrame([
            {
                'timestamp': data.timestamp,
                'open': data.open_price,
                'high': data.high_price,
                'low': data.low_price,
                'close': data.close_price,
                'volume': data.volume
            }
            for data in market_data
        ])
        
        # Calculate technical indicators
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        df['macd'] = ta.trend.MACD(df['close']).macd()
        df['macd_signal'] = ta.trend.MACD(df['close']).macd_signal()
        df['bb_upper'] = ta.volatility.BollingerBands(df['close']).bollinger_hband()
        df['bb_lower'] = ta.volatility.BollingerBands(df['close']).bollinger_lband()
        df['sma_20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
        df['ema_12'] = ta.trend.EMAIndicator(df['close'], window=12).ema_indicator()
        df['ema_26'] = ta.trend.EMAIndicator(df['close'], window=26).ema_indicator()
        
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Generate signals based on multiple indicators
        buy_signals = 0
        sell_signals = 0
        signal_strength = 0
        
        # RSI signals
        if latest['rsi'] < 30:  # Oversold
            buy_signals += 1
            signal_strength += 0.3
        elif latest['rsi'] > 70:  # Overbought
            sell_signals += 1
            signal_strength += 0.3
        
        # MACD signals
        if latest['macd'] > latest['macd_signal'] and previous['macd'] <= previous['macd_signal']:
            buy_signals += 1
            signal_strength += 0.4
        elif latest['macd'] < latest['macd_signal'] and previous['macd'] >= previous['macd_signal']:
            sell_signals += 1
            signal_strength += 0.4
        
        # EMA crossover
        if latest['ema_12'] > latest['ema_26'] and previous['ema_12'] <= previous['ema_26']:
            buy_signals += 1
            signal_strength += 0.3
        elif latest['ema_12'] < latest['ema_26'] and previous['ema_12'] >= previous['ema_26']:
            sell_signals += 1
            signal_strength += 0.3
        
        # Bollinger Bands
        if latest['close'] < latest['bb_lower']:
            buy_signals += 1
            signal_strength += 0.2
        elif latest['close'] > latest['bb_upper']:
            sell_signals += 1
            signal_strength += 0.2
        
        # Determine final signal
        if buy_signals > sell_signals and signal_strength > 0.5:
            return TradingSignal(
                strategy_id=self.strategy_id,
                symbol=market_data[-1].symbol,
                signal_type=SignalType.BUY,
                strength=min(signal_strength, 1.0),
                confidence=min(buy_signals / 4.0, 1.0),
                price=latest['close'],
                metadata={
                    'strategy_type': 'momentum',
                    'rsi': latest['rsi'],
                    'macd': latest['macd'],
                    'buy_signals': buy_signals,
                    'sell_signals': sell_signals
                },
                timestamp=datetime.utcnow()
            )
        elif sell_signals > buy_signals and signal_strength > 0.5:
            return TradingSignal(
                strategy_id=self.strategy_id,
                symbol=market_data[-1].symbol,
                signal_type=SignalType.SELL,
                strength=min(signal_strength, 1.0),
                confidence=min(sell_signals / 4.0, 1.0),
                price=latest['close'],
                metadata={
                    'strategy_type': 'momentum',
                    'rsi': latest['rsi'],
                    'macd': latest['macd'],
                    'buy_signals': buy_signals,
                    'sell_signals': sell_signals
                },
                timestamp=datetime.utcnow()
            )
        
        return None

class MLBasedStrategy(BaseStrategy):
    """Machine Learning Based Strategy"""
    
    def __init__(self, strategy_id: int, config: Dict[str, Any]):
        super().__init__(strategy_id, config)
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.model_version = None
        
    async def load_model(self):
        """Load trained ML model from MLflow"""
        try:
            mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
            model_name = self.config.get('model_name', f'strategy_{self.strategy_id}_model')
            
            # Try to load latest model version
            try:
                model_version = mlflow.pyfunc.load_model(f"models:/{model_name}/latest")
                self.model = model_version
                self.model_version = "latest"
                logger.info(f"Loaded model {model_name} version latest")
            except:
                logger.warning(f"No model found for {model_name}, will train new model")
                await self.train_model()
                
        except Exception as e:
            logger.error(f"Error loading ML model: {e}")
    
    async def train_model(self):
        """Train ML model using historical data"""
        try:
            # Get historical data for training
            async with ts_pool.acquire() as conn:
                historical_data = await conn.fetch(
                    """
                    SELECT * FROM market_data 
                    WHERE symbol = $1 
                    AND time >= NOW() - INTERVAL '30 days'
                    ORDER BY time ASC
                    """,
                    self.config.get('symbol', 'BTCUSDT')
                )
            
            if len(historical_data) < 1000:
                logger.warning("Insufficient data for ML training")
                return
            
            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    'timestamp': row['time'],
                    'open': float(row['open_price']),
                    'high': float(row['high_price']),
                    'low': float(row['low_price']),
                    'close': float(row['close_price']),
                    'volume': float(row['volume'])
                }
                for row in historical_data
            ])
            
            # Feature engineering
            df = self.create_features(df)
            
            # Create target variable (1 for price increase, 0 for decrease)
            df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
            
            # Remove NaN values
            df = df.dropna()
            
            if len(df) < 100:
                logger.warning("Insufficient clean data for ML training")
                return
            
            # Prepare features and target
            feature_columns = [col for col in df.columns if col not in ['timestamp', 'target']]
            X = df[feature_columns]
            y = df['target']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            
            logger.info(f"Model trained - Accuracy: {accuracy:.3f}, Precision: {precision:.3f}, Recall: {recall:.3f}")
            
            # Save model to MLflow
            with mlflow.start_run():
                mlflow.log_param("strategy_id", self.strategy_id)
                mlflow.log_param("n_estimators", 100)
                mlflow.log_metric("accuracy", accuracy)
                mlflow.log_metric("precision", precision)
                mlflow.log_metric("recall", recall)
                
                mlflow.sklearn.log_model(
                    model, 
                    "model",
                    registered_model_name=f"strategy_{self.strategy_id}_model"
                )
            
            self.model = model
            self.feature_columns = feature_columns
            
        except Exception as e:
            logger.error(f"Error training ML model: {e}")
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create technical indicators as features"""
        # Price-based features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        df['price_change'] = df['close'] - df['open']
        df['high_low_ratio'] = df['high'] / df['low']
        df['volume_price_trend'] = df['volume'] * df['returns']
        
        # Moving averages
        for window in [5, 10, 20, 50]:
            df[f'sma_{window}'] = ta.trend.SMAIndicator(df['close'], window=window).sma_indicator()
            df[f'ema_{window}'] = ta.trend.EMAIndicator(df['close'], window=window).ema_indicator()
            df[f'price_sma_{window}_ratio'] = df['close'] / df[f'sma_{window}']
        
        # Technical indicators
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        df['macd'] = ta.trend.MACD(df['close']).macd()
        df['macd_signal'] = ta.trend.MACD(df['close']).macd_signal()
        df['macd_histogram'] = ta.trend.MACD(df['close']).macd_diff()
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(df['close'])
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['close']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Volatility
        df['volatility'] = df['returns'].rolling(window=20).std()
        df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Momentum indicators
        df['stoch_k'] = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close']).stoch()
        df['stoch_d'] = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close']).stoch_signal()
        df['williams_r'] = ta.momentum.WilliamsRIndicator(df['high'], df['low'], df['close']).williams_r()
        
        return df
    
    async def generate_signal(self, market_data: List[MarketData]) -> Optional[TradingSignal]:
        if not self.model or len(market_data) < 100:
            return None
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    'timestamp': data.timestamp,
                    'open': data.open_price,
                    'high': data.high_price,
                    'low': data.low_price,
                    'close': data.close_price,
                    'volume': data.volume
                }
                for data in market_data
            ])
            
            # Create features
            df = self.create_features(df)
            
            # Get latest features
            latest_features = df[self.feature_columns].iloc[-1:]
            
            # Handle missing values
            latest_features = latest_features.fillna(0)
            
            # Scale features
            features_scaled = self.scaler.transform(latest_features)
            
            # Make prediction
            prediction = self.model.predict(features_scaled)[0]
            prediction_proba = self.model.predict_proba(features_scaled)[0]
            
            # Get confidence (probability of predicted class)
            confidence = max(prediction_proba)
            
            # Only generate signal if confidence is high enough
            min_confidence = self.config.get('min_confidence', 0.6)
            if confidence < min_confidence:
                return None
            
            # Generate signal based on prediction
            if prediction == 1:  # Price expected to increase
                signal_type = SignalType.BUY
            else:  # Price expected to decrease
                signal_type = SignalType.SELL
            
            return TradingSignal(
                strategy_id=self.strategy_id,
                symbol=market_data[-1].symbol,
                signal_type=signal_type,
                strength=confidence,
                confidence=confidence,
                price=market_data[-1].close_price,
                metadata={
                    'strategy_type': 'ml_based',
                    'model_version': self.model_version,
                    'prediction': int(prediction),
                    'prediction_proba': prediction_proba.tolist(),
                    'features_used': len(self.feature_columns)
                },
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error generating ML signal: {e}")
            return None

class StrategyEngine:
    """Main strategy engine that manages all trading strategies"""
    
    def __init__(self):
        self.strategies: Dict[int, BaseStrategy] = {}
        self.running = False
        
    async def initialize(self):
        """Initialize strategy engine"""
        global db_pool, ts_pool, redis_client, kafka_consumer, kafka_producer
        
        try:
            # Initialize database connections
            db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
            ts_pool = await asyncpg.create_pool(TIMESCALE_URL, min_size=3, max_size=10)
            
            # Initialize Redis
            redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            
            # Initialize Kafka
            kafka_consumer = KafkaConsumer(
                'market-data',
                'strategy-config-updates',
                bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id='strategy-engine'
            )
            
            kafka_producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
            )
            
            # Initialize MLflow
            mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
            
            # Load active strategies
            await self.load_strategies()
            
            logger.info("Strategy engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize strategy engine: {e}")
            raise
    
    async def load_strategies(self):
        """Load active strategies from database"""
        try:
            async with db_pool.acquire() as conn:
                strategies = await conn.fetch(
                    "SELECT * FROM trading_strategies WHERE is_active = true"
                )
                
                for strategy_row in strategies:
                    strategy_id = strategy_row['id']
                    strategy_type = strategy_row['strategy_type']
                    config = json.loads(strategy_row['config'])
                    
                    # Create strategy instance based on type
                    if strategy_type == StrategyType.DCA.value:
                        strategy = DCAStrategy(strategy_id, config)
                    elif strategy_type == StrategyType.GRID.value:
                        strategy = GridStrategy(strategy_id, config)
                    elif strategy_type == StrategyType.MOMENTUM.value:
                        strategy = MomentumStrategy(strategy_id, config)
                    elif strategy_type == StrategyType.ML_BASED.value:
                        strategy = MLBasedStrategy(strategy_id, config)
                        await strategy.load_model()
                    else:
                        logger.warning(f"Unknown strategy type: {strategy_type}")
                        continue
                    
                    self.strategies[strategy_id] = strategy
                    logger.info(f"Loaded strategy {strategy_id} ({strategy_type})")
                
                logger.info(f"Loaded {len(self.strategies)} active strategies")
                
        except Exception as e:
            logger.error(f"Error loading strategies: {e}")
    
    async def get_market_data(self, symbol: str, limit: int = 100) -> List[MarketData]:
        """Get recent market data for a symbol"""
        try:
            async with ts_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM market_data 
                    WHERE symbol = $1 
                    ORDER BY time DESC 
                    LIMIT $2
                    """,
                    symbol, limit
                )
                
                market_data = []
                for row in reversed(rows):  # Reverse to get chronological order
                    market_data.append(MarketData(
                        symbol=row['symbol'],
                        timestamp=row['time'],
                        open_price=float(row['open_price']),
                        high_price=float(row['high_price']),
                        low_price=float(row['low_price']),
                        close_price=float(row['close_price']),
                        volume=float(row['volume']),
                        exchange=row['exchange']
                    ))
                
                return market_data
                
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return []
    
    async def process_strategy_signals(self):
        """Process signals from all active strategies"""
        try:
            # Get unique symbols from all strategies
            symbols = set()
            for strategy in self.strategies.values():
                symbol = strategy.config.get('symbol', 'BTCUSDT')
                symbols.add(symbol)
            
            # Process each symbol
            for symbol in symbols:
                market_data = await self.get_market_data(symbol)
                
                if not market_data:
                    continue
                
                # Generate signals from relevant strategies
                for strategy in self.strategies.values():
                    if strategy.config.get('symbol', 'BTCUSDT') == symbol:
                        try:
                            signal = await strategy.generate_signal(market_data)
                            
                            if signal and strategy.validate_signal(signal):
                                await self.publish_signal(signal)
                                await self.store_signal(signal)
                                
                        except Exception as e:
                            logger.error(f"Error generating signal for strategy {strategy.strategy_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error processing strategy signals: {e}")
    
    async def publish_signal(self, signal: TradingSignal):
        """Publish trading signal to Kafka"""
        try:
            signal_data = {
                'strategy_id': signal.strategy_id,
                'symbol': signal.symbol,
                'signal_type': signal.signal_type.value,
                'strength': signal.strength,
                'confidence': signal.confidence,
                'price': signal.price,
                'quantity': signal.quantity,
                'metadata': signal.metadata,
                'timestamp': signal.timestamp.isoformat() if signal.timestamp else datetime.utcnow().isoformat()
            }
            
            kafka_producer.send('strategy-signals', signal_data)
            logger.info(f"Published signal: {signal.signal_type.value} {signal.symbol} (strength: {signal.strength:.2f})")
            
        except Exception as e:
            logger.error(f"Error publishing signal: {e}")
    
    async def store_signal(self, signal: TradingSignal):
        """Store trading signal in TimescaleDB"""
        try:
            async with ts_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO trading_signals (time, strategy_id, symbol, signal_type, 
                                               strength, price, quantity, confidence, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    signal.timestamp or datetime.utcnow(),
                    signal.strategy_id,
                    signal.symbol,
                    signal.signal_type.value,
                    signal.strength,
                    signal.price,
                    signal.quantity,
                    signal.confidence,
                    json.dumps(signal.metadata) if signal.metadata else None
                )
                
        except Exception as e:
            logger.error(f"Error storing signal: {e}")
    
    async def run(self):
        """Main strategy engine loop"""
        self.running = True
        logger.info("Strategy engine started")
        
        while self.running:
            try:
                # Process strategy signals
                await self.process_strategy_signals()
                
                # Wait before next iteration
                await asyncio.sleep(60)  # Run every minute
                
            except Exception as e:
                logger.error(f"Error in strategy engine loop: {e}")
                await asyncio.sleep(10)  # Wait before retrying
    
    async def stop(self):
        """Stop strategy engine"""
        self.running = False
        logger.info("Strategy engine stopped")

async def main():
    """Main function"""
    engine = StrategyEngine()
    
    try:
        await engine.initialize()
        await engine.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await engine.stop()
        
        # Cleanup connections
        if db_pool:
            await db_pool.close()
        if ts_pool:
            await ts_pool.close()
        if redis_client:
            await redis_client.close()
        if kafka_producer:
            kafka_producer.close()

if __name__ == "__main__":
    asyncio.run(main())