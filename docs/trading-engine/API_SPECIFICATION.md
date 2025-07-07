# Trading Engine API Specification

## 🎯 Overview

The Alphintra Trading Engine provides comprehensive RESTful APIs, GraphQL endpoints, and WebSocket connections for real-time trading operations across multiple brokers and asset classes.

## 🔗 Base URLs

- **Production**: `https://api.alphintra.com/trading`
- **Staging**: `https://staging-api.alphintra.com/trading`
- **Development**: `http://localhost:8080/trading`

## 🔐 Authentication

### JWT Token Authentication
```http
Authorization: Bearer <jwt_token>
```

### API Key Authentication (For programmatic access)
```http
X-API-Key: <api_key>
X-API-Secret: <api_secret>
X-Timestamp: <timestamp>
X-Signature: <hmac_sha256_signature>
```

## 📡 REST API Endpoints

### 🚀 Trading Operations

#### Submit Trading Signal
```yaml
POST /api/v1/signals
```

**Request Body:**
```json
{
  "signalId": "uuid",
  "modelId": "model-123",
  "userId": "user-456",
  "symbol": "BTCUSDT",
  "action": "BUY",
  "confidence": 0.85,
  "quantity": 1000,
  "entryPrice": 45000,
  "stopLoss": 43000,
  "takeProfit": 47000,
  "timeframe": "1H",
  "strategy": "momentum",
  "metadata": {
    "source": "ml_model",
    "version": "v2.1",
    "features": ["rsi", "macd", "volume"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "signalId": "uuid",
  "status": "ACCEPTED",
  "message": "Signal accepted for processing",
  "orderId": "order-789",
  "estimatedExecutionTime": "2024-01-01T10:30:15Z",
  "riskAssessment": {
    "riskScore": 6.5,
    "riskLevel": "MEDIUM",
    "adjustments": [
      {
        "type": "QUANTITY_REDUCTION",
        "originalQuantity": 1000,
        "adjustedQuantity": 850,
        "reason": "Position size limit"
      }
    ]
  }
}
```

#### Place Order
```yaml
POST /api/v1/orders
```

**Request Body:**
```json
{
  "symbol": "AAPL",
  "side": "BUY",
  "type": "LIMIT",
  "quantity": 100,
  "price": 150.00,
  "timeInForce": "GTC",
  "brokerId": "alpaca",
  "clientOrderId": "client-123",
  "stopPrice": 145.00,
  "takeProfitPrice": 160.00,
  "orderClass": "BRACKET",
  "metadata": {
    "strategy": "swing_trading",
    "signalId": "signal-456"
  }
}
```

**Response:**
```json
{
  "orderId": "order-789",
  "clientOrderId": "client-123",
  "brokerOrderId": "broker-abc123",
  "status": "NEW",
  "symbol": "AAPL",
  "side": "BUY",
  "type": "LIMIT",
  "quantity": 100,
  "price": 150.00,
  "filledQuantity": 0,
  "averagePrice": 0,
  "orderTime": "2024-01-01T10:30:00Z",
  "commission": 1.00,
  "estimatedCommission": 1.00
}
```

#### Get Orders
```yaml
GET /api/v1/orders?status=NEW&symbol=BTCUSDT&fromTime=2024-01-01T00:00:00Z
```

**Response:**
```json
{
  "orders": [
    {
      "orderId": "order-789",
      "symbol": "BTCUSDT",
      "side": "BUY",
      "type": "LIMIT",
      "quantity": 1.5,
      "price": 45000,
      "status": "PARTIALLY_FILLED",
      "filledQuantity": 0.8,
      "averagePrice": 44950,
      "orderTime": "2024-01-01T10:30:00Z",
      "lastUpdateTime": "2024-01-01T10:35:00Z"
    }
  ],
  "pagination": {
    "total": 150,
    "page": 1,
    "pageSize": 50,
    "hasNext": true
  }
}
```

#### Cancel Order
```yaml
DELETE /api/v1/orders/{orderId}
```

**Response:**
```json
{
  "orderId": "order-789",
  "status": "CANCELLED",
  "cancelledAt": "2024-01-01T10:45:00Z",
  "message": "Order cancelled successfully"
}
```

