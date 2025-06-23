-- alphintra PostgreSQL Database Initialization
-- This script sets up the core database schema for the trading platform

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    country_code VARCHAR(3),
    kyc_level INTEGER DEFAULT 0 CHECK (kyc_level >= 0 AND kyc_level <= 3),
    kyc_status VARCHAR(20) DEFAULT 'pending' CHECK (kyc_status IN ('pending', 'approved', 'rejected', 'under_review')),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- KYC documents table
CREATE TABLE kyc_documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL CHECK (document_type IN ('passport', 'drivers_license', 'national_id', 'utility_bill', 'bank_statement')),
    document_url VARCHAR(500),
    verification_status VARCHAR(20) DEFAULT 'pending' CHECK (verification_status IN ('pending', 'approved', 'rejected')),
    uploaded_at TIMESTAMP DEFAULT NOW(),
    verified_at TIMESTAMP,
    rejection_reason TEXT
);

-- User profiles table
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    date_of_birth DATE,
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    occupation VARCHAR(100),
    annual_income DECIMAL(15,2),
    trading_experience VARCHAR(20) CHECK (trading_experience IN ('beginner', 'intermediate', 'advanced', 'professional')),
    risk_tolerance VARCHAR(20) CHECK (risk_tolerance IN ('low', 'medium', 'high')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User accounts (trading accounts)
CREATE TABLE user_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    account_type VARCHAR(20) DEFAULT 'spot' CHECK (account_type IN ('spot', 'futures', 'margin')),
    account_name VARCHAR(100),
    balance DECIMAL(20,8) DEFAULT 0.00000000,
    available_balance DECIMAL(20,8) DEFAULT 0.00000000,
    locked_balance DECIMAL(20,8) DEFAULT 0.00000000,
    currency VARCHAR(10) DEFAULT 'USDT',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Asset balances
CREATE TABLE asset_balances (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES user_accounts(id) ON DELETE CASCADE,
    asset VARCHAR(20) NOT NULL,
    total_balance DECIMAL(20,8) DEFAULT 0.00000000,
    available_balance DECIMAL(20,8) DEFAULT 0.00000000,
    locked_balance DECIMAL(20,8) DEFAULT 0.00000000,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(account_id, asset)
);

-- Trading strategies
CREATE TABLE trading_strategies (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(50) NOT NULL CHECK (strategy_type IN ('dca', 'grid', 'momentum', 'mean_reversion', 'arbitrage', 'ml_based')),
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT false,
    performance_metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Strategy subscriptions (marketplace)
CREATE TABLE strategy_subscriptions (
    id SERIAL PRIMARY KEY,
    subscriber_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES trading_strategies(id) ON DELETE CASCADE,
    subscription_type VARCHAR(20) DEFAULT 'monthly' CHECK (subscription_type IN ('monthly', 'quarterly', 'yearly', 'lifetime')),
    price DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'cancelled', 'expired')),
    started_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Trades table
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    trade_id UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    account_id INTEGER REFERENCES user_accounts(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES trading_strategies(id) ON DELETE SET NULL,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('buy', 'sell')),
    order_type VARCHAR(20) NOT NULL CHECK (order_type IN ('market', 'limit', 'stop', 'stop_limit')),
    quantity DECIMAL(20,8) NOT NULL,
    price DECIMAL(20,8),
    filled_quantity DECIMAL(20,8) DEFAULT 0.00000000,
    average_price DECIMAL(20,8),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'filled', 'partially_filled', 'cancelled', 'rejected')),
    fees DECIMAL(20,8) DEFAULT 0.00000000,
    fee_currency VARCHAR(10),
    exchange_order_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    executed_at TIMESTAMP
);

-- Order history
CREATE TABLE order_history (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER REFERENCES trades(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL,
    quantity DECIMAL(20,8),
    price DECIMAL(20,8),
    timestamp TIMESTAMP DEFAULT NOW(),
    details JSONB
);

-- Risk management rules
CREATE TABLE risk_rules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    rule_type VARCHAR(50) NOT NULL CHECK (rule_type IN ('max_position_size', 'max_daily_loss', 'max_drawdown', 'stop_loss', 'take_profit')),
    rule_config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Audit logs
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- API keys
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    key_name VARCHAR(100) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    api_secret_hash VARCHAR(255) NOT NULL,
    permissions JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    last_used TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Notifications
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('trade_executed', 'strategy_alert', 'risk_warning', 'kyc_update', 'system_maintenance')),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT false,
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'critical')),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_uuid ON users(uuid);
CREATE INDEX idx_trades_user_id ON trades(user_id);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_created_at ON trades(created_at);
CREATE INDEX idx_trades_status ON trades(status);
CREATE INDEX idx_asset_balances_account_asset ON asset_balances(account_id, asset);
CREATE INDEX idx_strategies_user_id ON trading_strategies(user_id);
CREATE INDEX idx_strategies_public ON trading_strategies(is_public) WHERE is_public = true;
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = false;

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_accounts_updated_at BEFORE UPDATE ON user_accounts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_asset_balances_updated_at BEFORE UPDATE ON asset_balances FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_trading_strategies_updated_at BEFORE UPDATE ON trading_strategies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_trades_updated_at BEFORE UPDATE ON trades FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_risk_rules_updated_at BEFORE UPDATE ON risk_rules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data
INSERT INTO users (email, password_hash, first_name, last_name, kyc_level, kyc_status, is_verified) VALUES
('admin@alphintra.com', crypt('admin123', gen_salt('bf')), 'Admin', 'User', 3, 'approved', true),
('trader@example.com', crypt('trader123', gen_salt('bf')), 'John', 'Trader', 2, 'approved', true),
('demo@example.com', crypt('demo123', gen_salt('bf')), 'Demo', 'User', 1, 'approved', true);

-- Insert sample trading accounts
INSERT INTO user_accounts (user_id, account_type, account_name, balance, available_balance, currency) VALUES
(1, 'spot', 'Admin Spot Account', 100000.00000000, 100000.00000000, 'USDT'),
(2, 'spot', 'Trader Spot Account', 10000.00000000, 10000.00000000, 'USDT'),
(2, 'futures', 'Trader Futures Account', 5000.00000000, 5000.00000000, 'USDT'),
(3, 'spot', 'Demo Account', 1000.00000000, 1000.00000000, 'USDT');

-- Insert sample asset balances
INSERT INTO asset_balances (account_id, asset, total_balance, available_balance) VALUES
(1, 'USDT', 100000.00000000, 100000.00000000),
(2, 'USDT', 10000.00000000, 10000.00000000),
(3, 'USDT', 5000.00000000, 5000.00000000),
(4, 'USDT', 1000.00000000, 1000.00000000);

-- Insert sample trading strategies
INSERT INTO trading_strategies (user_id, name, description, strategy_type, config, is_public) VALUES
(1, 'BTC DCA Strategy', 'Dollar Cost Averaging for Bitcoin', 'dca', '{"symbol": "BTCUSDT", "amount": 100, "interval": "daily"}', true),
(1, 'ETH Grid Trading', 'Grid trading strategy for Ethereum', 'grid', '{"symbol": "ETHUSDT", "grid_size": 0.01, "grid_count": 10}', true),
(2, 'Momentum Scalping', 'Short-term momentum trading', 'momentum', '{"timeframe": "5m", "rsi_threshold": 70}', false);

COMMIT;