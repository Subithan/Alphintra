# Stripe Subscription Integration - Setup Guide

This document explains the Stripe integration for subscription management in the Auth Service.

## 🔑 Required Stripe Keys

To use Stripe in **test mode**, you need the following keys from your Stripe Dashboard:

### 1. **Stripe API Key** (Secret Key)
- **Where to find**: [Stripe Dashboard](https://dashboard.stripe.com/test/apikeys) → Developers → API keys
- **Format**: `sk_test_...`
- **Environment Variable**: `STRIPE_API_KEY`
- **Usage**: Server-side API calls to create customers, sessions, and process webhooks

### 2. **Webhook Secret**
- **Where to find**: [Stripe Dashboard](https://dashboard.stripe.com/test/webhooks) → Developers → Webhooks → Add endpoint
- **Format**: `whsec_...`
- **Environment Variable**: `STRIPE_WEBHOOK_SECRET`
- **Usage**: Verify webhook signatures to ensure events come from Stripe

### 3. **Price IDs** (for each subscription plan)
- **Where to find**: [Stripe Dashboard](https://dashboard.stripe.com/test/products) → Products → Click on product → Copy Price ID
- **Format**: `price_...`
- **Environment Variables**:
  - `STRIPE_PRICE_ID_BASIC` (e.g., `price_1234567890abcdef`)
  - `STRIPE_PRICE_ID_PRO` (e.g., `price_abcdef1234567890`)
  - `STRIPE_PRICE_ID_ENTERPRISE` (e.g., `price_fedcba0987654321`)
- **Usage**: Create checkout sessions for specific subscription plans

---

## 📋 Step-by-Step Setup

### Step 1: Create a Stripe Account
1. Go to [Stripe](https://stripe.com) and sign up
2. Complete your account setup
3. Make sure you're in **Test Mode** (toggle in top-right corner)

### Step 2: Get Your API Keys
1. Navigate to **Developers** → **API keys**
2. Copy your **Secret key** (starts with `sk_test_`)
3. **NEVER share this key publicly** - it's for server-side use only

### Step 3: Create Subscription Products & Prices
1. Go to **Products** → **Add product**
2. Create three products (or modify as needed):
   - **Basic Plan**: $9.99/month
   - **Pro Plan**: $19.99/month
   - **Enterprise Plan**: $49.99/month
3. For each product:
   - Set a name and description
   - Add a price (recurring, monthly)
   - Copy the **Price ID** (starts with `price_`)

### Step 4: Set Up Webhooks
1. Navigate to **Developers** → **Webhooks** → **Add endpoint**
2. Set endpoint URL to: `http://localhost:8009/api/subscriptions/webhook`
   - For production: `https://your-domain.com/api/subscriptions/webhook`
3. Select events to listen for:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Copy the **Signing secret** (starts with `whsec_`)

### Step 5: Configure Environment Variables

Create a `.env` file or add to your `application.yml`:

```bash
# Stripe Configuration
STRIPE_API_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Price IDs
STRIPE_PRICE_ID_BASIC=price_your_basic_price_id
STRIPE_PRICE_ID_PRO=price_your_pro_price_id
STRIPE_PRICE_ID_ENTERPRISE=price_your_enterprise_price_id

# Redirect URLs
STRIPE_SUCCESS_URL=http://localhost:3000/subscription/success
STRIPE_CANCEL_URL=http://localhost:3000/subscription/cancel
```

Or in `application.yml`:

```yaml
stripe:
  api-key: ${STRIPE_API_KEY:sk_test_your_key}
  webhook-secret: ${STRIPE_WEBHOOK_SECRET:whsec_your_secret}
  price-ids:
    basic: ${STRIPE_PRICE_ID_BASIC:price_basic_id}
    pro: ${STRIPE_PRICE_ID_PRO:price_pro_id}
    enterprise: ${STRIPE_PRICE_ID_ENTERPRISE:price_enterprise_id}
  success-url: ${STRIPE_SUCCESS_URL:http://localhost:3000/subscription/success}
  cancel-url: ${STRIPE_CANCEL_URL:http://localhost:3000/subscription/cancel}
```

---

## 🧪 Testing Webhooks Locally

Since Stripe can't reach `localhost` directly, you need to use the Stripe CLI:

### Install Stripe CLI
```bash
# Windows (with Scoop)
scoop bucket add stripe https://github.com/stripe/scoop-stripe-cli.git
scoop install stripe

# macOS (with Homebrew)
brew install stripe/stripe-cli/stripe

# Linux
# Download from https://github.com/stripe/stripe-cli/releases
```

### Login and Forward Webhooks
```bash
# Login to Stripe
stripe login

# Forward webhooks to your local server
stripe listen --forward-to localhost:8009/api/subscriptions/webhook
```

This will give you a **webhook signing secret** (whsec_...) - use this for local development.

---

## 🔄 API Endpoints

### 1. Create Checkout Session
**POST** `/api/subscriptions/create-checkout-session`

```json
{
  "priceId": "price_1234567890abcdef",
  "planName": "pro"
}
```

**Response:**
```json
{
  "success": true,
  "sessionId": "cs_test_...",
  "sessionUrl": "https://checkout.stripe.com/pay/cs_test_..."
}
```

### 2. Get Current Subscription
**GET** `/api/subscriptions/current`

**Response:**
```json
{
  "id": 1,
  "planName": "pro",
  "status": "active",
  "currentPeriodStart": "2024-01-01T00:00:00",
  "currentPeriodEnd": "2024-02-01T00:00:00",
  "cancelAtPeriodEnd": false,
  "amount": "19.99",
  "currency": "usd",
  "interval": "month"
}
```

### 3. Webhook Endpoint
**POST** `/api/subscriptions/webhook`

Automatically processes Stripe events.

---

## 📊 Database Schema

### Users Table (Updated)
```sql
ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(255);
ALTER TABLE users ADD COLUMN subscription_id VARCHAR(255);
ALTER TABLE users ADD COLUMN subscription_status VARCHAR(50);
ALTER TABLE users ADD COLUMN subscription_plan VARCHAR(50);
ALTER TABLE users ADD COLUMN subscription_start_date TIMESTAMP;
ALTER TABLE users ADD COLUMN subscription_end_date TIMESTAMP;
```

### Subscriptions Table (New)
```sql
CREATE TABLE subscriptions (
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
    -- ... more fields
);
```

---

## 🧪 Test Cards

Use these test card numbers in Stripe test mode:

| Card Number          | Scenario                |
|---------------------|-------------------------|
| 4242 4242 4242 4242 | Success                 |
| 4000 0000 0000 0002 | Card declined           |
| 4000 0025 0000 3155 | Requires authentication |

**Expiry**: Any future date  
**CVC**: Any 3 digits  
**ZIP**: Any 5 digits

---

## 🚀 Quick Start

1. **Start the auth service**:
   ```bash
   cd src/backend/auth-service
   ./mvnw spring-boot:run
   ```

2. **Start Stripe webhook forwarding** (in another terminal):
   ```bash
   stripe listen --forward-to localhost:8009/api/subscriptions/webhook
   ```

3. **Test subscription flow**:
   - Create checkout session via API
   - Complete payment with test card
   - Webhook automatically updates user subscription

---

## 🔐 Security Notes

- ✅ **Never commit** `STRIPE_API_KEY` to version control
- ✅ Always verify webhook signatures using `STRIPE_WEBHOOK_SECRET`
- ✅ Use environment variables for all secrets
- ✅ In production, use live keys (starts with `sk_live_` and `whsec_live_`)

---

## 📚 Additional Resources

- [Stripe Testing Guide](https://stripe.com/docs/testing)
- [Stripe Webhooks Documentation](https://stripe.com/docs/webhooks)
- [Stripe Checkout Documentation](https://stripe.com/docs/payments/checkout)
- [Stripe Subscriptions Guide](https://stripe.com/docs/billing/subscriptions/overview)

---

## ❓ FAQ

**Q: Do I need a real credit card for testing?**  
A: No! Use Stripe's test card numbers (see Test Cards section).

**Q: How do I switch to production?**  
A: Toggle to "Live mode" in Stripe Dashboard and use live keys (sk_live_...).

**Q: What if webhooks aren't working?**  
A: Make sure Stripe CLI is running with `stripe listen --forward-to localhost:8009/api/subscriptions/webhook`

**Q: Can I test without webhooks?**  
A: Yes, but subscriptions won't update automatically. Use the Stripe Dashboard to manually trigger events.
