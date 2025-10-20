-- Create the trading_bots table
CREATE TABLE IF NOT EXISTS trading_bots (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    strategy_id BIGINT NOT NULL,
    status VARCHAR(255) NOT NULL,
    symbol VARCHAR(255) NOT NULL,
    capital_allocation_percentage DECIMAL(5, 2),
    started_at TIMESTAMP,
    stopped_at TIMESTAMP
);

-- Create the trade_orders table
CREATE TABLE IF NOT EXISTS trade_orders (
    id BIGSERIAL PRIMARY KEY,
    bot_id BIGINT,
    exchange_order_id VARCHAR(255),
    symbol VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL,
    side VARCHAR(255) NOT NULL,
    price DECIMAL(19, 8),
    amount DECIMAL(19, 8),
    status VARCHAR(255),
    pending_order_id BIGINT,
    exit_reason VARCHAR(50),
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (bot_id) REFERENCES trading_bots(id)
);

-- Create the pending_orders table
CREATE TABLE IF NOT EXISTS pending_orders (
    id BIGSERIAL PRIMARY KEY,
    position_id BIGINT NOT NULL,
    take_profit_price DECIMAL(18, 8),
    stop_loss_price DECIMAL(18, 8),
    quantity DECIMAL(18, 8) NOT NULL,
    status VARCHAR(50) NOT NULL,
    symbol VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    triggered_at TIMESTAMP,
    triggered_type VARCHAR(50),
    cancelled_at TIMESTAMP
);

-- Create the positions table
CREATE TABLE IF NOT EXISTS positions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    asset VARCHAR(255) NOT NULL,
    quantity DECIMAL(19, 8) NOT NULL,
    average_entry_price DECIMAL(19, 8),
    UNIQUE(user_id, asset)
);