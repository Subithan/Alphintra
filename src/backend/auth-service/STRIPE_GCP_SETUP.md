# 🚀 Stripe Setup for GCP Production

## ✅ What Was Updated

### 1. Kubernetes Configuration Files
- **`infra/kubernetes/base/auth-service/secret.yaml`** - Added Stripe API keys and webhook secret
- **`infra/kubernetes/base/auth-service/configmap.yaml`** - Added redirect URLs
- **`infra/kubernetes/base/auth-service/deployment.yaml`** - Added environment variable mappings

---

## 📋 Step-by-Step Setup Guide

### Step 1: Get Your Stripe Credentials

1. **Go to Stripe Dashboard**: https://dashboard.stripe.com/
2. **Get API Keys**:
   - Navigate to **Developers** → **API keys**
   - Copy your **Secret key** (starts with `sk_test_` or `sk_live_`)

3. **Set Up Webhook**:
   - Navigate to **Developers** → **Webhooks**
   - Click **Add endpoint**
   - **Endpoint URL**: `https://api.alphintra.com/api/subscriptions/webhook`
   - **Events to send**:
     - ✅ `checkout.session.completed`
     - ✅ `customer.subscription.created`
     - ✅ `customer.subscription.updated`
     - ✅ `customer.subscription.deleted`
     - ✅ `invoice.payment_succeeded`
     - ✅ `invoice.payment_failed`
   - Click **Add endpoint**
   - Copy the **Signing secret** (starts with `whsec_`)

4. **Create Products and Prices**:
   - Navigate to **Products** → **Add product**
   - Create three products:
     - **Basic** - $9.99/month
     - **Pro** - $19.99/month
     - **Enterprise** - $49.99/month
   - For each product, copy the **Price ID** (starts with `price_`)

---

### Step 2: Update Kubernetes Secrets

**⚠️ IMPORTANT: Replace placeholder values with your actual Stripe credentials**

Edit `infra/kubernetes/base/auth-service/secret.yaml`:

```yaml
STRIPE_API_KEY: "sk_test_YOUR_ACTUAL_KEY_HERE"  # Replace this!
STRIPE_WEBHOOK_SECRET: "whsec_YOUR_ACTUAL_SECRET_HERE"  # Replace this!
STRIPE_PRICE_ID_BASIC: "price_YOUR_BASIC_PRICE_ID"  # Replace this!
STRIPE_PRICE_ID_PRO: "price_YOUR_PRO_PRICE_ID"  # Replace this!
STRIPE_PRICE_ID_ENTERPRISE: "price_YOUR_ENTERPRISE_PRICE_ID"  # Replace this!
```

---

### Step 3: Deploy to GCP

#### Option A: Using kubectl directly

```bash
# Navigate to Kubernetes directory
cd infra/kubernetes/base/auth-service

# Apply the updated secrets and config
kubectl apply -f secret.yaml
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml

# Verify the deployment
kubectl get pods -l app=auth-service
kubectl logs -l app=auth-service --tail=100
```

#### Option B: Using Cloud Build (Recommended)

```bash
# Navigate to auth-service
cd src/backend/auth-service

# Trigger Cloud Build
bash build.sh
```

This will:
1. Build the Docker image
2. Push to Google Container Registry
3. Deploy to GKE with updated environment variables

---

### Step 4: Verify Webhook Configuration

1. **Test the webhook endpoint**:
```bash
curl https://api.alphintra.com/api/subscriptions/webhook \
  -H "Content-Type: application/json" \
  -d '{}'
```

You should get a `400 Bad Request` (expected - Stripe signature missing)

2. **In Stripe Dashboard**:
   - Go to **Developers** → **Webhooks**
   - Click on your webhook endpoint
   - Click **Send test webhook**
   - Select `checkout.session.completed`
   - Check if the webhook is received successfully (200 OK)

---

### Step 5: Update Frontend Environment Variables

Update your frontend to use production URLs:

