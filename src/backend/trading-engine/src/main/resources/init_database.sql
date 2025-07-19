-- Alphintra Trading Engine Database Schema
-- This script initializes the database schema for the trading engine

-- Creating Users table
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Creating Trading Accounts table
CREATE TABLE IF NOT EXISTS trading_accounts (
    account_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    account_type VARCHAR(20) NOT NULL,
    exchange VARCHAR(50) NOT NULL DEFAULT 'internal',
    total_balance DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    available_balance DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    locked_balance DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, account_type, exchange)
);

-- Creating Orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id BIGSERIAL PRIMARY KEY,
    order_uuid UUID DEFAULT gen_random_uuid() UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES trading_accounts(account_id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    order_type VARCHAR(20) NOT NULL CHECK (order_type IN ('MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT', 'TRAILING_STOP')),
    quantity DECIMAL(20, 8) NOT NULL CHECK (quantity > 0),
    price DECIMAL(20, 8),
    stop_price DECIMAL(20, 8),
    time_in_force VARCHAR(20) NOT NULL DEFAULT 'GTC' CHECK (time_in_force IN ('GTC', 'IOC', 'FOK', 'GTD')),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'FILLED', 'CANCELED', 'PARTIALLY_FILLED', 'REJECTED')),
    filled_quantity DECIMAL(20, 8) DEFAULT 0.0,
    average_price DECIMAL(20, 8),
    fee DECIMAL(20, 8) DEFAULT 0.0,
    exchange VARCHAR(50) NOT NULL DEFAULT 'internal',
    client_order_id VARCHAR(100),
    exchange_order_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Creating Trades table
CREATE TABLE IF NOT EXISTS trades (
    trade_id SERIAL PRIMARY KEY,
    trade_uuid UUID DEFAULT gen_random_uuid() UNIQUE,
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES trading_accounts(account_id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity DECIMAL(20, 8) NOT NULL CHECK (quantity > 0),
    price DECIMAL(20, 8) NOT NULL CHECK (price > 0),
    fee DECIMAL(20, 8) DEFAULT 0.0,
    exchange VARCHAR(50) NOT NULL DEFAULT 'internal',
    trade_type VARCHAR(10) CHECK (trade_type IN ('MAKER', 'TAKER')),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Creating Market Data table
CREATE TABLE IF NOT EXISTS market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    timeframe VARCHAR(10) NOT NULL DEFAULT '1m',
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    open_price DECIMAL(20, 8) NOT NULL,
    high_price DECIMAL(20, 8) NOT NULL,
    low_price DECIMAL(20, 8) NOT NULL,
    close_price DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(20, 8) NOT NULL,
    quote_volume DECIMAL(20, 8),
    trades_count INTEGER,
    UNIQUE(symbol, exchange, timeframe, timestamp)
);

-- Creating Trading Strategies table
CREATE TABLE IF NOT EXISTS trading_strategies (
    strategy_id SERIAL PRIMARY KEY,
    strategy_uuid UUID DEFAULT gen_random_uuid() UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'INACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'PAUSED')),
    parameters JSONB NOT NULL DEFAULT '{}',
    performance_metrics JSONB DEFAULT '{}',
    risk_limits JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Creating Trading Signals table
CREATE TABLE IF NOT EXISTS trading_signals (
    signal_id SERIAL PRIMARY KEY,
    strategy_id INTEGER NOT NULL REFERENCES trading_strategies(strategy_id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(20) NOT NULL CHECK (signal_type IN ('BUY', 'SELL', 'HOLD', 'CLOSE')),
    strength DECIMAL(5, 4) CHECK (strength >= 0 AND strength <= 1),
    confidence DECIMAL(5, 4) CHECK (confidence >= 0 AND confidence <= 1),
    price DECIMAL(20, 8),
    quantity DECIMAL(20, 8),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    data JSONB NOT NULL DEFAULT '{}',
    processed BOOLEAN DEFAULT FALSE
);

-- Creating Positions table
CREATE TABLE IF NOT EXISTS positions (
    position_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES trading_accounts(account_id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    average_price DECIMAL(20, 8),
    market_value DECIMAL(20, 8),
    unrealized_pnl DECIMAL(20, 8) DEFAULT 0.0,
    realized_pnl DECIMAL(20, 8) DEFAULT 0.0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, account_id, symbol)
);

-- Creating Asset Balances table
CREATE TABLE IF NOT EXISTS asset_balances (
    balance_id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES trading_accounts(account_id) ON DELETE CASCADE,
    asset VARCHAR(20) NOT NULL,
    total_balance DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    available_balance DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    locked_balance DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, asset)
);

-- Creating indexes for Users
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Creating indexes for Trading Accounts
CREATE INDEX IF NOT EXISTS idx_trading_accounts_user_id ON trading_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_accounts_type ON trading_accounts(account_type);
CREATE INDEX IF NOT EXISTS idx_trading_accounts_exchange ON trading_accounts(exchange);

-- Creating indexes for Orders
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_account_id ON orders(account_id);
CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_uuid ON orders(order_uuid);
CREATE INDEX IF NOT EXISTS idx_orders_exchange ON orders(exchange);

-- Creating indexes for Trades
CREATE INDEX IF NOT EXISTS idx_trades_order_id ON trades(order_id);
CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
CREATE INDEX IF NOT EXISTS idx_trades_uuid ON trades(trade_uuid);

-- Creating indexes for Market Data
CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_market_data_exchange ON market_data(exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_market_data_timeframe ON market_data(timeframe, timestamp DESC);

-- Creating indexes for Trading Strategies
CREATE INDEX IF NOT EXISTS idx_trading_strategies_user_id ON trading_strategies(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_strategies_status ON trading_strategies(status);
CREATE INDEX IF NOT EXISTS idx_trading_strategies_type ON trading_strategies(strategy_type);
CREATE INDEX IF NOT EXISTS idx_trading_strategies_uuid ON trading_strategies(strategy_uuid);

-- Creating indexes for Trading Signals
CREATE INDEX IF NOT EXISTS idx_trading_signals_strategy ON trading_signals(strategy_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trading_signals_symbol ON trading_signals(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trading_signals_processed ON trading_signals(processed);

-- Creating indexes for Positions
CREATE INDEX IF NOT EXISTS idx_positions_user_id ON positions(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_account_id ON positions(account_id);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);

-- Creating indexes for Asset Balances
CREATE INDEX IF NOT EXISTS idx_asset_balances_account_id ON asset_balances(account_id);
CREATE INDEX IF NOT EXISTS idx_asset_balances_asset ON asset_balances(asset);

-- Insert default data for testing
INSERT INTO users (username, email, password_hash, first_name, last_name) 
VALUES ('admin', 'admin@alphintra.com', 'hashed_password', 'Admin', 'User')
ON CONFLICT (username) DO NOTHING;

INSERT INTO trading_accounts (user_id, account_type, exchange, total_balance, available_balance)
SELECT user_id, 'SPOT', 'internal', 100000.0, 100000.0
FROM users WHERE username = 'admin'
ON CONFLICT (user_id, account_type, exchange) DO NOTHING;