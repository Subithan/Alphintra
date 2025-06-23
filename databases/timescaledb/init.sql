-- alphintra TimescaleDB Initialization
-- This script sets up time-series tables for market data and trading metrics

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Market data table (OHLCV data)
CREATE TABLE market_data (
    time TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    timeframe VARCHAR(10) NOT NULL, -- 1m, 5m, 15m, 1h, 4h, 1d
    open_price DECIMAL(20,8) NOT NULL,
    high_price DECIMAL(20,8) NOT NULL,
    low_price DECIMAL(20,8) NOT NULL,
    close_price DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8) NOT NULL,
    quote_volume DECIMAL(20,8),
    trades_count INTEGER,
    taker_buy_volume DECIMAL(20,8),
    taker_buy_quote_volume DECIMAL(20,8)
);

-- Convert to hypertable
SELECT create_hypertable('market_data', 'time', chunk_time_interval => INTERVAL '1 day');

-- Create composite index
CREATE INDEX idx_market_data_symbol_time ON market_data (symbol, time DESC);
CREATE INDEX idx_market_data_exchange_symbol ON market_data (exchange, symbol, time DESC);
CREATE INDEX idx_market_data_timeframe ON market_data (timeframe, symbol, time DESC);

-- Real-time tick data
CREATE TABLE tick_data (
    time TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    quantity DECIMAL(20,8) NOT NULL,
    side VARCHAR(10) CHECK (side IN ('buy', 'sell')),
    trade_id VARCHAR(100),
    is_maker BOOLEAN
);

-- Convert to hypertable with smaller chunks for high-frequency data
SELECT create_hypertable('tick_data', 'time', chunk_time_interval => INTERVAL '1 hour');

-- Create indexes for tick data
CREATE INDEX idx_tick_data_symbol_time ON tick_data (symbol, time DESC);
CREATE INDEX idx_tick_data_exchange_symbol ON tick_data (exchange, symbol, time DESC);

-- Order book snapshots
CREATE TABLE orderbook_snapshots (
    time TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    bids JSONB NOT NULL, -- Array of [price, quantity] arrays
    asks JSONB NOT NULL, -- Array of [price, quantity] arrays
    last_update_id BIGINT
);

-- Convert to hypertable
SELECT create_hypertable('orderbook_snapshots', 'time', chunk_time_interval => INTERVAL '6 hours');

-- Create indexes
CREATE INDEX idx_orderbook_symbol_time ON orderbook_snapshots (symbol, time DESC);
CREATE INDEX idx_orderbook_exchange_symbol ON orderbook_snapshots (exchange, symbol, time DESC);

-- Trading signals
CREATE TABLE trading_signals (
    time TIMESTAMPTZ NOT NULL,
    strategy_id INTEGER NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    signal_type VARCHAR(20) NOT NULL CHECK (signal_type IN ('buy', 'sell', 'hold', 'close')),
    strength DECIMAL(5,4) CHECK (strength >= 0 AND strength <= 1), -- Signal strength 0-1
    price DECIMAL(20,8),
    quantity DECIMAL(20,8),
    confidence DECIMAL(5,4) CHECK (confidence >= 0 AND confidence <= 1),
    metadata JSONB,
    processed BOOLEAN DEFAULT false
);

-- Convert to hypertable
SELECT create_hypertable('trading_signals', 'time', chunk_time_interval => INTERVAL '1 day');

-- Create indexes
CREATE INDEX idx_signals_strategy_time ON trading_signals (strategy_id, time DESC);
CREATE INDEX idx_signals_symbol_time ON trading_signals (symbol, time DESC);
CREATE INDEX idx_signals_unprocessed ON trading_signals (processed, time DESC) WHERE processed = false;

-- Portfolio performance metrics
CREATE TABLE portfolio_metrics (
    time TIMESTAMPTZ NOT NULL,
    user_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    total_value DECIMAL(20,8) NOT NULL,
    available_balance DECIMAL(20,8) NOT NULL,
    locked_balance DECIMAL(20,8) NOT NULL,
    unrealized_pnl DECIMAL(20,8) DEFAULT 0,
    realized_pnl DECIMAL(20,8) DEFAULT 0,
    daily_pnl DECIMAL(20,8) DEFAULT 0,
    total_fees DECIMAL(20,8) DEFAULT 0,
    trade_count INTEGER DEFAULT 0,
    win_rate DECIMAL(5,4) DEFAULT 0,
    sharpe_ratio DECIMAL(10,6),
    max_drawdown DECIMAL(5,4),
    volatility DECIMAL(10,6)
);

