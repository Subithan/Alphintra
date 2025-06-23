-- Alphintra Trading Platform TimescaleDB Schema
-- This script initializes time-series tables for market data and trading metrics

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Market data table for OHLCV data
CREATE TABLE IF NOT EXISTS market_data (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    timeframe VARCHAR(10) NOT NULL, -- 1m, 5m, 15m, 1h, 4h, 1d
    open DECIMAL(20, 8) NOT NULL,
    high DECIMAL(20, 8) NOT NULL,
    low DECIMAL(20, 8) NOT NULL,
    close DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(20, 8) NOT NULL,
    quote_volume DECIMAL(20, 8),
    trades_count INTEGER,
    taker_buy_volume DECIMAL(20, 8),
    taker_buy_quote_volume DECIMAL(20, 8)
);

-- Convert to hypertable
SELECT create_hypertable('market_data', 'time', if_not_exists => TRUE);

-- Create composite index for efficient queries
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_time ON market_data (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_market_data_exchange_symbol ON market_data (exchange, symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_market_data_timeframe ON market_data (timeframe, symbol, time DESC);

-- Real-time price ticks
CREATE TABLE IF NOT EXISTS price_ticks (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(20, 8),
    side VARCHAR(10), -- BUY, SELL
    trade_id VARCHAR(100)
);

-- Convert to hypertable
SELECT create_hypertable('price_ticks', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_price_ticks_symbol_time ON price_ticks (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_price_ticks_exchange ON price_ticks (exchange, symbol, time DESC);

-- Order book snapshots
CREATE TABLE IF NOT EXISTS order_book_snapshots (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    bids JSONB NOT NULL, -- Array of [price, quantity] arrays
    asks JSONB NOT NULL, -- Array of [price, quantity] arrays
    best_bid DECIMAL(20, 8),
    best_ask DECIMAL(20, 8),
    spread DECIMAL(20, 8),
    spread_percentage DECIMAL(10, 6)
);

-- Convert to hypertable
SELECT create_hypertable('order_book_snapshots', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_orderbook_symbol_time ON order_book_snapshots (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_orderbook_exchange ON order_book_snapshots (exchange, symbol, time DESC);

-- Trading signals from strategies
CREATE TABLE IF NOT EXISTS trading_signals (
    time TIMESTAMPTZ NOT NULL,
    strategy_id UUID NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(20) NOT NULL, -- BUY, SELL, HOLD
    strength DECIMAL(5, 2), -- Signal strength 0-100
    price DECIMAL(20, 8),
    quantity DECIMAL(20, 8),
    stop_loss DECIMAL(20, 8),
    take_profit DECIMAL(20, 8),
    confidence DECIMAL(5, 2), -- Confidence level 0-100
    indicators JSONB, -- Technical indicators used
    metadata JSONB -- Additional signal metadata
);

-- Convert to hypertable
SELECT create_hypertable('trading_signals', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_signals_strategy_time ON trading_signals (strategy_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_signals_symbol_time ON trading_signals (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_signals_type ON trading_signals (signal_type, time DESC);

-- Portfolio value over time
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    time TIMESTAMPTZ NOT NULL,
    user_id UUID NOT NULL,
    trading_account_id UUID NOT NULL,
    total_value_usd DECIMAL(20, 8) NOT NULL,
    available_balance DECIMAL(20, 8) NOT NULL,
    margin_used DECIMAL(20, 8) DEFAULT 0,
    unrealized_pnl DECIMAL(20, 8) DEFAULT 0,
    realized_pnl_daily DECIMAL(20, 8) DEFAULT 0,
    positions_count INTEGER DEFAULT 0,
    active_orders_count INTEGER DEFAULT 0,
    holdings JSONB -- Asset breakdown
);

-- Convert to hypertable
SELECT create_hypertable('portfolio_snapshots', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_portfolio_user_time ON portfolio_snapshots (user_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_portfolio_account_time ON portfolio_snapshots (trading_account_id, time DESC);

-- Strategy performance metrics over time
CREATE TABLE IF NOT EXISTS strategy_metrics (
    time TIMESTAMPTZ NOT NULL,
    strategy_id UUID NOT NULL,
    user_id UUID, -- NULL for global strategy metrics
    trading_account_id UUID, -- NULL for global strategy metrics
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    total_pnl DECIMAL(20, 8) DEFAULT 0,
    daily_pnl DECIMAL(20, 8) DEFAULT 0,
    drawdown DECIMAL(5, 2) DEFAULT 0,
    win_rate DECIMAL(5, 2) DEFAULT 0,
    profit_factor DECIMAL(10, 4) DEFAULT 0,
    sharpe_ratio DECIMAL(10, 4) DEFAULT 0,
    max_consecutive_wins INTEGER DEFAULT 0,
    max_consecutive_losses INTEGER DEFAULT 0,
    avg_trade_duration INTERVAL,
    volatility DECIMAL(10, 6) DEFAULT 0
);

-- Convert to hypertable
SELECT create_hypertable('strategy_metrics', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_strategy_metrics_strategy_time ON strategy_metrics (strategy_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_strategy_metrics_user_time ON strategy_metrics (user_id, time DESC) WHERE user_id IS NOT NULL;

-- System metrics for monitoring
CREATE TABLE IF NOT EXISTS system_metrics (
    time TIMESTAMPTZ NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(20, 8) NOT NULL,
    metric_unit VARCHAR(20),
    service_name VARCHAR(50),
    instance_id VARCHAR(100),
    tags JSONB
);

-- Convert to hypertable
SELECT create_hypertable('system_metrics', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_system_metrics_name_time ON system_metrics (metric_name, time DESC);
CREATE INDEX IF NOT EXISTS idx_system_metrics_service ON system_metrics (service_name, time DESC);

-- Trade execution logs
CREATE TABLE IF NOT EXISTS trade_executions (
    time TIMESTAMPTZ NOT NULL,
    trade_id UUID NOT NULL,
    user_id UUID NOT NULL,
    strategy_id UUID,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    order_type VARCHAR(20) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8),
    executed_price DECIMAL(20, 8),
    executed_quantity DECIMAL(20, 8),
    commission DECIMAL(20, 8) DEFAULT 0,
    slippage DECIMAL(10, 6) DEFAULT 0,
    latency_ms INTEGER, -- Execution latency in milliseconds
    broker VARCHAR(50),
    broker_order_id VARCHAR(100),
    status VARCHAR(20) NOT NULL
);

-- Convert to hypertable
SELECT create_hypertable('trade_executions', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_trade_executions_user_time ON trade_executions (user_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_trade_executions_strategy_time ON trade_executions (strategy_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_trade_executions_symbol_time ON trade_executions (symbol, time DESC);

-- Create continuous aggregates for common queries

-- Hourly OHLCV aggregation
CREATE MATERIALIZED VIEW IF NOT EXISTS market_data_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS time,
    symbol,
    exchange,
    first(open, time) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, time) AS close,
    sum(volume) AS volume,
    count(*) AS trades_count
FROM market_data
WHERE timeframe = '1m'
GROUP BY time_bucket('1 hour', time), symbol, exchange;

-- Daily OHLCV aggregation
CREATE MATERIALIZED VIEW IF NOT EXISTS market_data_1d
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS time,
    symbol,
    exchange,
    first(open, time) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, time) AS close,
    sum(volume) AS volume,
    count(*) AS trades_count
FROM market_data
WHERE timeframe = '1m'
GROUP BY time_bucket('1 day', time), symbol, exchange;

-- Hourly portfolio performance
CREATE MATERIALIZED VIEW IF NOT EXISTS portfolio_performance_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS time,
    user_id,
    trading_account_id,
    last(total_value_usd, time) AS total_value_usd,
    last(unrealized_pnl, time) AS unrealized_pnl,
    sum(realized_pnl_daily) AS realized_pnl_hourly,
    avg(positions_count) AS avg_positions_count
FROM portfolio_snapshots
GROUP BY time_bucket('1 hour', time), user_id, trading_account_id;

-- Set up data retention policies (keep raw data for 30 days, aggregated for 1 year)
SELECT add_retention_policy('price_ticks', INTERVAL '30 days', if_not_exists => TRUE);
SELECT add_retention_policy('order_book_snapshots', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_retention_policy('system_metrics', INTERVAL '90 days', if_not_exists => TRUE);

-- Enable compression for older data
ALTER TABLE market_data SET (timescaledb.compress = true, timescaledb.compress_segmentby = 'symbol, exchange, timeframe');
ALTER TABLE price_ticks SET (timescaledb.compress = true, timescaledb.compress_segmentby = 'symbol, exchange');
ALTER TABLE trading_signals SET (timescaledb.compress = true, timescaledb.compress_segmentby = 'strategy_id, symbol');
ALTER TABLE portfolio_snapshots SET (timescaledb.compress = true, timescaledb.compress_segmentby = 'user_id, trading_account_id');

-- Add compression policies (compress data older than 7 days)
SELECT add_compression_policy('market_data', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_compression_policy('price_ticks', INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_compression_policy('trading_signals', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_compression_policy('portfolio_snapshots', INTERVAL '7 days', if_not_exists => TRUE);

COMMIT;