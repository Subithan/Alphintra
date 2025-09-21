"""
Basic tests for the inference service.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from app.models.strategies import StrategyPackage, StrategyFile, StrategySource
from app.models.signals import TradingSignal, SignalAction, ExecutionParams
from app.models.market_data import OHLCV, DataProvider, Timeframe, MarketDataStatus
from app.services.strategy_loader import StrategyLoader
from app.services.inference_engine import InferenceEngine
from app.services.signal_distributor import SignalDistributor
from app.utils.sandbox import StrategySandbox


class TestStrategyLoader:
    """Test strategy loading functionality."""

    @pytest.fixture
    def mock_strategy_loader(self):
        return StrategyLoader("mock://ai_ml_db", "mock://no_code_db")

    def test_strategy_package_creation(self):
        """Test creating a strategy package."""
        strategy_package = StrategyPackage(
            strategy_id="test-123",
            source=StrategySource.AI_ML,
            name="Test Strategy",
            description="A test strategy",
            files={
                "main.py": StrategyFile(
                    filename="main.py",
                    content="def generate_signal(data): return {'action': 'HOLD', 'confidence': 0.5}",
                    file_type="python"
                )
            },
            requirements=["pandas", "numpy"]
        )
        
        assert strategy_package.strategy_id == "test-123"
        assert strategy_package.source == StrategySource.AI_ML
        assert "main.py" in strategy_package.files
        assert strategy_package.get_main_content().startswith("def generate_signal")


class TestSignalDistributor:
    """Test signal distribution functionality."""

    def test_signal_creation(self):
        """Test creating a trading signal."""
        signal = TradingSignal(
            strategy_id="test-strategy",
            strategy_source="ai_ml",
            symbol="BTCUSDT",
            action=SignalAction.BUY,
            confidence=0.85,
            execution_params=ExecutionParams(
                quantity=0.1,
                price_target=45000.0
            ),
            current_price=44950.0
        )
        
        assert signal.strategy_id == "test-strategy"
        assert signal.action == SignalAction.BUY
        assert signal.confidence == 0.85
        assert signal.execution_params.quantity == 0.1


class TestMarketData:
    """Test market data models."""

    def test_ohlcv_validation(self):
        """Test OHLCV data validation."""
        ohlcv = OHLCV(
            symbol="BTCUSDT",
            timestamp=datetime.utcnow(),
            timeframe=Timeframe.T1h,
            open_price=45000.0,
            high_price=45500.0,
            low_price=44800.0,
            close_price=45200.0,
            volume=1000.0,
            provider=DataProvider.BINANCE,
            status=MarketDataStatus.LIVE
        )
        
        assert ohlcv.symbol == "BTCUSDT"
        assert ohlcv.high_price >= ohlcv.low_price
        assert ohlcv.low_price <= ohlcv.close_price <= ohlcv.high_price

    def test_invalid_ohlcv_validation(self):
        """Test OHLCV validation with invalid data."""
        with pytest.raises(ValueError):
            OHLCV(
                symbol="BTCUSDT",
                timestamp=datetime.utcnow(),
                timeframe=Timeframe.T1h,
                open_price=45000.0,
                high_price=44000.0,  # High < Low (invalid)
                low_price=44800.0,
                close_price=45200.0,
                volume=1000.0,
                provider=DataProvider.BINANCE,
                status=MarketDataStatus.LIVE
            )


class TestStrategySandbox:
    """Test strategy sandbox functionality."""

    def test_sandbox_initialization(self):
        """Test sandbox initialization."""
        strategy_package = StrategyPackage(
            strategy_id="test-sandbox",
            source=StrategySource.AI_ML,
            name="Test Strategy",
            files={
                "main.py": StrategyFile(
                    filename="main.py",
                    content="def generate_signal(data): return {'action': 'HOLD', 'confidence': 0.5}",
                    file_type="python"
                )
            }
        )
        
        sandbox = StrategySandbox(strategy_package)
        assert sandbox.strategy_package.strategy_id == "test-sandbox"
        assert sandbox.temp_dir is None  # Not initialized yet

    def test_convert_dict_to_signal(self):
        """Test converting dictionary to TradingSignal."""
        strategy_package = StrategyPackage(
            strategy_id="test-conversion",
            source=StrategySource.AI_ML,
            name="Test Strategy",
            files={
                "main.py": StrategyFile(
                    filename="main.py",
                    content="pass",
                    file_type="python"
                )
            }
        )
        
        sandbox = StrategySandbox(strategy_package)
        
        signal_dict = {
            "symbol": "ETHUSDT",
            "action": "BUY",
            "confidence": 0.8,
            "quantity": 0.5,
            "price_target": 3000.0
        }
        
        signal = sandbox._dict_to_signal(signal_dict)
        
        assert signal.symbol == "ETHUSDT"
        assert signal.action == SignalAction.BUY
        assert signal.confidence == 0.8
        assert signal.execution_params.quantity == 0.5


@pytest.mark.asyncio
class TestAsyncComponents:
    """Test async components of the service."""

    async def test_mock_strategy_execution(self):
        """Test mock strategy execution."""
        # This would be expanded with actual async tests
        # For now, just test that async functions can be called
        
        # Mock market data
        market_data = {
            "BTCUSDT": [
                OHLCV(
                    symbol="BTCUSDT",
                    timestamp=datetime.utcnow(),
                    timeframe=Timeframe.T1h,
                    open_price=45000.0,
                    high_price=45500.0,
                    low_price=44800.0,
                    close_price=45200.0,
                    volume=1000.0,
                    provider=DataProvider.BINANCE,
                    status=MarketDataStatus.LIVE
                )
            ]
        }
        
        # Simple assertion for async test structure
        assert len(market_data["BTCUSDT"]) == 1
        assert market_data["BTCUSDT"][0].symbol == "BTCUSDT"


def test_service_configuration():
    """Test service configuration constants."""
    from app.models.strategies import StrategySource, StrategyStatus
    from app.models.signals import SignalAction, SignalStatus
    
    # Test enum values
    assert StrategySource.AI_ML == "ai_ml"
    assert StrategySource.NO_CODE == "no_code"
    
    assert SignalAction.BUY == "BUY"
    assert SignalAction.SELL == "SELL"
    assert SignalAction.HOLD == "HOLD"
    
    assert SignalStatus.PENDING == "pending"
    assert SignalStatus.ACTIVE == "active"


# Integration test example
@pytest.mark.integration
async def test_full_signal_flow():
    """Integration test for complete signal generation flow."""
    # This would test the full flow from strategy loading to signal distribution
    # Skipped for basic implementation
    pytest.skip("Integration test requires full service setup")


if __name__ == "__main__":
    pytest.main([__file__])