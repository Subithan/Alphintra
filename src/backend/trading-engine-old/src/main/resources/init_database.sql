-- Create the trading_bots table
CREATE TABLE IF NOT EXISTS trading_bots (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    strategy_id BIGINT NOT NULL,
    status VARCHAR(255) NOT NULL,
    symbol VARCHAR(255) NOT NULL,
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
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (bot_id) REFERENCES trading_bots(id)
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