**Frontend `.env` or `.env.production`:**
```bash
NEXT_PUBLIC_STRIPE_PRICE_ID_BASIC=price_YOUR_BASIC_PRICE_ID
NEXT_PUBLIC_STRIPE_PRICE_ID_PRO=price_YOUR_PRO_PRICE_ID
NEXT_PUBLIC_STRIPE_PRICE_ID_ENTERPRISE=price_YOUR_ENTERPRISE_PRICE_ID
NEXT_PUBLIC_API_BASE_URL=https://api.alphintra.com
```

---

## 🔍 Verify Everything Works

### 1. Check Auth Service Logs
```bash
kubectl logs -l app=auth-service --follow
```

Look for:
```
✅ Stripe initialized successfully
✅ Application started successfully
```

### 2. Test Subscription Flow

1. **Visit your frontend**: https://alphintra.com/subscription
2. **Click on a plan** (e.g., Pro)
3. **Complete checkout** using Stripe test card:
   - Card: `4242 4242 4242 4242`
   - Expiry: Any future date
   - CVC: Any 3 digits
4. **Check backend logs** for webhook processing:
   ```
   Processing Stripe webhook event: checkout.session.completed
   Subscription saved: <subscription-id>
   ```

---

## 🎯 Production Checklist

- [ ] Stripe webhook URL is `https://api.alphintra.com/api/subscriptions/webhook`
- [ ] Webhook signing secret is added to Kubernetes secret
- [ ] All 6 webhook events are configured in Stripe
- [ ] Stripe API key is in Kubernetes secret
- [ ] All 3 price IDs are in Kubernetes secret
- [ ] Success URL is `https://alphintra.com/subscription/success`
- [ ] Cancel URL is `https://alphintra.com/subscription/cancel`
- [ ] Auth service deployment includes all Stripe env vars
- [ ] Cloud Build completed successfully
- [ ] Test webhook shows 200 OK in Stripe dashboard
- [ ] Test subscription flow works end-to-end

---

## 🛡️ Security Best Practices

### For Production (Live Mode):

1. **Switch to Live Keys**:
   - Use `sk_live_...` instead of `sk_test_...`
   - Create new webhook endpoint for production
   - Use live price IDs

2. **Use Google Secret Manager** (More Secure):
```bash
# Store secrets in Google Secret Manager
echo -n "sk_live_YOUR_KEY" | gcloud secrets create stripe-api-key --data-file=-

# Update deployment to use Secret Manager
# (Requires Workload Identity setup)
```

3. **Enable HTTPS Only**:
   - Ensure all URLs use HTTPS
   - Stripe webhooks require HTTPS in production

4. **Monitor Webhook Logs**:
   - Set up alerts for failed webhooks
   - Monitor Stripe dashboard for webhook delivery status

---

## 🐛 Troubleshooting

### Webhook Returns 400
- **Cause**: Invalid signature or webhook secret mismatch
- **Fix**: Verify `STRIPE_WEBHOOK_SECRET` matches the signing secret in Stripe dashboard

### Webhook Returns 500
- **Cause**: Application error processing the event
- **Fix**: Check auth-service logs: `kubectl logs -l app=auth-service`

### Subscription Not Created
- **Cause**: Database connection issue or missing customer
- **Fix**: Check database connectivity and user exists in database

### Redirect URLs Not Working
- **Cause**: Frontend URLs mismatch
- **Fix**: Ensure frontend success/cancel pages exist at configured URLs

---

## 📚 Related Documentation

- [Stripe Webhooks Guide](https://stripe.com/docs/webhooks)
- [Stripe API Documentation](https://stripe.com/docs/api)
- [Stripe Testing](https://stripe.com/docs/testing)
- **Local files**:
  - `COMPLETE_SUBSCRIPTION_SYSTEM.md` - Full system overview
  - `SUBSCRIPTION_IMPLEMENTATION.md` - Backend implementation details
  - `STRIPE_SETUP.md` - Original setup guide

---

## ✅ Current Setup Status

Based on your screenshot:
- ✅ Production webhook configured: `https://api.alphintra.com/api/subscriptions/webhook`
- ✅ Listening to 6 events (correct!)
- ✅ Active status
- ⚠️ Sandbox webhook (localhost:8009) - Can be deleted if not needed for local testing

**Next Step**: Replace placeholder values in `secret.yaml` with your actual Stripe credentials and deploy! 🚀