-- Convert to hypertable
SELECT create_hypertable('portfolio_metrics', 'time', chunk_time_interval => INTERVAL '1 day');

-- Create indexes
CREATE INDEX idx_portfolio_user_time ON portfolio_metrics (user_id, time DESC);
CREATE INDEX idx_portfolio_account_time ON portfolio_metrics (account_id, time DESC);

-- Strategy performance metrics
CREATE TABLE strategy_metrics (
    time TIMESTAMPTZ NOT NULL,
    strategy_id INTEGER NOT NULL,
    symbol VARCHAR(50),
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    total_pnl DECIMAL(20,8) DEFAULT 0,
    total_fees DECIMAL(20,8) DEFAULT 0,
    win_rate DECIMAL(5,4) DEFAULT 0,
    avg_win DECIMAL(20,8) DEFAULT 0,
    avg_loss DECIMAL(20,8) DEFAULT 0,
    profit_factor DECIMAL(10,6) DEFAULT 0,
    sharpe_ratio DECIMAL(10,6),
    max_drawdown DECIMAL(5,4),
    calmar_ratio DECIMAL(10,6),
    sortino_ratio DECIMAL(10,6)
);

-- Convert to hypertable
SELECT create_hypertable('strategy_metrics', 'time', chunk_time_interval => INTERVAL '1 day');

-- Create indexes
CREATE INDEX idx_strategy_metrics_id_time ON strategy_metrics (strategy_id, time DESC);
CREATE INDEX idx_strategy_metrics_symbol_time ON strategy_metrics (symbol, time DESC);

-- Risk metrics
CREATE TABLE risk_metrics (
    time TIMESTAMPTZ NOT NULL,
    user_id INTEGER NOT NULL,
    account_id INTEGER,
    var_1d DECIMAL(20,8), -- Value at Risk 1 day
    var_7d DECIMAL(20,8), -- Value at Risk 7 days
    cvar_1d DECIMAL(20,8), -- Conditional VaR 1 day
    cvar_7d DECIMAL(20,8), -- Conditional VaR 7 days
    beta DECIMAL(10,6), -- Market beta
    correlation_btc DECIMAL(5,4), -- Correlation with BTC
    correlation_eth DECIMAL(5,4), -- Correlation with ETH
    leverage_ratio DECIMAL(10,6),
    margin_ratio DECIMAL(5,4),
    liquidation_price DECIMAL(20,8)
);

-- Convert to hypertable
SELECT create_hypertable('risk_metrics', 'time', chunk_time_interval => INTERVAL '1 day');

-- Create indexes
CREATE INDEX idx_risk_metrics_user_time ON risk_metrics (user_id, time DESC);
CREATE INDEX idx_risk_metrics_account_time ON risk_metrics (account_id, time DESC);

-- System metrics
CREATE TABLE system_metrics (
    time TIMESTAMPTZ NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(20,8) NOT NULL,
    metric_unit VARCHAR(20),
    service_name VARCHAR(50),
    instance_id VARCHAR(100),
    tags JSONB
);

-- Convert to hypertable
SELECT create_hypertable('system_metrics', 'time', chunk_time_interval => INTERVAL '1 day');

-- Create indexes
CREATE INDEX idx_system_metrics_name_time ON system_metrics (metric_name, time DESC);
CREATE INDEX idx_system_metrics_service_time ON system_metrics (service_name, time DESC);

-- Create continuous aggregates for common queries

-- 1-hour OHLCV aggregates
CREATE MATERIALIZED VIEW market_data_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS time,
    exchange,
    symbol,
    FIRST(open_price, time) AS open_price,
    MAX(high_price) AS high_price,
    MIN(low_price) AS low_price,
    LAST(close_price, time) AS close_price,
    SUM(volume) AS volume,
    SUM(quote_volume) AS quote_volume,
    SUM(trades_count) AS trades_count