### 📊 Portfolio Management

#### Get Portfolio Summary
```yaml
GET /api/v1/portfolio
```

**Response:**
```json
{
  "portfolioId": "portfolio-123",
  "userId": "user-456",
  "totalValue": 100000.00,
  "cashBalance": 25000.00,
  "positionsValue": 75000.00,
  "unrealizedPnL": 2500.00,
  "realizedPnL": 1500.00,
  "dailyPnL": 800.00,
  "totalReturn": 0.04,
  "totalReturnPercent": 4.0,
  "sharpeRatio": 1.25,
  "maxDrawdown": -0.08,
  "lastUpdated": "2024-01-01T10:30:00Z",
  "performance": {
    "1d": 0.008,
    "7d": 0.025,
    "30d": 0.04,
    "ytd": 0.12
  }
}
```

#### Get Positions
```yaml
GET /api/v1/positions?symbols=BTCUSDT,ETHUSDT
```

**Response:**
```json
{
  "positions": [
    {
      "positionId": "pos-123",
      "symbol": "BTCUSDT",
      "side": "LONG",
      "quantity": 2.5,
      "averagePrice": 44000,
      "currentPrice": 45000,
      "marketValue": 112500,
      "unrealizedPnL": 2500,
      "realizedPnL": 0,
      "unrealizedPnLPercent": 2.27,
      "openedAt": "2024-01-01T09:00:00Z",
      "lastUpdated": "2024-01-01T10:30:00Z"
    }
  ]
}
```

### 📈 Market Data

#### Get Quote
```yaml
GET /api/v1/quotes/{symbol}
```

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "bidPrice": 44950,
  "askPrice": 45050,
  "lastPrice": 45000,
  "volume": 1250000,
  "high24h": 46000,
  "low24h": 43500,
  "change24h": 1500,
  "changePercent24h": 3.45,
  "timestamp": "2024-01-01T10:30:00Z"
}
```

#### Get Historical Data
```yaml
GET /api/v1/historical/{symbol}?timeframe=1H&count=100
```

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1H",
  "data": [
    {
      "timestamp": "2024-01-01T10:00:00Z",
      "open": 44800,
      "high": 45200,
      "low": 44700,
      "close": 45000,
      "volume": 125000
    }
  ]
}
```

### ⚡ Execution Management

#### Get Execution Quality Metrics
```yaml
GET /api/v1/execution/metrics?fromDate=2024-01-01&toDate=2024-01-31
```

**Response:**
```json
{
  "period": {
    "from": "2024-01-01",
    "to": "2024-01-31"
  },
  "metrics": {
    "totalOrders": 1250,
    "filledOrders": 1180,
    "fillRate": 0.944,
    "averageSlippage": 0.0025,
    "averageExecutionTime": 245,
    "averageCommission": 2.50,
    "priceImprovementRate": 0.15,
    "averagePriceImprovement": 0.001
  },
  "byBroker": [
    {
      "brokerId": "binance",
      "fillRate": 0.98,
      "averageSlippage": 0.002,
      "averageExecutionTime": 180
    }
  ],
  "byAssetClass": [
    {
      "assetClass": "CRYPTO",
      "fillRate": 0.95,
      "averageSlippage": 0.003
    }
  ]
}
```

### 🛡️ Risk Management

#### Get Risk Metrics
```yaml
GET /api/v1/risk/metrics
```

**Response:**
```json
{
  "portfolioId": "portfolio-123",
  "riskMetrics": {
    "var1Day": {
      "amount": 2500,
      "percent": 0.025,
      "confidence": 95
    },
    "var5Day": {
      "amount": 5590,
      "percent": 0.056,
      "confidence": 95
    },
    "expectedShortfall": 3200,
    "beta": 1.15,
    "sharpeRatio": 1.25,
    "sortinoRatio": 1.45,
    "informationRatio": 0.85,
    "maxDrawdown": 0.08,
    "currentDrawdown": 0.02
  },
  "concentrationRisk": [
    {
      "category": "CRYPTO",
      "exposure": 0.65,
      "limit": 0.70,
      "status": "WITHIN_LIMITS"
    }
  ],
  "correlationRisk": {
    "maxCorrelation": 0.75,
    "correlationPairs": [
      {
        "symbol1": "BTCUSDT",
        "symbol2": "ETHUSDT", 
        "correlation": 0.68
      }
    ]
  },
  "calculatedAt": "2024-01-01T10:30:00Z"
}
```

