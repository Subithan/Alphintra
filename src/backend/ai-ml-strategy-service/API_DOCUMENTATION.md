# AI/ML Strategy Service - Comprehensive API Documentation

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
   - [Strategy Development](#strategy-development)
   - [Dataset Management](#dataset-management)
   - [Model Training](#model-training)
   - [Backtesting](#backtesting)
   - [Paper Trading](#paper-trading)
   - [Live Execution](#live-execution)
   - [Model Registry](#model-registry)
   - [AI Code Assistant](#ai-code-assistant)
4. [SDK Components](#sdk-components)
5. [Data Models](#data-models)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Examples](#examples)

## Overview

The AI/ML Strategy Service provides a comprehensive RESTful API for developing, training, testing, and deploying algorithmic trading strategies. Built with FastAPI, it offers automatic API documentation, request/response validation, and high-performance async operations.

**Base URL**: `http://localhost:8002/api` (development)
**OpenAPI Docs**: `http://localhost:8002/docs`
**ReDoc**: `http://localhost:8002/redoc`

### Service Architecture

- **Framework**: FastAPI with Python 3.11+
- **Database**: PostgreSQL + TimescaleDB
- **Caching**: Redis
- **ML Frameworks**: TensorFlow, PyTorch, Scikit-learn
- **Training Platform**: Google Vertex AI
- **Message Queue**: Apache Kafka
- **Storage**: Google Cloud Storage

## Authentication

All API endpoints require authentication using JWT tokens. Include the token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

### Authentication Flow

1. Obtain JWT token from the auth service
2. Include token in all API requests
3. Refresh token before expiration (30 minutes default)

## API Endpoints

### Strategy Development

Endpoints for creating, managing, and executing trading strategies.

#### Create Strategy

```http
POST /api/strategies
```

Creates a new trading strategy with Python code.

**Request Body:**
```json
{
  "name": "RSI Mean Reversion",
  "description": "Strategy using RSI indicator for mean reversion trades",
  "code": "from alphintra import BaseStrategy\n\nclass RSIStrategy(BaseStrategy):\n    def on_bar(self, context):\n        # Strategy implementation\n        pass",
  "parameters": {
    "rsi_period": 14,
    "oversold_threshold": 30,
    "overbought_threshold": 70
  },
  "tags": ["rsi", "mean-reversion", "technical"]
}
```

**Response:**
```json
{
  "success": true,
  "strategy_id": "550e8400-e29b-41d4-a716-446655440000",
  "validation_warnings": []
}
```

**Example:**
```python
import requests

url = "http://localhost:8002/api/strategies"
headers = {
    "Authorization": "Bearer your-jwt-token",
    "Content-Type": "application/json"
}

data = {
    "name": "Simple Moving Average Crossover",
    "description": "Classic SMA crossover strategy",
    "code": '''
from alphintra import BaseStrategy

class SMAStrategy(BaseStrategy):
    def initialize(self, context):
        context.set_variable("position", 0)
    
    def on_bar(self, context):
        # Get market data
        data = context.market_data.get_bars("BTCUSDT", 50)
        
        # Calculate moving averages
        short_ma = data.close.rolling(10).mean().iloc[-1]
        long_ma = data.close.rolling(30).mean().iloc[-1]
        
        current_price = data.close.iloc[-1]
        position = context.get_variable("position")
        
        # Generate signals
        if short_ma > long_ma and position <= 0:
            context.order_manager.market_order("BTCUSDT", 1.0)
            context.set_variable("position", 1)
            context.log("Buy signal generated")
            
        elif short_ma < long_ma and position >= 0:
            context.order_manager.market_order("BTCUSDT", -1.0)
            context.set_variable("position", -1)
            context.log("Sell signal generated")
    ''',
    "parameters": {
        "short_period": 10,
        "long_period": 30,
        "position_size": 1.0
    },
    "tags": ["sma", "crossover", "trend-following"]
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

#### Get Strategy

```http
GET /api/strategies/{strategy_id}
```

Retrieves a strategy by ID.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "RSI Mean Reversion",
  "description": "Strategy using RSI indicator for mean reversion trades",
  "code": "...",
  "status": "draft",
  "parameters": {...},
  "tags": ["rsi", "mean-reversion"],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "performance_metrics": {
    "total_return": null,
    "max_drawdown": null,
    "sharpe_ratio": null
  }
}
```

#### Update Strategy

```http
PUT /api/strategies/{strategy_id}
```

Updates an existing strategy.

**Request Body:**
```json
{
  "name": "Updated Strategy Name",
  "code": "# Updated strategy code",
  "parameters": {
    "updated_param": "value"
  }
}
```

#### List Strategies

```http
GET /api/strategies
```

Lists all strategies for the authenticated user.

**Query Parameters:**
- `status`: Filter by status (`draft`, `active`, `archived`)
- `tag`: Filter by tag
- `search`: Search in name and description
- `limit`: Number of results (default: 50)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
{
  "strategies": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "RSI Strategy",
      "status": "active",
      "tags": ["rsi"],
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### Execute Strategy

```http
POST /api/strategies/{strategy_id}/execute
```

Executes a strategy against historical data for testing.

**Request Body:**
```json
{
  "dataset_id": "dataset-uuid",
  "parameters": {
    "rsi_period": 14
  },
  "initial_capital": 100000.0
}
```

**Response:**
```json
{
  "execution_id": "exec-uuid",
  "status": "running",
  "progress": 0,
  "estimated_completion": "2024-01-15T11:00:00Z"
}
```

#### Validate Strategy Code

```http
POST /api/strategies/validate
```

Validates strategy code without saving.

**Request Body:**
```json
{
  "code": "from alphintra import BaseStrategy\n\nclass TestStrategy(BaseStrategy):\n    pass"
}
```

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Strategy does not implement on_bar method"
  ],
  "suggestions": [
    "Consider adding proper error handling",
    "Add parameter validation"
  ]
}
```

#### Debug Strategy

```http
POST /api/strategies/{strategy_id}/debug
```

Creates a debugging session for interactive strategy development.

**Request Body:**
```json
{
  "dataset_id": "dataset-uuid",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}
```

### Dataset Management

Endpoints for managing market data and custom datasets.

#### List Datasets

```http
GET /api/datasets
```

Lists available datasets with filtering options.

**Query Parameters:**
- `asset_class`: Filter by asset class (`crypto`, `stocks`, `forex`, `commodities`)
- `source`: Filter by data source
- `frequency`: Filter by frequency (`1m`, `5m`, `1h`, `1d`)
- `symbols`: Filter by symbols (comma-separated)
- `search`: Search in name and description
- `is_public`: Filter public/private datasets
- `limit`: Number of results (default: 50)
- `offset`: Pagination offset

**Response:**
```json
{
  "datasets": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Crypto OHLCV Data",
      "description": "1-minute OHLCV data for major cryptocurrencies",
      "asset_class": "crypto",
      "source": "binance",
      "frequency": "1m",
      "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT"],
      "start_date": "2023-01-01",
      "end_date": "2024-01-15",
      "size_mb": 245.7,
      "record_count": 1500000,
      "is_public": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### Get Dataset

```http
GET /api/datasets/{dataset_id}
```

Retrieves detailed dataset information.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Crypto OHLCV Data",
  "description": "1-minute OHLCV data for major cryptocurrencies",
  "asset_class": "crypto",
  "source": "binance",
  "frequency": "1m",
  "symbols": ["BTCUSDT", "ETHUSDT"],
  "columns": ["timestamp", "open", "high", "low", "close", "volume"],
  "start_date": "2023-01-01",
  "end_date": "2024-01-15",
  "size_mb": 245.7,
  "record_count": 1500000,
  "quality_score": 0.98,
  "metadata": {
    "exchange": "binance",
    "timezone": "UTC",
    "data_quality_checks": ["completeness", "consistency", "outliers"]
  },
  "preview_data": [
    {
      "timestamp": "2024-01-15T10:00:00Z",
      "symbol": "BTCUSDT",
      "open": 42500.0,
      "high": 42750.0,
      "low": 42400.0,
      "close": 42650.0,
      "volume": 125.45
    }
  ]
}
```

#### Upload Dataset

```http
POST /api/datasets/upload
```

Uploads a custom dataset file.

**Request:**
- Content-Type: `multipart/form-data`
- File: CSV or Parquet file
- Metadata: JSON string with dataset information

**Form Data:**
```
file: [binary file data]
metadata: {
  "name": "My Custom Dataset",
  "description": "Custom trading data",
  "asset_class": "stocks",
  "symbols": ["AAPL", "GOOGL"],
  "frequency": "1d",
  "tags": ["custom", "stocks"]
}
```

**Response:**
```json
{
  "dataset_id": "new-dataset-uuid",
  "upload_status": "processing",
  "validation_job_id": "validation-job-uuid",
  "estimated_processing_time": "5 minutes"
}
```

#### Validate Dataset

```http
POST /api/datasets/{dataset_id}/validate
```

Validates dataset quality and structure.

**Response:**
```json
{
  "validation_id": "validation-uuid",
  "status": "completed",
  "quality_score": 0.95,
  "issues": [
    {
      "type": "missing_data",
      "severity": "warning",
      "description": "Missing data points: 0.5% of records",
      "affected_columns": ["volume"],
      "suggestion": "Consider interpolation or removal of affected records"
    }
  ],
  "statistics": {
    "total_records": 150000,
    "date_range": {
      "start": "2023-01-01",
      "end": "2024-01-15"
    },
    "completeness": 0.995,
    "consistency_score": 0.98
  }
}
```

### Model Training

Endpoints for training machine learning models on strategies and market data.

#### Create Training Job

```http
POST /api/training/jobs
```

Creates a new model training job.

**Request Body:**
```json
{
  "strategy_id": "strategy-uuid",
  "dataset_id": "dataset-uuid",
  "job_name": "LSTM Price Prediction",
  "job_type": "training",
  "instance_type": "GPU_MEDIUM",
  "disk_size": 100,
  "timeout_hours": 12,
  "priority": "normal",
  "hyperparameters": {
    "learning_rate": 0.001,
    "batch_size": 32,
    "epochs": 100,
    "hidden_units": 128
  },
  "training_config": {
    "model_type": "lstm",
    "sequence_length": 60,
    "prediction_horizon": 1,
    "features": ["open", "high", "low", "close", "volume"],
    "target": "close"
  }
}
```

**Response:**
```json
{
  "job_id": "training-job-uuid",
  "status": "queued",
  "estimated_start_time": "2024-01-15T11:00:00Z",
  "estimated_duration": "2 hours",
  "resource_allocation": {
    "instance_type": "GPU_MEDIUM",
    "cpu_cores": 4,
    "memory_gb": 16,
    "gpu_count": 1,
    "disk_gb": 100
  },
  "cost_estimate": {
    "currency": "USD",
    "estimated_cost": 12.50
  }
}
```

#### Get Training Job Status

```http
GET /api/training/jobs/{job_id}
```

Retrieves training job status and progress.

**Response:**
```json
{
  "job_id": "training-job-uuid",
  "job_name": "LSTM Price Prediction",
  "status": "running",
  "progress": 0.65,
  "current_epoch": 65,
  "total_epochs": 100,
  "metrics": {
    "train_loss": 0.0245,
    "val_loss": 0.0289,
    "train_accuracy": 0.847,
    "val_accuracy": 0.823
  },
  "resource_usage": {
    "cpu_percent": 75,
    "memory_percent": 68,
    "gpu_percent": 92
  },
  "estimated_completion": "2024-01-15T13:30:00Z",
  "logs_url": "/api/training/jobs/training-job-uuid/logs"
}
```

#### Hyperparameter Tuning

```http
POST /api/training/hyperparameter-tune
```

Starts hyperparameter optimization for a strategy.

**Request Body:**
```json
{
  "strategy_id": "strategy-uuid",
  "dataset_id": "dataset-uuid",
  "job_name": "RSI Optimization",
  "parameter_space": {
    "rsi_period": {
      "type": "int",
      "min": 10,
      "max": 30,
      "step": 2
    },
    "oversold_threshold": {
      "type": "float",
      "min": 20.0,
      "max": 35.0,
      "step": 2.5
    },
    "overbought_threshold": {
      "type": "float",
      "min": 65.0,
      "max": 80.0,
      "step": 2.5
    }
  },
  "optimization_algorithm": "random_search",
  "optimization_objective": "maximize",
  "objective_metric": "sharpe_ratio",
  "max_trials": 100,
  "max_duration_hours": 6
}
```

**Response:**
```json
{
  "tuning_job_id": "tuning-job-uuid",
  "status": "running",
  "total_trials": 100,
  "completed_trials": 0,
  "best_trial": null,
  "estimated_completion": "2024-01-15T17:00:00Z"
}
```

### Backtesting

Endpoints for testing strategies against historical data.

#### Create Backtest

```http
POST /api/backtesting/jobs
```

Creates a comprehensive backtest job.

**Request Body:**
```json
{
  "strategy_id": "strategy-uuid",
  "dataset_id": "dataset-uuid",
  "name": "RSI Strategy Backtest",
  "description": "Testing RSI mean reversion on crypto data",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "initial_capital": 100000.0,
  "commission_rate": 0.001,
  "slippage_rate": 0.0005,
  "methodology": "standard",
  "position_sizing": "fixed_percentage",
  "position_sizing_config": {
    "percentage": 0.1
  },
  "max_position_size": 0.2,
  "max_portfolio_risk": 0.02,
  "stop_loss_pct": 0.05,
  "take_profit_pct": 0.1,
  "benchmark_symbol": "BTCUSDT"
}
```

**Response:**
```json
{
  "backtest_id": "backtest-uuid",
  "status": "queued",
  "estimated_start_time": "2024-01-15T11:00:00Z",
  "estimated_duration": "15 minutes",
  "progress": 0
}
```

#### Get Backtest Results

```http
GET /api/backtesting/jobs/{backtest_id}/results
```

Retrieves detailed backtest results and performance metrics.

**Response:**
```json
{
  "backtest_id": "backtest-uuid",
  "status": "completed",
  "performance_metrics": {
    "total_return": 0.234,
    "total_return_pct": 23.4,
    "annualized_return": 0.187,
    "max_drawdown": 0.089,
    "max_drawdown_pct": 8.9,
    "sharpe_ratio": 1.45,
    "sortino_ratio": 1.89,
    "calmar_ratio": 2.10,
    "win_rate": 0.58,
    "profit_factor": 1.34,
    "avg_win": 245.67,
    "avg_loss": -156.23,
    "largest_win": 1245.67,
    "largest_loss": -892.34,
    "total_trades": 156,
    "winning_trades": 90,
    "losing_trades": 66
  },
  "benchmark_comparison": {
    "benchmark_return": 0.156,
    "alpha": 0.078,
    "beta": 0.67,
    "correlation": 0.45,
    "tracking_error": 0.12,
    "information_ratio": 0.65
  },
  "trades": [
    {
      "trade_id": 1,
      "symbol": "BTCUSDT",
      "side": "buy",
      "quantity": 0.5,
      "entry_price": 42500.0,
      "exit_price": 43200.0,
      "entry_time": "2023-01-15T10:30:00Z",
      "exit_time": "2023-01-15T14:20:00Z",
      "pnl": 350.0,
      "pnl_pct": 0.0165,
      "commission": 42.85,
      "slippage": 12.75,
      "duration_hours": 3.83
    }
  ],
  "equity_curve": [
    {
      "date": "2023-01-01",
      "equity": 100000.0,
      "cash": 100000.0,
      "positions_value": 0.0,
      "drawdown": 0.0
    }
  ],
  "monthly_returns": {
    "2023-01": 0.045,
    "2023-02": -0.012,
    "2023-03": 0.067
  }
}
```

#### Compare Backtests

```http
POST /api/backtesting/compare
```

Compares multiple backtest results.

**Request Body:**
```json
{
  "backtest_ids": ["backtest-1", "backtest-2", "backtest-3"],
  "metrics": ["total_return", "sharpe_ratio", "max_drawdown"]
}
```

**Response:**
```json
{
  "comparison_id": "comparison-uuid",
  "backtests": [
    {
      "backtest_id": "backtest-1",
      "name": "RSI Strategy",
      "total_return": 0.234,
      "sharpe_ratio": 1.45,
      "max_drawdown": 0.089
    }
  ],
  "best_performer": {
    "metric": "sharpe_ratio",
    "backtest_id": "backtest-1",
    "value": 1.45
  },
  "correlation_matrix": {
    "backtest-1": {
      "backtest-2": 0.67,
      "backtest-3": 0.45
    }
  }
}
```

### Paper Trading

Endpoints for virtual trading with real-time market data.

#### Create Paper Trading Session

```http
POST /api/paper-trading/sessions
```

Creates a new paper trading session.

**Request Body:**
```json
{
  "strategy_id": 123,
  "name": "RSI Strategy Paper Trading",
  "description": "Testing RSI strategy with virtual funds",
  "initial_capital": 100000.00,
  "commission_rate": 0.001,
  "slippage_rate": 0.0001
}
```

**Response:**
```json
{
  "session_id": 456,
  "strategy_id": 123,
  "name": "RSI Strategy Paper Trading",
  "is_active": true,
  "initial_capital": 100000.0,
  "current_capital": 100000.0,
  "cash_balance": 100000.0,
  "total_return": 0.0,
  "created_at": "2024-01-15T11:00:00Z"
}
```

#### Submit Order

```http
POST /api/paper-trading/sessions/{session_id}/orders
```

Submits a trading order in the paper trading session.

**Request Body:**
```json
{
  "symbol": "BTCUSDT",
  "side": "buy",
  "order_type": "limit",
  "quantity": 0.5,
  "price": 42500.0,
  "time_in_force": "GTC",
  "client_order_id": "my-order-123"
}
```

**Response:**
```json
{
  "order_id": "order-uuid",
  "client_order_id": "my-order-123",
  "symbol": "BTCUSDT",
  "side": "buy",
  "order_type": "limit",
  "quantity": 0.5,
  "price": 42500.0,
  "status": "pending",
  "created_at": "2024-01-15T11:30:00Z"
}
```

#### Get Portfolio

```http
GET /api/paper-trading/sessions/{session_id}/portfolio
```

Retrieves current portfolio status.

**Response:**
```json
{
  "session_id": 456,
  "total_value": 102345.67,
  "cash_balance": 85432.10,
  "positions_value": 16913.57,
  "total_pnl": 2345.67,
  "total_pnl_pct": 0.0235,
  "day_pnl": 234.56,
  "day_pnl_pct": 0.0023,
  "realized_pnl": 1234.56,
  "unrealized_pnl": 1111.11,
  "num_positions": 3,
  "positions": [
    {
      "symbol": "BTCUSDT",
      "quantity": 0.5,
      "avg_price": 42500.0,
      "current_price": 43200.0,
      "market_value": 21600.0,
      "unrealized_pnl": 350.0,
      "unrealized_pnl_pct": 0.0165
    }
  ]
}
```

### Live Execution

Endpoints for deploying strategies to live trading environments.

#### Deploy Strategy

```http
POST /api/live-execution/deploy
```

Deploys a strategy to live trading.

**Request Body:**
```json
{
  "strategy_id": "strategy-uuid",
  "deployment_name": "RSI Live Trading",
  "environment": "staging",
  "resource_allocation": {
    "cpu_cores": 2,
    "memory_gb": 4,
    "max_positions": 10
  },
  "risk_limits": {
    "max_daily_loss": 1000.0,
    "max_position_size": 0.1,
    "max_portfolio_risk": 0.02
  },
  "execution_config": {
    "order_type": "limit",
    "price_improvement_attempts": 3,
    "max_slippage_pct": 0.001
  }
}
```

**Response:**
```json
{
  "deployment_id": "deployment-uuid",
  "status": "deploying",
  "estimated_ready_time": "2024-01-15T11:45:00Z",
  "resource_allocation": {
    "instance_id": "live-exec-123",
    "cpu_cores": 2,
    "memory_gb": 4
  }
}
```

#### Get Deployment Status

```http
GET /api/live-execution/deployments/{deployment_id}
```

Retrieves live deployment status and metrics.

**Response:**
```json
{
  "deployment_id": "deployment-uuid",
  "strategy_id": "strategy-uuid",
  "status": "running",
  "uptime": "2 hours 15 minutes",
  "performance": {
    "total_pnl": 234.56,
    "total_pnl_pct": 0.0023,
    "trades_today": 5,
    "success_rate": 0.8
  },
  "resource_usage": {
    "cpu_percent": 15,
    "memory_percent": 32,
    "network_io": "low"
  },
  "health_checks": {
    "strategy_health": "healthy",
    "market_data_connection": "healthy",
    "broker_connection": "healthy",
    "last_heartbeat": "2024-01-15T13:30:00Z"
  }
}
```

### Model Registry

Endpoints for managing trained models and their lifecycle.

#### Register Model

```http
POST /api/model-registry/models
```

Registers a trained model in the model registry.

**Request Body:**
```json
{
  "name": "LSTM Price Predictor v1.2",
  "description": "LSTM model for 1-hour price prediction",
  "model_type": "lstm",
  "framework": "tensorflow",
  "version": "1.2.0",
  "training_job_id": "training-job-uuid",
  "model_artifacts": {
    "model_file": "gs://bucket/models/lstm_v1.2.h5",
    "config_file": "gs://bucket/models/lstm_v1.2_config.json",
    "preprocessing_pipeline": "gs://bucket/models/preprocessing_v1.2.pkl"
  },
  "performance_metrics": {
    "mse": 0.0245,
    "mae": 0.1234,
    "r2_score": 0.8567
  },
  "tags": ["lstm", "price-prediction", "1h-timeframe"]
}
```

**Response:**
```json
{
  "model_id": "model-uuid",
  "name": "LSTM Price Predictor v1.2",
  "version": "1.2.0",
  "status": "registered",
  "registry_url": "/api/model-registry/models/model-uuid",
  "created_at": "2024-01-15T14:00:00Z"
}
```

#### Get Model

```http
GET /api/model-registry/models/{model_id}
```

Retrieves model details and metadata.

**Response:**
```json
{
  "model_id": "model-uuid",
  "name": "LSTM Price Predictor v1.2",
  "description": "LSTM model for 1-hour price prediction",
  "version": "1.2.0",
  "status": "active",
  "model_type": "lstm",
  "framework": "tensorflow",
  "performance_metrics": {
    "mse": 0.0245,
    "mae": 0.1234,
    "r2_score": 0.8567
  },
  "model_artifacts": {
    "model_file": "gs://bucket/models/lstm_v1.2.h5",
    "config_file": "gs://bucket/models/lstm_v1.2_config.json"
  },
  "deployment_history": [
    {
      "deployment_id": "deploy-1",
      "environment": "staging",
      "deployed_at": "2024-01-15T14:30:00Z",
      "status": "active"
    }
  ],
  "created_at": "2024-01-15T14:00:00Z",
  "updated_at": "2024-01-15T14:00:00Z"
}
```

### AI Code Assistant

Endpoints for AI-powered code assistance and generation.

#### Generate Strategy Code

```http
POST /api/ai-code/generate-strategy
```

Generates strategy code based on natural language description.

**Request Body:**
```json
{
  "description": "Create a mean reversion strategy using RSI indicator with 14-period lookback. Buy when RSI is below 30 and sell when above 70.",
  "style": "professional",
  "include_comments": true,
  "target_symbols": ["BTCUSDT", "ETHUSDT"]
}
```

**Response:**
```json
{
  "generated_code": "from alphintra import BaseStrategy\nfrom alphintra.indicators import RSI\n\nclass RSIMeanReversionStrategy(BaseStrategy):\n    \"\"\"RSI Mean Reversion Strategy\"\"\"\n    \n    def initialize(self, context):\n        # Initialize RSI indicator with 14-period\n        self.rsi = RSI(period=14)\n        context.set_variable('position', 0)\n    \n    def on_bar(self, context):\n        # Calculate RSI for current symbol\n        current_rsi = self.rsi.calculate(context.market_data.get_bars())\n        \n        if current_rsi < 30 and context.get_variable('position') <= 0:\n            # Buy signal - RSI oversold\n            context.order_manager.market_order(context.symbol, 1.0)\n            context.set_variable('position', 1)\n            context.log(f'Buy signal: RSI={current_rsi:.2f}')\n            \n        elif current_rsi > 70 and context.get_variable('position') >= 0:\n            # Sell signal - RSI overbought  \n            context.order_manager.market_order(context.symbol, -1.0)\n            context.set_variable('position', -1)\n            context.log(f'Sell signal: RSI={current_rsi:.2f}')",
  "explanation": "This strategy implements RSI mean reversion logic with the following features:\n- Uses 14-period RSI indicator\n- Generates buy signals when RSI < 30 (oversold)\n- Generates sell signals when RSI > 70 (overbought)\n- Maintains position state to avoid duplicate signals\n- Includes logging for trade decisions",
  "suggested_parameters": {
    "rsi_period": 14,
    "oversold_threshold": 30,
    "overbought_threshold": 70,
    "position_size": 1.0
  },
  "confidence_score": 0.92
}
```

#### Code Completion

```http
POST /api/ai-code/complete
```

Provides intelligent code completion suggestions.

**Request Body:**
```json
{
  "code": "from alphintra import BaseStrategy\n\nclass MyStrategy(BaseStrategy):\n    def on_bar(self, context):\n        data = context.market_data.get_bars()\n        sma_20 = data.close.rolling(",
  "line": 5,
  "column": 35
}
```

**Response:**
```json
{
  "completions": [
    {
      "text": "20).mean()",
      "description": "Calculate 20-period simple moving average",
      "type": "method_completion"
    },
    {
      "text": "window=20).mean()",
      "description": "Calculate rolling mean with explicit window parameter",
      "type": "method_completion"
    }
  ]
}
```

## SDK Components

The Alphintra Python SDK provides a comprehensive framework for strategy development.

### BaseStrategy Class

The foundation class for all trading strategies.

```python
from alphintra import BaseStrategy

class MyStrategy(BaseStrategy):
    def initialize(self, context):
        """Called once at strategy startup."""
        pass
    
    def on_bar(self, context):
        """Called for each new data bar."""
        pass
    
    def on_order_fill(self, context, order):
        """Called when an order is filled."""
        pass
    
    def on_error(self, context, error):
        """Called when an error occurs."""
        pass
```

**Key Methods:**

- `initialize(context)`: Setup strategy state and indicators
- `on_bar(context)`: Process new market data and generate signals
- `on_order_fill(context, order)`: Handle order execution events
- `on_error(context, error)`: Handle runtime errors

### StrategyContext Class

Provides access to market data, portfolio, and trading functions.

```python
class StrategyContext:
    # Market data access
    market_data: MarketData
    
    # Portfolio management
    portfolio: Portfolio
    
    # Order management
    order_manager: OrderManager
    
    # Risk management
    risk_manager: RiskManager
    
    # Strategy parameters
    parameters: Dict[str, Any]
    
    # State management
    def set_variable(name: str, value: Any)
    def get_variable(name: str, default: Any = None) -> Any
    
    # Logging
    def log(message: str, level: str = "INFO", **kwargs)
    
    # Metrics
    def record_metric(name: str, value: Any)
```

### MarketData Class

Provides access to market data and technical indicators.

```python
class MarketData:
    def get_bars(self, symbol: str = None, count: int = 100) -> pd.DataFrame:
        """Get OHLCV bars for analysis."""
        pass
    
    def get_current_price(self, symbol: str) -> float:
        """Get current market price."""
        pass
    
    def get_bid_ask(self, symbol: str) -> Tuple[float, float]:
        """Get current bid/ask prices."""
        pass
    
    def is_market_open(self, symbol: str = None) -> bool:
        """Check if market is currently open."""
        pass
```

### Portfolio Class

Manages portfolio positions and performance tracking.

```python
class Portfolio:
    @property
    def total_value(self) -> float:
        """Total portfolio value."""
        pass
    
    @property
    def cash_balance(self) -> float:
        """Available cash balance."""
        pass
    
    @property
    def positions(self) -> Dict[str, Position]:
        """Current positions by symbol."""
        pass
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol."""
        pass
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get portfolio performance metrics."""
        pass
```

### OrderManager Class

Handles order submission and management.

```python
class OrderManager:
    def market_order(self, symbol: str, quantity: float, 
                    client_id: str = None) -> str:
        """Submit market order."""
        pass
    
    def limit_order(self, symbol: str, quantity: float, price: float,
                   client_id: str = None) -> str:
        """Submit limit order."""
        pass
    
    def stop_order(self, symbol: str, quantity: float, stop_price: float,
                  client_id: str = None) -> str:
        """Submit stop order."""
        pass
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel existing order."""
        pass
    
    def get_open_orders(self, symbol: str = None) -> List[Order]:
        """Get open orders."""
        pass
```

### Technical Indicators

Built-in technical indicators for strategy development.

```python
from alphintra.indicators import SMA, EMA, RSI, MACD, BollingerBands

# Simple Moving Average
sma = SMA(period=20)
sma_value = sma.calculate(data.close)

# Exponential Moving Average  
ema = EMA(period=12)
ema_value = ema.calculate(data.close)

# RSI
rsi = RSI(period=14)
rsi_value = rsi.calculate(data.close)

# MACD
macd = MACD(fast_period=12, slow_period=26, signal_period=9)
macd_line, signal_line, histogram = macd.calculate(data.close)

# Bollinger Bands
bb = BollingerBands(period=20, std_dev=2)
upper, middle, lower = bb.calculate(data.close)
```

## Data Models

### Strategy Model

```python
class Strategy:
    id: UUID
    name: str
    description: Optional[str]
    code: str
    language: str = "python"
    sdk_version: str
    parameters: Dict[str, Any]
    status: StrategyStatus  # draft, active, archived, testing, deployed
    tags: List[str]
    
    # Performance metrics
    total_return: Optional[float]
    max_drawdown: Optional[float]
    sharpe_ratio: Optional[float]
    win_rate: Optional[float]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    user_id: UUID
```

### Dataset Model

```python
class Dataset:
    id: UUID
    name: str
    description: str
    asset_class: AssetClass  # crypto, stocks, forex, commodities
    source: DataSource
    frequency: DataFrequency  # 1m, 5m, 15m, 1h, 4h, 1d
    symbols: List[str]
    columns: List[str]
    
    # Data range
    start_date: str
    end_date: str
    record_count: int
    size_mb: float
    
    # Quality metrics
    quality_score: float
    completeness: float
    
    # Metadata
    tags: List[str]
    is_public: bool
    created_at: datetime
    user_id: UUID
```

### BacktestJob Model

```python
class BacktestJob:
    id: UUID
    strategy_id: UUID
    dataset_id: UUID
    name: str
    description: Optional[str]
    
    # Time period
    start_date: str
    end_date: str
    
    # Trading parameters
    initial_capital: float
    commission_rate: float
    slippage_rate: float
    
    # Configuration
    methodology: BacktestMethodology
    position_sizing: PositionSizing
    position_sizing_config: Dict[str, Any]
    
    # Risk management
    max_position_size: float
    max_portfolio_risk: float
    stop_loss_pct: Optional[float]
    take_profit_pct: Optional[float]
    
    # Status
    status: BacktestStatus  # queued, running, completed, failed
    progress: float
    
    # Results
    performance_metrics: Optional[Dict[str, float]]
    trades: Optional[List[Dict[str, Any]]]
    
    # Timestamps
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    user_id: UUID
```

### TrainingJob Model

```python
class TrainingJob:
    id: UUID
    strategy_id: UUID
    dataset_id: UUID
    job_name: str
    job_type: JobType  # training, hyperparameter_tuning
    
    # Resource allocation
    instance_type: InstanceType
    machine_type: str
    disk_size: int
    timeout_hours: int
    priority: TrainingPriority
    
    # Configuration
    hyperparameters: Dict[str, Any]
    training_config: Dict[str, Any]
    model_config: Dict[str, Any]
    
    # Status
    status: JobStatus  # queued, running, completed, failed, cancelled
    progress: float
    current_epoch: Optional[int]
    total_epochs: Optional[int]
    
    # Metrics
    metrics: Optional[Dict[str, Any]]
    
    # Results
    model_artifacts: Optional[Dict[str, str]]
    
    # Timestamps
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    user_id: UUID
```

## Error Handling

The API uses standard HTTP status codes and returns detailed error information.

### Error Response Format

```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "error_id": "unique-error-id",
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/strategies",
  "method": "POST",
  "validation_errors": [
    {
      "field": "code",
      "message": "Strategy code is required",
      "type": "value_error.missing"
    }
  ]
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request parameters or body
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: Insufficient permissions for the operation
- `404 Not Found`: Requested resource not found
- `409 Conflict`: Resource already exists or conflicting state
- `422 Unprocessable Entity`: Validation errors in request data
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Unexpected server error
- `503 Service Unavailable`: Service temporarily unavailable

### Specific Error Codes

- `STRATEGY_NOT_FOUND`: Strategy with given ID not found
- `DATASET_NOT_FOUND`: Dataset with given ID not found  
- `INVALID_STRATEGY_CODE`: Strategy code validation failed
- `TRAINING_JOB_FAILED`: Model training job failed
- `BACKTEST_FAILED`: Backtest execution failed
- `INSUFFICIENT_FUNDS`: Not enough capital for paper trading
- `MARKET_CLOSED`: Market is closed for trading
- `INVALID_SYMBOL`: Trading symbol not supported
- `RESOURCE_LIMIT_EXCEEDED`: Resource allocation limit exceeded

## Rate Limiting

API endpoints are rate-limited to ensure fair usage and system stability.

### Rate Limits

- **Default**: 100 requests per minute per user
- **Burst**: 200 requests (short-term burst allowance)
- **Strategy Execution**: 30 requests per minute
- **Training Jobs**: 10 requests per minute
- **File Uploads**: 5 requests per minute

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1642248600
X-RateLimit-Retry-After: 45
```

### Rate Limit Exceeded Response

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1642248600
X-RateLimit-Retry-After: 60

{
  "detail": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 60
}
```

## Examples

### Complete Strategy Development Workflow

```python
import requests
import time
from typing import Dict, Any

class AlphintraClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def create_strategy(self, strategy_data: Dict[str, Any]) -> str:
        """Create a new strategy."""
        response = requests.post(
            f"{self.base_url}/api/strategies",
            headers=self.headers,
            json=strategy_data
        )
        response.raise_for_status()
        return response.json()["strategy_id"]
    
    def create_backtest(self, backtest_data: Dict[str, Any]) -> str:
        """Create a backtest job."""
        response = requests.post(
            f"{self.base_url}/api/backtesting/jobs",
            headers=self.headers,
            json=backtest_data
        )
        response.raise_for_status()
        return response.json()["backtest_id"]
    
    def wait_for_backtest(self, backtest_id: str) -> Dict[str, Any]:
        """Wait for backtest completion and return results."""
        while True:
            response = requests.get(
                f"{self.base_url}/api/backtesting/jobs/{backtest_id}",
                headers=self.headers
            )
            response.raise_for_status()
            status = response.json()["status"]
            
            if status == "completed":
                # Get results
                results_response = requests.get(
                    f"{self.base_url}/api/backtesting/jobs/{backtest_id}/results",
                    headers=self.headers
                )
                results_response.raise_for_status()
                return results_response.json()
            elif status == "failed":
                raise Exception(f"Backtest failed: {response.json().get('error')}")
            
            time.sleep(10)  # Wait 10 seconds before checking again

# Usage example
client = AlphintraClient("http://localhost:8002", "your-jwt-token")

# 1. Create a strategy
strategy_code = '''
from alphintra import BaseStrategy
from alphintra.indicators import RSI

class RSIMeanReversion(BaseStrategy):
    def initialize(self, context):
        self.rsi = RSI(period=context.get_parameter("rsi_period", 14))
        context.set_variable("position", 0)
    
    def on_bar(self, context):
        bars = context.market_data.get_bars(count=50)
        current_rsi = self.rsi.calculate(bars.close)
        
        oversold = context.get_parameter("oversold_threshold", 30)
        overbought = context.get_parameter("overbought_threshold", 70)
        position = context.get_variable("position")
        
        if current_rsi < oversold and position <= 0:
            context.order_manager.market_order("BTCUSDT", 1.0)
            context.set_variable("position", 1)
            context.log(f"Buy signal: RSI={current_rsi:.2f}")
            
        elif current_rsi > overbought and position >= 0:
            context.order_manager.market_order("BTCUSDT", -1.0)
            context.set_variable("position", -1)
            context.log(f"Sell signal: RSI={current_rsi:.2f}")
'''

strategy_data = {
    "name": "RSI Mean Reversion Strategy",
    "description": "Mean reversion strategy using RSI indicator",
    "code": strategy_code,
    "parameters": {
        "rsi_period": 14,
        "oversold_threshold": 30,
        "overbought_threshold": 70
    },
    "tags": ["rsi", "mean-reversion", "crypto"]
}

strategy_id = client.create_strategy(strategy_data)
print(f"Strategy created: {strategy_id}")

# 2. Create a backtest
backtest_data = {
    "strategy_id": strategy_id,
    "dataset_id": "crypto-1min-dataset-uuid",
    "name": "RSI Strategy Backtest - 2023",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 100000.0,
    "commission_rate": 0.001,
    "slippage_rate": 0.0005
}

backtest_id = client.create_backtest(backtest_data)
print(f"Backtest started: {backtest_id}")

# 3. Wait for results
results = client.wait_for_backtest(backtest_id)
print(f"Backtest completed!")
print(f"Total Return: {results['performance_metrics']['total_return_pct']:.2f}%")
print(f"Sharpe Ratio: {results['performance_metrics']['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['performance_metrics']['max_drawdown_pct']:.2f}%")
```

### Paper Trading Example

```python
# Create paper trading session
session_data = {
    "strategy_id": 123,
    "name": "RSI Strategy Paper Trading",
    "initial_capital": 50000.0,
    "commission_rate": 0.001
}

response = requests.post(
    f"{base_url}/api/paper-trading/sessions",
    headers=headers,
    json=session_data
)
session_id = response.json()["session_id"]

# Submit orders
order_data = {
    "symbol": "BTCUSDT",
    "side": "buy",
    "order_type": "limit",
    "quantity": 0.1,
    "price": 42500.0,
    "time_in_force": "GTC"
}

response = requests.post(
    f"{base_url}/api/paper-trading/sessions/{session_id}/orders",
    headers=headers,
    json=order_data
)
order_id = response.json()["order_id"]

# Monitor portfolio
response = requests.get(
    f"{base_url}/api/paper-trading/sessions/{session_id}/portfolio",
    headers=headers
)
portfolio = response.json()
print(f"Portfolio Value: ${portfolio['total_value']:.2f}")
print(f"P&L: ${portfolio['total_pnl']:.2f} ({portfolio['total_pnl_pct']*100:.2f}%)")
```

### Model Training Example

```python
# Create training job
training_data = {
    "strategy_id": strategy_id,
    "dataset_id": "crypto-dataset-uuid", 
    "job_name": "LSTM Price Prediction",
    "instance_type": "GPU_MEDIUM",
    "timeout_hours": 6,
    "hyperparameters": {
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 100,
        "lstm_units": 128,
        "dropout_rate": 0.2
    },
    "training_config": {
        "model_type": "lstm",
        "sequence_length": 60,
        "features": ["open", "high", "low", "close", "volume"],
        "target": "close",
        "validation_split": 0.2
    }
}

response = requests.post(
    f"{base_url}/api/training/jobs",
    headers=headers,
    json=training_data
)
job_id = response.json()["job_id"]

# Monitor training progress
while True:
    response = requests.get(
        f"{base_url}/api/training/jobs/{job_id}",
        headers=headers
    )
    job_status = response.json()
    
    if job_status["status"] == "completed":
        print("Training completed!")
        print(f"Final validation loss: {job_status['metrics']['val_loss']}")
        break
    elif job_status["status"] == "failed":
        print(f"Training failed: {job_status.get('error')}")
        break
    else:
        progress = job_status["progress"] * 100
        print(f"Training progress: {progress:.1f}%")
        time.sleep(30)
```

This comprehensive documentation covers all major aspects of the AI/ML Strategy Service API, providing developers with the information needed to effectively integrate with and utilize the service's capabilities.