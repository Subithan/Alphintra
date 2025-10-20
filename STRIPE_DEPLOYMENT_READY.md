# ✅ Stripe Integration - READY TO DEPLOY!

## 🎉 Configuration Complete

All Stripe credentials have been successfully configured and are ready for deployment to GCP.

---

## 📋 What Was Configured

### ✅ Backend (Auth Service)

**File: `infra/kubernetes/base/auth-service/secret.yaml`**
- ✅ **Stripe API Key**: `sk_test_51SJrdmI8b6luJNpe...` (configured)
- ✅ **Webhook Secret**: `whsec_q4Y6z8A3SkCIQCUEHwS2CjgmNAtRT6nv` (configured)
- ✅ **Price ID**: `price_1SJsePI8b6luJNpeBVzbXtCJ` (configured for all tiers)

**File: `infra/kubernetes/base/auth-service/configmap.yaml`**
- ✅ **Success URL**: `https://alphintra.com/subscription/success`
- ✅ **Cancel URL**: `https://alphintra.com/subscription/cancel`

**File: `infra/kubernetes/base/auth-service/deployment.yaml`**
- ✅ All Stripe environment variables mapped to pods

---

### ✅ Frontend

**File: `src/frontend/.env.example`**
- ✅ **Publishable Key**: `pk_test_51SJrdmI8b6luJNpey...` (configured)
- ✅ **Price IDs**: All three tiers configured

**File: `src/frontend/app/api/paymentApi.ts`**
- ✅ Updated to use environment variable for Stripe key
- ✅ Fallback to your actual key if env var not set

---

## 🚀 Ready to Deploy

### Step 1: Deploy Backend to GCP

```bash
# Option A: Deploy via Cloud Build (Recommended)
cd src/backend/auth-service
bash build.sh

# Option B: Deploy Kubernetes configs directly
cd infra/kubernetes/base/auth-service
kubectl apply -f secret.yaml
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
```

### Step 2: Verify Backend Deployment

```bash
# Check if pods are running
kubectl get pods -l app=auth-service

# Watch the logs for successful startup
kubectl logs -l app=auth-service --follow

# Look for these messages:
# ✅ "Stripe initialized successfully"
# ✅ "Started AuthServiceApplication"
```

### Step 3: Test Webhook Endpoint

From Stripe Dashboard:
1. Go to **Developers** → **Webhooks**
2. Click on `https://api.alphintra.com/api/subscriptions/webhook`
3. Click **Send test webhook**
4. Select `checkout.session.completed`
5. Should return **200 OK** ✅

### Step 4: Deploy Frontend (if needed)

If your frontend is also deployed via GCP:

```bash
cd src/frontend

# Create .env.local for local testing
cat > .env.local << 'EOF'
NEXT_PUBLIC_GATEWAY_URL=https://api.alphintra.com
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_51SJrdmI8b6luJNpeyPm1TkxA1ZJTolJ1AfcNvW8zeaLHdB2V81YyqbXQeVJNxzfEgiOtAOt3t3Yq6gxRbWgvNvbe00c3VIQ4Eu
NEXT_PUBLIC_STRIPE_PRICE_ID_BASIC=price_1SJsePI8b6luJNpeBVzbXtCJ
NEXT_PUBLIC_STRIPE_PRICE_ID_PRO=price_1SJsePI8b6luJNpeBVzbXtCJ
NEXT_PUBLIC_STRIPE_PRICE_ID_ENTERPRISE=price_1SJsePI8b6luJNpeBVzbXtCJ
EOF

# Build and deploy
npm run build
# (Follow your frontend deployment process)
```

---

## 🧪 Testing Checklist

### Backend Tests

- [ ] **Health Check**: `curl https://api.alphintra.com/actuator/health`
- [ ] **Webhook Endpoint**: Send test webhook from Stripe dashboard
- [ ] **Create Checkout Session**: 
  ```bash
  curl -X POST https://api.alphintra.com/api/subscriptions/create-checkout-session \
    -H "Authorization: Bearer YOUR_JWT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"priceId":"price_1SJsePI8b6luJNpeBVzbXtCJ","planName":"pro"}'
  ```

### Frontend Tests

- [ ] Visit subscription page: `https://alphintra.com/subscription`
- [ ] Click on a pricing plan
- [ ] Verify redirect to Stripe Checkout
- [ ] Complete test payment with card `4242 4242 4242 4242`
- [ ] Verify redirect to success page
- [ ] Check subscription status in dashboard