#### Set Risk Limits
```yaml
PUT /api/v1/risk/limits
```

**Request Body:**
```json
{
  "maxDailyLoss": 5000,
  "maxDailyLossPercent": 5.0,
  "maxPositionSize": 10000,
  "maxPositionSizePercent": 10.0,
  "maxLeverage": 3.0,
  "maxConcentration": {
    "CRYPTO": 0.70,
    "STOCKS": 0.80,
    "FOREX": 0.60
  },
  "stopLossRequired": true,
  "maxCorrelation": 0.75
}
```

### 🔧 Broker Management

#### Get Supported Brokers
```yaml
GET /api/v1/brokers
```

**Response:**
```json
{
  "brokers": [
    {
      "brokerId": "binance",
      "name": "Binance",
      "assetClasses": ["CRYPTO"],
      "features": ["SPOT", "FUTURES", "MARGIN"],
      "status": "ACTIVE",
      "apiVersion": "v3",
      "rateLimit": 1200,
      "commission": {
        "maker": 0.001,
        "taker": 0.001
      }
    },
    {
      "brokerId": "alpaca",
      "name": "Alpaca Markets",
      "assetClasses": ["STOCKS"],
      "features": ["SPOT", "OPTIONS"],
      "status": "ACTIVE",
      "commission": {
        "stocks": 0.0,
        "options": 0.65
      }
    }
  ]
}
```

#### Connect to Broker
```yaml
POST /api/v1/brokers/{brokerId}/connect
```

**Request Body:**
```json
{
  "apiKey": "encrypted_api_key",
  "secretKey": "encrypted_secret_key",
  "passphrase": "optional_passphrase",
  "isTestnet": true,
  "permissions": ["TRADING", "ACCOUNT_DATA"]
}
```

## 🔄 GraphQL API

### Schema Definition
```graphql
type Query {
  # Portfolio queries
  portfolio(userId: ID!): Portfolio
  positions(userId: ID!, symbols: [String]): [Position]
  
  # Order queries
  orders(
    userId: ID!
    status: OrderStatus
    symbol: String
    fromTime: DateTime
    toTime: DateTime
    limit: Int = 50
    offset: Int = 0
  ): OrderConnection
  
  # Market data queries
  quote(symbol: String!): Quote
  historicalData(
    symbol: String!
    timeframe: Timeframe!
    count: Int = 100
  ): [OHLCV]
  
  # Risk queries
  riskMetrics(userId: ID!): RiskMetrics
  riskAlerts(userId: ID!, severity: AlertSeverity): [RiskAlert]
  
  # Execution analytics
  executionMetrics(
    userId: ID!
    fromDate: Date!
    toDate: Date!
  ): ExecutionMetrics
}

type Mutation {
  # Trading operations
  submitSignal(input: TradingSignalInput!): SignalResponse
  placeOrder(input: OrderInput!): OrderResponse
  cancelOrder(orderId: ID!): CancelResponse
  modifyOrder(orderId: ID!, modification: OrderModificationInput!): OrderResponse
  
  # Portfolio management
  rebalancePortfolio(userId: ID!, targets: [AssetAllocationInput!]!): RebalanceResponse
  
  # Risk management
  setRiskLimits(userId: ID!, limits: RiskLimitsInput!): RiskLimits
  emergencyStop(userId: ID!, reason: String!): EmergencyStopResponse
  
  # Broker management
  connectBroker(brokerId: String!, credentials: BrokerCredentialsInput!): BrokerConnectionResponse
  disconnectBroker(brokerId: String!): DisconnectionResponse
}

type Subscription {
  # Real-time updates
  orderUpdates(userId: ID!): OrderUpdate
  positionUpdates(userId: ID!): PositionUpdate
  portfolioUpdates(userId: ID!): PortfolioUpdate
  
  # Market data streams
  marketData(symbols: [String!]!): MarketDataUpdate
  priceAlerts(userId: ID!): PriceAlert
  
  # Risk monitoring
  riskAlerts(userId: ID!): RiskAlert
  
  # Trade execution
  executionUpdates(userId: ID!): ExecutionUpdate
}

# Type definitions
type Portfolio {
  portfolioId: ID!
  userId: ID!
  totalValue: Float!
  cashBalance: Float!
  positionsValue: Float!
  unrealizedPnL: Float!
  realizedPnL: Float!
  dailyPnL: Float!
  totalReturn: Float!
  sharpeRatio: Float
  maxDrawdown: Float
  performance: PerformanceMetrics!
  lastUpdated: DateTime!
}

type Order {
  orderId: ID!
  clientOrderId: String
  brokerOrderId: String
  symbol: String!
  side: OrderSide!
  type: OrderType!
  quantity: Float!
  price: Float
  stopPrice: Float
  status: OrderStatus!
  filledQuantity: Float!
  averagePrice: Float
  commission: Float
  orderTime: DateTime!
  fillTime: DateTime
  timeInForce: TimeInForce!
  brokerId: String!
}

enum OrderStatus {
  NEW
  PARTIALLY_FILLED
  FILLED
  CANCELLED
  REJECTED
  EXPIRED
  PENDING_CANCEL
}

enum OrderSide {
  BUY
  SELL
}

enum OrderType {
  MARKET
  LIMIT
  STOP
  STOP_LIMIT
  TRAILING_STOP
  ICEBERG
}
```

