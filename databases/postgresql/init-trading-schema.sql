-- Alphintra Trading Platform Database Schema
-- This script initializes the core database schema for the trading platform

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table for authentication and user management
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    kyc_level INTEGER DEFAULT 0, -- 0: None, 1: Basic, 2: Advanced, 3: Professional
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- User profiles for additional information
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    phone VARCHAR(20),
    country VARCHAR(3), -- ISO country code
    timezone VARCHAR(50),
    preferred_currency VARCHAR(10) DEFAULT 'USD',
    risk_tolerance VARCHAR(20) DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH
    trading_experience VARCHAR(20) DEFAULT 'BEGINNER', -- BEGINNER, INTERMEDIATE, ADVANCED, EXPERT
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trading accounts for users
CREATE TABLE IF NOT EXISTS trading_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_name VARCHAR(100) NOT NULL,
    account_type VARCHAR(20) NOT NULL, -- DEMO, LIVE
    broker VARCHAR(50) NOT NULL, -- BINANCE, BYBIT, etc.
    api_key_encrypted TEXT,
    api_secret_encrypted TEXT,
    is_active BOOLEAN DEFAULT true,
    balance_usd DECIMAL(20, 8) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Strategies table
CREATE TABLE IF NOT EXISTS strategies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    creator_id UUID NOT NULL REFERENCES users(id),
    strategy_type VARCHAR(50) NOT NULL, -- SCALPING, SWING, ARBITRAGE, etc.
    risk_level VARCHAR(20) DEFAULT 'MEDIUM',
    min_capital DECIMAL(20, 8),
    max_drawdown DECIMAL(5, 2), -- Percentage
    expected_return DECIMAL(5, 2), -- Percentage
    is_public BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    price DECIMAL(10, 2), -- Strategy price in USD
    config JSONB, -- Strategy configuration parameters
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User strategy subscriptions
CREATE TABLE IF NOT EXISTS user_strategies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    strategy_id UUID NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    trading_account_id UUID NOT NULL REFERENCES trading_accounts(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    allocation_percentage DECIMAL(5, 2) DEFAULT 100.00, -- Percentage of account to allocate
    max_position_size DECIMAL(20, 8),
    subscribed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    unsubscribed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, strategy_id, trading_account_id)
);

-- Trades table
CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    strategy_id UUID REFERENCES strategies(id),
    trading_account_id UUID NOT NULL REFERENCES trading_accounts(id),
    symbol VARCHAR(20) NOT NULL, -- e.g., BTCUSDT
    side VARCHAR(10) NOT NULL, -- BUY, SELL
    order_type VARCHAR(20) NOT NULL, -- MARKET, LIMIT, STOP_LOSS, etc.
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8),
    executed_price DECIMAL(20, 8),
    executed_quantity DECIMAL(20, 8),
    status VARCHAR(20) NOT NULL, -- PENDING, FILLED, PARTIALLY_FILLED, CANCELLED, FAILED
    broker_order_id VARCHAR(100),
    commission DECIMAL(20, 8) DEFAULT 0,
    commission_asset VARCHAR(10),
    pnl DECIMAL(20, 8), -- Profit and Loss
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    executed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Portfolio positions
CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    trading_account_id UUID NOT NULL REFERENCES trading_accounts(id),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL, -- LONG, SHORT
    quantity DECIMAL(20, 8) NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    current_price DECIMAL(20, 8),
    unrealized_pnl DECIMAL(20, 8),
    realized_pnl DECIMAL(20, 8) DEFAULT 0,
    margin_used DECIMAL(20, 8),
    is_open BOOLEAN DEFAULT true,
    opened_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    closed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, trading_account_id, symbol, side)
);

-- Strategy performance metrics
CREATE TABLE IF NOT EXISTS strategy_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id UUID NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    total_pnl DECIMAL(20, 8) DEFAULT 0,
    max_drawdown DECIMAL(5, 2),
    sharpe_ratio DECIMAL(10, 4),
    win_rate DECIMAL(5, 2),
    avg_win DECIMAL(20, 8),
    avg_loss DECIMAL(20, 8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- TRADE_EXECUTED, STRATEGY_ALERT, SYSTEM_MAINTENANCE, etc.
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT false,
    priority VARCHAR(20) DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH, URGENT
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE
);

-- API keys for external integrations
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_name VARCHAR(100) NOT NULL,
    api_key VARCHAR(255) NOT NULL,
    permissions JSONB, -- Array of permissions
    is_active BOOLEAN DEFAULT true,
    last_used TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_strategy_id ON trades(strategy_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at);
CREATE INDEX IF NOT EXISTS idx_positions_user_id ON positions(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
CREATE INDEX IF NOT EXISTS idx_positions_is_open ON positions(is_open);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);

-- Insert sample data for development
INSERT INTO users (email, username, password_hash, first_name, last_name, kyc_level, is_verified) VALUES
('admin@alphintra.com', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uO9G', 'Admin', 'User', 3, true),
('demo@alphintra.com', 'demo_user', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uO9G', 'Demo', 'User', 1, true)
ON CONFLICT (email) DO NOTHING;

-- Insert sample strategies
INSERT INTO strategies (name, description, creator_id, strategy_type, risk_level, min_capital, price, is_public, is_active) VALUES
('BTC Scalping Pro', 'High-frequency Bitcoin scalping strategy using technical indicators', (SELECT id FROM users WHERE email = 'admin@alphintra.com'), 'SCALPING', 'HIGH', 1000.00, 99.99, true, true),
('ETH Swing Trader', 'Medium-term Ethereum swing trading strategy', (SELECT id FROM users WHERE email = 'admin@alphintra.com'), 'SWING', 'MEDIUM', 500.00, 49.99, true, true)
ON CONFLICT DO NOTHING;

COMMIT;