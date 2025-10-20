-- Add subscription_status column to users table if it doesn't exist
-- Default value is 'INACTIVE' (not subscribed)
-- Note: Column may already exist, so using IF NOT EXISTS
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(20) DEFAULT 'INACTIVE';

-- Update existing NULL values to 'INACTIVE'
UPDATE users SET subscription_status = 'INACTIVE' WHERE subscription_status IS NULL;

-- Create index for subscription_status for faster queries
CREATE INDEX IF NOT EXISTS idx_users_subscription_status ON users(subscription_status);