### Example GraphQL Queries

#### Get Portfolio with Positions
```graphql
query GetPortfolioWithPositions($userId: ID!) {
  portfolio(userId: $userId) {
    portfolioId
    totalValue
    cashBalance
    positionsValue
    unrealizedPnL
    realizedPnL
    dailyPnL
    performance {
      day1
      day7
      day30
      ytd
    }
  }
  
  positions(userId: $userId) {
    positionId
    symbol
    side
    quantity
    averagePrice
    currentPrice
    marketValue
    unrealizedPnL
    unrealizedPnLPercent
  }
}
```

#### Place Order with Risk Check
```graphql
mutation PlaceOrderWithRiskCheck($orderInput: OrderInput!) {
  placeOrder(input: $orderInput) {
    success
    orderId
    brokerOrderId
    status
    message
    riskAssessment {
      riskScore
      riskLevel
      adjustments {
        type
        originalValue
        adjustedValue
        reason
      }
    }
    estimatedExecution {
      expectedFillTime
      estimatedSlippage
      estimatedCommission
    }
  }
}
```

## 🔌 WebSocket API

### Connection
```javascript
const ws = new WebSocket('wss://api.alphintra.com/trading/ws');

// Authentication
ws.send(JSON.stringify({
  action: 'authenticate',
  token: 'jwt_token_here'
}));
```

### Subscription Messages

#### Subscribe to Order Updates
```javascript
ws.send(JSON.stringify({
  action: 'subscribe',
  channel: 'orders',
  userId: 'user-123',
  filters: {
    symbols: ['BTCUSDT', 'ETHUSDT'],
    status: ['NEW', 'PARTIALLY_FILLED']
  }
}));
```

#### Subscribe to Market Data
```javascript
ws.send(JSON.stringify({
  action: 'subscribe',
  channel: 'market_data',
  symbols: ['BTCUSDT', 'ETHUSDT', 'AAPL'],
  data_types: ['quotes', 'trades', 'orderbook']
}));
```

#### Subscribe to Portfolio Updates
```javascript
ws.send(JSON.stringify({
  action: 'subscribe',
  channel: 'portfolio',
  userId: 'user-123',
  update_frequency: 'real_time' // or 'throttled'
}));
```

### Message Formats

#### Order Update Message
```json
{
  "channel": "orders",
  "type": "order_update",
  "timestamp": "2024-01-01T10:30:00Z",
  "data": {
    "orderId": "order-789",
    "status": "PARTIALLY_FILLED",
    "filledQuantity": 0.5,
    "averagePrice": 44975,
    "lastFillPrice": 44980,
    "lastFillQuantity": 0.2,
    "lastFillTime": "2024-01-01T10:29:58Z",
    "commission": 0.5
  }
}
```

