# 🔧 Stripe Webhook 404 Fix

## ❌ Problem Found

Your Stripe webhook endpoint was returning **404 Not Found** because the **service-gateway** wasn't routing `/api/subscriptions/**` requests to the auth-service.

### Root Cause:
```yaml
# OLD routing - Missing subscription routes
predicates:
  - Path=/api/auth/**, /api/users/**, /api/kyc/**  ❌
```

---

## ✅ Fix Applied

Updated `src/backend/service-gateway/src/main/resources/application.yml`:

```yaml
# NEW routing - Added subscription routes
predicates:
  - Path=/api/auth/**, /api/users/**, /api/kyc/**, /api/subscriptions/**  ✅
```

---

## 🚀 Deploy the Fix

### Step 1: Build and Deploy Service Gateway

```bash
cd src/backend/service-gateway
bash build.sh
```

Wait ~5-10 minutes for deployment to complete.

---

### Step 2: Verify the Fix

After deployment completes, test the webhook endpoint:

```bash
curl -X POST https://api.alphintra.com/api/subscriptions/webhook \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected result:**
```
Webhook error: Invalid signature
```

✅ This means **200 or 400 status** (not 404!) - the endpoint is now reachable!

---

### Step 3: Test from Stripe Dashboard

1. Go to Stripe Dashboard → **Developers** → **Webhooks**
2. Click your webhook endpoint: `https://api.alphintra.com/api/subscriptions/webhook`
3. Look for the **"Testing"** tab or **"Send test webhook"** button
4. If not available, create a real test checkout session (better test anyway!)

---

## 🧪 Alternative: Create Real Test Checkout Session

This is actually the best way to test:

### 1. Get a JWT Token

```bash
# Register or login to get a JWT token
curl -X POST https://api.alphintra.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

### 2. Create Checkout Session

```bash
curl -X POST https://api.alphintra.com/api/subscriptions/create-checkout-session \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "priceId": "price_1SJsePI8b6luJNpeBVzbXtCJ",
    "planName": "pro"
  }'
```

### 3. Complete Checkout

Open the returned URL in browser and complete payment with test card:
- **Card**: `4242 4242 4242 4242`
- **Expiry**: Any future date
- **CVC**: Any 3 digits

### 4. Webhook Fires Automatically

Stripe will send the `checkout.session.completed` webhook to your endpoint! ✅

---

## 📊 Deployment Status

- [x] Fixed service-gateway routing configuration
- [ ] **Deploy service-gateway** ⬅️ **DO THIS NOW!**
- [ ] Test webhook endpoint (should return 400, not 404)
- [ ] Verify in Stripe Dashboard
- [ ] Create test checkout session
- [ ] Complete end-to-end test

---

## 🎯 Quick Commands

```bash
# 1. Deploy the gateway fix
cd src/backend/service-gateway
bash build.sh

# 2. Wait 5-10 minutes, then test
curl -X POST https://api.alphintra.com/api/subscriptions/webhook \
  -H "Content-Type: application/json" \
  -d '{}'

# 3. Should see "Invalid signature" (not 404) ✅
```

---

## ✅ Success Criteria

After deploying the gateway:
- ✅ Webhook endpoint returns **400 Bad Request** "Invalid signature" (not 404)
- ✅ Health check still works: `https://api.alphintra.com/actuator/health`
- ✅ Stripe test webhook returns **200 OK**
- ✅ Real checkout flow triggers webhook successfully

---

**Next Step: Deploy the service-gateway now!** 🚀