### End-to-End Test

1. **Register a new user** or login
2. **Navigate to subscription page**
3. **Click "Subscribe" on Pro plan**
4. **Complete Stripe checkout** (test mode)
5. **Verify webhook received** in backend logs:
   ```
   Processing Stripe webhook event: checkout.session.completed
   Subscription saved: <subscription-id>
   ```
6. **Check user subscription status** via API or frontend

---

## 📊 Stripe Configuration Summary

| Setting | Value | Location |
|---------|-------|----------|
| **API Key** | `sk_test_51SJrdmI8b6luJNpe...` | Kubernetes Secret |
| **Webhook Secret** | `whsec_q4Y6z8A3SkCIQCUEHwS2CjgmNAtRT6nv` | Kubernetes Secret |
| **Publishable Key** | `pk_test_51SJrdmI8b6luJNpey...` | Frontend Env Var |
| **Price ID (All Tiers)** | `price_1SJsePI8b6luJNpeBVzbXtCJ` | Both Backend & Frontend |
| **Webhook URL** | `https://api.alphintra.com/api/subscriptions/webhook` | Stripe Dashboard |
| **Success URL** | `https://alphintra.com/subscription/success` | ConfigMap |
| **Cancel URL** | `https://alphintra.com/subscription/cancel` | ConfigMap |

---

## 📝 Notes

### Single Price ID
You currently have **one price ID** configured for all three tiers (Basic, Pro, Enterprise). This means:
- All plans will use the same pricing
- You may want to create separate products/prices in Stripe for each tier
- Update the price IDs in both backend and frontend when you create them

### Creating Multiple Price Tiers in Stripe

1. Go to **Products** in Stripe Dashboard
2. Create three products:
   - **Basic**: e.g., $9.99/month → Copy `price_id`
   - **Pro**: e.g., $19.99/month → Copy `price_id`
   - **Enterprise**: e.g., $49.99/month → Copy `price_id`
3. Update **`secret.yaml`** with individual price IDs
4. Update **`.env.local`** with individual price IDs
5. Redeploy both backend and frontend

---

## 🔒 Security Reminders

- ✅ **Secret keys** are in Kubernetes Secrets (not committed to git)
- ✅ **Publishable keys** are safe to expose (public by design)
- ⚠️ **Never commit** `.env.local` to git (add to `.gitignore`)
- ⚠️ **Webhook secret** must match exactly between Stripe and your config
- 🔐 **For production**: Use `sk_live_` and `pk_live_` keys

---

## 🐛 Troubleshooting

### Webhook Returns 400
**Symptom**: Stripe webhook test returns 400 Bad Request

**Fix**: 
```bash
# Verify webhook secret matches
kubectl get secret auth-service-secrets -o jsonpath='{.data.STRIPE_WEBHOOK_SECRET}' | base64 -d
# Should output: whsec_q4Y6z8A3SkCIQCUEHwS2CjgmNAtRT6nv
```

### Checkout Session Creation Fails
**Symptom**: Frontend receives error when clicking subscribe

**Check**:
1. JWT token is valid and included in request
2. Stripe API key is correct
3. Backend logs: `kubectl logs -l app=auth-service --tail=100`

### Webhook Not Received
**Symptom**: Payment succeeds but subscription not created

**Check**:
1. Webhook endpoint is accessible: `curl https://api.alphintra.com/api/subscriptions/webhook`
2. Firewall/ingress allows POST to `/api/subscriptions/webhook`
3. Stripe dashboard shows webhook delivery status

---

## 📚 Related Documentation

- **Setup Guide**: `src/backend/auth-service/STRIPE_GCP_SETUP.md`
- **Complete System**: `COMPLETE_SUBSCRIPTION_SYSTEM.md`
- **Implementation Details**: `src/backend/auth-service/SUBSCRIPTION_IMPLEMENTATION.md`
- **Stripe Docs**: https://stripe.com/docs

---

## ✅ Deployment Status

- [x] Stripe credentials configured
- [x] Kubernetes secrets updated
- [x] Kubernetes configmaps updated
- [x] Deployment manifest updated
- [x] Frontend environment configured
- [ ] **Backend deployed to GCP** ⬅️ Next step!
- [ ] Webhook tested
- [ ] End-to-end test completed

---

## 🎯 Next Action

**Deploy the auth service to GCP:**

```bash
cd src/backend/auth-service
bash build.sh
```

Then verify the deployment and test the webhook! 🚀
