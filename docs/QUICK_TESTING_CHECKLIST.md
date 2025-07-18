# Quick Testing Checklist
## Alphintra Secure API Microservices Architecture

### 🚀 **Quick Start Testing (5 minutes)**

```bash
# 1. Deploy the complete system
cd /Users/usubithan/Documents/Alphintra
./scripts/deploy-secure-microservices.sh

# 2. Wait for deployment (2-3 minutes)
kubectl get pods -n alphintra -w

# 3. Quick validation
./scripts/validate-deployment.sh

# 4. Test API Gateway
curl http://localhost:30001/health

# 5. Test GraphQL
curl -X POST http://localhost:30001/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "query { __schema { types { name } } }"}'
```

### ✅ **Essential Tests Checklist**

#### Infrastructure Tests
- [ ] Cluster connectivity: `kubectl cluster-info`
- [ ] Namespaces exist: `kubectl get ns alphintra monitoring`
- [ ] Pods running: `kubectl get pods -n alphintra`
- [ ] Services accessible: `kubectl get svc -n alphintra`

#### Core Services Tests
- [ ] PostgreSQL: `kubectl exec -n alphintra deployment/postgresql-primary -- psql -U postgres -c "SELECT version();"`
- [ ] Redis: `kubectl exec -n alphintra deployment/redis-primary -- redis-cli ping`
- [ ] Eureka: Port-forward and check `http://localhost:8761`
- [ ] API Gateway: `curl http://localhost:30001/actuator/health`

#### Microservices Tests
```bash
services=("trading-service" "risk-service" "user-service" "no-code-service" "strategy-service" "broker-service" "notification-service" "graphql-gateway")

for service in "${services[@]}"; do
  echo "Testing $service..."
  kubectl get deployment $service -n alphintra
done
```

#### API Tests
- [ ] REST API: `curl http://localhost:30001/api/v1/trading/health`
- [ ] GraphQL Introspection: `curl -X POST http://localhost:30001/graphql -H "Content-Type: application/json" -d '{"query": "query { __schema { types { name } } }"}'`
- [ ] Gateway Routes: `curl http://localhost:30001/actuator/gateway/routes`

#### Monitoring Tests
- [ ] Prometheus: Port-forward and check `http://localhost:9090/targets`
- [ ] Grafana: Port-forward and check `http://localhost:3000` (admin/alphintra123)
- [ ] Jaeger: Port-forward and check `http://localhost:16686`

### 🔍 **Automated Testing Commands**

```bash
# Complete validation suite
./scripts/validate-deployment.sh

# End-to-end testing suite  
./scripts/test-microservices-e2e.sh

# Individual component tests
./scripts/test-microservices-e2e.sh gateway
./scripts/test-microservices-e2e.sh microservices
./scripts/test-microservices-e2e.sh graphql
./scripts/test-microservices-e2e.sh monitoring
```

### 🎯 **Success Criteria**

#### Deployment Success
- All pods in `Running` state
- All services have endpoints
- No `CrashLoopBackOff` or `Error` states
- HPA configured and working

#### Functional Success
- API Gateway responds on port 30001
- All microservices respond to health checks
- GraphQL introspection query works
- Service discovery shows all services registered

#### Performance Success
- API response time < 100ms
- All services start within 60 seconds
- No resource limit violations
- Database connections successful

### 🐛 **Quick Troubleshooting**

#### If Pods Won't Start
```bash
# Check pod status
kubectl describe pod <pod-name> -n alphintra

# Check logs
kubectl logs <pod-name> -n alphintra

# Common fixes
kubectl delete pod <pod-name> -n alphintra  # Force restart
```

#### If Services Not Accessible
```bash
# Check service endpoints
kubectl get endpoints -n alphintra

# Test internal connectivity
kubectl exec -n alphintra deployment/api-gateway -- curl http://trading-service:8080/health
```

#### If Database Issues
```bash
# Test PostgreSQL
kubectl exec -n alphintra deployment/postgresql-primary -- psql -U postgres -l

# Test Redis
kubectl exec -n alphintra deployment/redis-primary -- redis-cli info
```

### 📊 **Monitoring Quick Access**

```bash
# Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &
open http://localhost:9090

# Grafana  
kubectl port-forward -n monitoring svc/grafana 3000:3000 &
open http://localhost:3000

# Jaeger
kubectl port-forward -n monitoring svc/jaeger-query 16686:16686 &
open http://localhost:16686

# Kill all port forwards
pkill -f "kubectl port-forward"
```

### 🔥 **Load Testing (Optional)**

```bash
# Simple load test
ab -n 100 -c 10 http://localhost:30001/health

# GraphQL load test
echo '{"query": "query { users(limit: 5) { id username } }"}' > query.json
ab -n 50 -c 5 -p query.json -T application/json http://localhost:30001/graphql
```

### 📈 **Expected Results**

#### Successful Deployment
```
✅ All 45 validation checks passed
✅ 8 microservices running (2 replicas each)
✅ API Gateway routing to all services
✅ GraphQL federation working
✅ Monitoring stack operational
✅ 97%+ test success rate
```

#### Performance Benchmarks
- API Gateway health check: < 50ms
- GraphQL introspection: < 200ms
- Service discovery lookup: < 100ms
- Database query: < 10ms
- Inter-service call: < 150ms

### 🎉 **Production Readiness Sign-off**

When all these tests pass, your system is ready for production:

- [ ] ✅ Infrastructure deployed and validated
- [ ] ✅ All microservices healthy and responsive  
- [ ] ✅ API Gateway routing correctly
- [ ] ✅ Database connectivity working
- [ ] ✅ Monitoring and alerting operational
- [ ] ✅ Security policies enforced
- [ ] ✅ Performance benchmarks met
- [ ] ✅ End-to-end workflows tested

---

**🏁 Final Command to Verify Everything:**

```bash
./scripts/test-microservices-e2e.sh && echo "🎉 PRODUCTION READY!"
```