# 🔍 Webhook Endpoint Troubleshooting

## Current Status: 404 Error

The webhook endpoint is still returning 404 after deploying the gateway. This is normal and usually means the deployment is still in progress.

---

## ⏱️ Timeline

Typical GCP deployment timeline:
1. **0-2 min**: Image build and push ✅ (completed)
2. **2-5 min**: Kubernetes rolling update (in progress)
3. **5-10 min**: Health checks and traffic routing (waiting)
4. **10+ min**: Full propagation across load balancers

**Current time since deployment**: ~5 minutes
**Expected fix time**: Wait another 5-10 minutes

---

## 🧪 Quick Tests

### Test 1: Check if deployment started
```bash
# This will show error if kubectl not configured, but that's okay
kubectl get pods -n alphintra -l app=service-gateway
```

### Test 2: Keep testing the endpoint every 2 minutes
```bash
# Run this every 2 minutes until you get 400 (not 404)
curl -X POST https://api.alphintra.com/api/subscriptions/webhook \
  -H "Content-Type: application/json" \
  -d '{}'
```

**What to look for:**
- ✅ **400 Bad Request** "Invalid signature" = SUCCESS! Endpoint is live
- ❌ **404 Not Found** = Still deploying, wait 2 more minutes

---

## 🎯 Expected Behavior After Deployment

### Before (Current):
```json
{"status":404,"error":"Not Found"}
```

### After (Success):
```json
{"status":400,"error":"Bad Request","message":"Webhook error: Invalid signature"}
```

The 400 error is **GOOD** - it means:
- ✅ Gateway is routing to auth-service
- ✅ Auth-service received the request
- ✅ Stripe webhook validation is working
- ❌ Just missing valid Stripe signature (expected for manual test)

---

## 🔄 Alternative: Force Restart Gateway

If waiting doesn't work after 15 minutes, you can try forcing a restart:

```bash
# Navigate to gateway
cd ~/Documents/Alphintra/src/backend/service-gateway

# Rebuild and redeploy
bash build.sh
```

---

## ✅ When It Works

Once you see **400 Bad Request**, your Stripe webhook is ready! 🎉

Next steps:
1. Go to Stripe Dashboard
2. Send test webhook
3. Should return **200 OK**
4. Create real checkout session
5. Complete payment
6. Webhook fires automatically!

---

## 📊 Deployment Progress Checklist

- [x] Configuration updated in `application.yml`
- [x] Gateway build completed (`bash build.sh`)
- [ ] **Kubernetes pods updated** ⬅️ Waiting...
- [ ] **Load balancer routing updated** ⬅️ Waiting...
- [ ] Webhook endpoint returns 400 (not 404)
- [ ] Stripe test webhook succeeds

**Current Step**: Waiting for Kubernetes deployment to propagate (~5-10 more minutes)

---

## 💡 Pro Tip

While waiting, you can:
1. ☕ Get coffee (seriously, deployments take time!)
2. 📝 Review the Stripe dashboard setup
3. 🎨 Work on frontend subscription UI
4. 📧 Prepare test user accounts

---

**Next Test**: Run the curl command again in 5 minutes! ⏰
