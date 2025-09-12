# Backtest Microservice

A dedicated microservice for running backtests on generated trading strategies from the no-code-service.

## Features

- **Strategy Execution**: Runs generated Python trading strategy code with historical market data
- **Performance Analysis**: Comprehensive performance metrics including Sharpe ratio, drawdown, win rate
- **Market Data**: Simulated historical data for multiple symbols and timeframes
- **Risk Metrics**: Advanced risk analysis with Sortino ratio, Calmar ratio, and more
- **Trade Analysis**: Detailed trade statistics and equity curve generation
- **API Integration**: RESTful API for integration with no-code-service

## Architecture

```
┌─────────────────┐    HTTP API    ┌─────────────────┐
│  No-Code        │ ──────────────► │  Backtest       │
│  Service        │                 │  Service        │
│  (Port 8006)    │ ◄────────────── │  (Port 8007)    │
└─────────────────┘    Results      └─────────────────┘
         │                                    │
         │                                    │
         ▼                                    ▼
┌─────────────────┐                ┌─────────────────┐
│  PostgreSQL     │                │  Market Data    │
│  Database       │                │  Provider       │
│  (Strategies)   │                │  (Historical)   │
└─────────────────┘                └─────────────────┘
```

## Installation

1. Install dependencies:
```bash
cd src/backend/backtest-service
pip install -r requirements.txt
```

2. Run the service:
```bash
python main.py
```

The service will start on `http://localhost:8007`

## API Endpoints

### Core Endpoints

#### `POST /api/backtest/run`
Execute backtest for strategy code.

**Request:**
```json
{
  "workflow_id": "d08c4e90-fae3-4543-ba4b-e326d6e1ae06",
  "strategy_code": "# Generated Python strategy code...",
  "config": {
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 10000,
    "commission": 0.001,
    "symbols": ["AAPL"],
    "timeframe": "1h"
  }
}
```

**Response:**
```json
{
  "success": true,
  "execution_id": "uuid-string",
  "performance_metrics": {
    "total_return_percent": 15.5,
    "sharpe_ratio": 1.8,
    "max_drawdown_percent": -5.2,
    "total_trades": 25,
    "win_rate": 72.0,
    "profit_factor": 2.1
  },
  "trade_summary": {
    "total_trades": 25,
    "winning_trades": 18,
    "losing_trades": 7
  }
}
```

#### `GET /health`
Health check endpoint.

#### `GET /api/backtest/market-data/symbols`
Get available symbols for backtesting.

### Integration with No-Code Service

The backtest service is called by the no-code-service via the backtest client:

```python
# In no-code-service
result = await backtest_client.run_backtest(
    workflow_id=workflow_id,
    strategy_code=workflow.generated_code,
    config=backtest_config
)
```

## Performance Metrics

The service calculates comprehensive performance metrics:

### Return Metrics
- **Total Return**: Absolute profit/loss
- **Total Return %**: Percentage return on initial capital
- **Final Capital**: Capital at end of backtest

### Risk Metrics
- **Sharpe Ratio**: Risk-adjusted return (higher is better)
- **Sortino Ratio**: Risk-adjusted return using downside deviation
- **Calmar Ratio**: Annual return divided by maximum drawdown
- **Max Drawdown**: Maximum peak-to-trough decline
- **Max Drawdown %**: Maximum drawdown as percentage

### Trade Metrics
- **Total Trades**: Number of trades executed
- **Win Rate**: Percentage of profitable trades
- **Winning/Losing Trades**: Count of profitable/unprofitable trades
- **Average Win/Loss**: Average profit per winning/losing trade
- **Profit Factor**: Ratio of gross profit to gross loss

## Market Data

The service provides simulated market data for testing:

### Supported Symbols
- **Stocks**: AAPL, GOOGL, MSFT, TSLA, AMZN
- **Crypto**: BTCUSD, ETHUSD

### Supported Timeframes
- 1m, 5m, 15m, 1h, 4h, 1d

### Data Features
- Realistic price movements using random walk
- Proper OHLCV structure
- Volume simulation
- Configurable date ranges

## Configuration

Environment variables:

```bash
PORT=8007                    # Service port
LOG_LEVEL=info              # Logging level
```

## Error Handling

The service provides detailed error responses:

```json
{
  "success": false,
  "execution_id": "uuid-string",
  "error": "Strategy execution failed: NameError: name 'undefined_variable' is not defined",
  "exception_type": "NameError"
}
```

## Microservice Benefits

### Separation of Concerns
- **No-Code Service**: Focuses on strategy generation and workflow management
- **Backtest Service**: Dedicated to strategy execution and performance analysis

### Scalability
- Can be scaled independently based on backtest load
- Multiple instances can run different backtests concurrently
- Easy to add more powerful hardware for compute-intensive backtests

### Reliability
- Isolated failures don't affect the main no-code service
- Can be restarted without disrupting workflow generation
- Independent deployment and updates

### Development
- Separate teams can work on each service
- Different technology stacks if needed
- Independent testing and deployment

## Usage Flow

1. **Strategy Generation**: User creates workflow in no-code-service
2. **Code Generation**: No-code-service generates Python strategy code
3. **Backtest Request**: User triggers backtest via no-code-service API
4. **Service Call**: No-code-service calls backtest-service with strategy code
5. **Execution**: Backtest-service executes strategy with market data
6. **Results**: Performance metrics returned to no-code-service
7. **Storage**: Results stored in database via no-code-service

## Future Enhancements

- Real market data integration (Alpha Vantage, IEX Cloud, etc.)
- Advanced portfolio optimization
- Multi-asset strategy support
- Custom benchmark comparisons
- Paper trading simulation
- Performance attribution analysis
- Risk factor decomposition

## Development

To run in development mode:

```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn main:app --reload --port 8007

# Run tests
python -m pytest tests/
```

## Docker Support

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8007

CMD ["python", "main.py"]
```