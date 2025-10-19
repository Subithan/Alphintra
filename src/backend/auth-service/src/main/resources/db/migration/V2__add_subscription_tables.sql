-- Add subscription fields to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255) UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_plan VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_start_date TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_end_date TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_users_subscription_id ON users(subscription_id);

-- Create subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    stripe_subscription_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_customer_id VARCHAR(255) NOT NULL,
    stripe_price_id VARCHAR(255) NOT NULL,
    plan_name VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at TIMESTAMP,
    trial_start TIMESTAMP,
    trial_end TIMESTAMP,
    amount DECIMAL(10, 2),
    currency VARCHAR(3),
    interval VARCHAR(20),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT fk_subscription_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_subscription_id ON subscriptions(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_customer_id ON subscriptions(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