#### Market Data Message
```json
{
  "channel": "market_data",
  "type": "quote_update", 
  "timestamp": "2024-01-01T10:30:00.123Z",
  "data": {
    "symbol": "BTCUSDT",
    "bidPrice": 44950,
    "askPrice": 45050,
    "lastPrice": 45000,
    "volume": 1250000,
    "change24h": 1500,
    "changePercent24h": 3.45
  }
}
```

#### Risk Alert Message
```json
{
  "channel": "risk_alerts",
  "type": "risk_alert",
  "timestamp": "2024-01-01T10:30:00Z",
  "data": {
    "alertId": "alert-456",
    "severity": "HIGH",
    "type": "DRAWDOWN_BREACH",
    "title": "Daily drawdown limit exceeded",
    "message": "Portfolio drawdown of 6.2% exceeds daily limit of 5%",
    "portfolioId": "portfolio-123",
    "metrics": {
      "currentDrawdown": 0.062,
      "maxDrawdown": 0.05,
      "portfolioValue": 94000,
      "dailyPnL": -6000
    },
    "recommendedActions": [
      "Review open positions",
      "Consider reducing position sizes",
      "Tighten stop losses"
    ]
  }
}
```

## 📊 Error Handling

### Standard Error Response
```json
{
  "success": false,
  "error": {
    "code": "INVALID_ORDER",
    "message": "Order quantity exceeds position size limit",
    "details": {
      "requestedQuantity": 1000,
      "maxAllowedQuantity": 750,
      "reason": "Risk management: position size limit"
    },
    "timestamp": "2024-01-01T10:30:00Z",
    "requestId": "req-789"
  }
}
```

### Error Codes
| Code | HTTP Status | Description |
|------|-------------|-------------|
| INVALID_REQUEST | 400 | Malformed request data |
| UNAUTHORIZED | 401 | Invalid or missing authentication |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| INVALID_ORDER | 400 | Order validation failed |
| INSUFFICIENT_FUNDS | 400 | Not enough balance |
| MARKET_CLOSED | 400 | Market is closed |
| RISK_LIMIT_EXCEEDED | 400 | Risk limits violated |
| BROKER_ERROR | 502 | Broker API error |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Internal server error |

## 🔒 Rate Limiting

### Default Limits
- **REST API**: 1000 requests per minute per user
- **GraphQL**: 500 queries per minute per user  
- **WebSocket**: 100 subscriptions per connection

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1640995200
X-RateLimit-Retry-After: 60
```

## 📱 SDK Examples

### Python SDK
```python
from alphintra_trading import TradingClient

# Initialize client
client = TradingClient(
    api_key='your_api_key',
    api_secret='your_api_secret',
    environment='production'  # or 'sandbox'
)

# Submit trading signal
signal = client.submit_signal(
    symbol='BTCUSDT',
    action='BUY',
    confidence=0.85,
    quantity=1.5,
    entry_price=45000,
    stop_loss=43000,
    take_profit=47000
)

# Place order
order = client.place_order(
    symbol='AAPL',
    side='BUY',
    type='LIMIT',
    quantity=100,
    price=150.00,
    broker_id='alpaca'
)

# Get portfolio
portfolio = client.get_portfolio()
print(f"Total Value: ${portfolio.total_value:,.2f}")
```

### JavaScript SDK
```javascript
import { TradingClient } from '@alphintra/trading-sdk';

const client = new TradingClient({
  apiKey: 'your_api_key',
  apiSecret: 'your_api_secret',
  environment: 'production'
});

// Submit signal
const signal = await client.submitSignal({
  symbol: 'BTCUSDT',
  action: 'BUY',
  confidence: 0.85,
  quantity: 1.5,
  entryPrice: 45000,
  stopLoss: 43000,
  takeProfit: 47000
});

// Real-time updates
client.subscribe('orders', (orderUpdate) => {
  console.log('Order update:', orderUpdate);
});

client.subscribe('portfolio', (portfolioUpdate) => {
  console.log('Portfolio update:', portfolioUpdate);
});
```

This comprehensive API specification provides complete documentation for integrating with the Alphintra Trading Engine across all supported interfaces and protocols.