FROM market_data
WHERE timeframe = '1m'
GROUP BY time_bucket('1 hour', time), exchange, symbol;

-- Daily OHLCV aggregates
CREATE MATERIALIZED VIEW market_data_1d
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS time,
    exchange,
    symbol,
    FIRST(open_price, time) AS open_price,
    MAX(high_price) AS high_price,
    MIN(low_price) AS low_price,
    LAST(close_price, time) AS close_price,
    SUM(volume) AS volume,
    SUM(quote_volume) AS quote_volume,
    SUM(trades_count) AS trades_count
FROM market_data
WHERE timeframe = '1m'
GROUP BY time_bucket('1 day', time), exchange, symbol;

-- Daily portfolio performance
CREATE MATERIALIZED VIEW daily_portfolio_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS time,
    user_id,
    LAST(total_value, time) AS total_value,
    LAST(available_balance, time) AS available_balance,
    LAST(unrealized_pnl, time) AS unrealized_pnl,
    SUM(realized_pnl) AS daily_realized_pnl,
    SUM(total_fees) AS daily_fees,
    SUM(trade_count) AS daily_trades
FROM portfolio_metrics
GROUP BY time_bucket('1 day', time), user_id;

-- Set up refresh policies for continuous aggregates
SELECT add_continuous_aggregate_policy('market_data_1h',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

SELECT add_continuous_aggregate_policy('market_data_1d',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

SELECT add_continuous_aggregate_policy('daily_portfolio_summary',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

-- Set up data retention policies
-- Keep tick data for 30 days
SELECT add_retention_policy('tick_data', INTERVAL '30 days');

-- Keep orderbook snapshots for 7 days
SELECT add_retention_policy('orderbook_snapshots', INTERVAL '7 days');

-- Keep 1-minute market data for 1 year
SELECT add_retention_policy('market_data', INTERVAL '1 year');

-- Keep trading signals for 6 months
SELECT add_retention_policy('trading_signals', INTERVAL '6 months');

-- Keep system metrics for 3 months
SELECT add_retention_policy('system_metrics', INTERVAL '3 months');

-- Insert sample market data
INSERT INTO market_data (time, exchange, symbol, timeframe, open_price, high_price, low_price, close_price, volume, quote_volume, trades_count) VALUES
(NOW() - INTERVAL '1 hour', 'binance', 'BTCUSDT', '1m', 45000.00, 45100.00, 44950.00, 45050.00, 10.5, 472500.00, 150),
(NOW() - INTERVAL '59 minutes', 'binance', 'BTCUSDT', '1m', 45050.00, 45150.00, 45000.00, 45100.00, 8.2, 369820.00, 120),
(NOW() - INTERVAL '58 minutes', 'binance', 'BTCUSDT', '1m', 45100.00, 45200.00, 45080.00, 45180.00, 12.1, 546780.00, 180),
(NOW() - INTERVAL '1 hour', 'binance', 'ETHUSDT', '1m', 3200.00, 3210.00, 3195.00, 3205.00, 50.5, 161600.00, 200),
(NOW() - INTERVAL '59 minutes', 'binance', 'ETHUSDT', '1m', 3205.00, 3215.00, 3200.00, 3210.00, 45.2, 145092.00, 180),
(NOW() - INTERVAL '58 minutes', 'binance', 'ETHUSDT', '1m', 3210.00, 3220.00, 3208.00, 3218.00, 38.7, 124466.00, 160);

-- Insert sample trading signals
INSERT INTO trading_signals (time, strategy_id, symbol, signal_type, strength, price, quantity, confidence, metadata) VALUES
(NOW() - INTERVAL '30 minutes', 1, 'BTCUSDT', 'buy', 0.75, 45100.00, 0.1, 0.85, '{"indicator": "rsi_oversold", "rsi_value": 25}'),
(NOW() - INTERVAL '25 minutes', 1, 'ETHUSDT', 'buy', 0.65, 3210.00, 1.5, 0.70, '{"indicator": "macd_bullish", "macd_value": 0.05}'),
(NOW() - INTERVAL '15 minutes', 2, 'BTCUSDT', 'sell', 0.80, 45200.00, 0.05, 0.90, '{"indicator": "resistance_level", "level": 45200}');

COMMIT;