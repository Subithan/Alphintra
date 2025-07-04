# Kubernetes Debugging Guide

## Table of Contents
- [Pod Issues](#pod-issues)
- [Service Issues](#service-issues)
- [Network Issues](#network-issues)
- [Resource Issues](#resource-issues)
- [Application Issues](#application-issues)
- [Common Error Patterns](#common-error-patterns)

---

## Pod Issues

### Pod Won't Start

#### Check Pod Status
```bash
kubectl get pods -n alphintra
kubectl describe pod <pod-name> -n alphintra
```

#### Common Causes & Solutions

**ImagePullBackOff / ErrImagePull**
```bash
# Check if image exists locally
docker images | grep no-code-service

# Import image to k3d cluster
k3d image import no-code-service:latest -c alphintra-dev

# Verify image policy
kubectl get deployment no-code-service -n alphintra -o yaml | grep imagePullPolicy
```

**CrashLoopBackOff**
```bash
# Check container logs
kubectl logs pod/<pod-name> -n alphintra
kubectl logs pod/<pod-name> -n alphintra --previous

# Check if health checks are failing
kubectl describe pod <pod-name> -n alphintra | grep -A 10 "Liveness\|Readiness"

# Disable health checks temporarily
kubectl patch deployment no-code-service -n alphintra -p '{"spec":{"template":{"spec":{"containers":[{"name":"no-code-service","livenessProbe":null,"readinessProbe":null}]}}}}'
```

**Pending State**
```bash
# Check resource availability
kubectl describe pod <pod-name> -n alphintra | grep Events -A 20

# Check node resources
kubectl top nodes
kubectl describe nodes

# Check if PVCs are bound
kubectl get pvc -n alphintra
```

### Pod Running but Not Ready

#### Check Readiness Probe
```bash
# View probe configuration
kubectl describe pod <pod-name> -n alphintra | grep -A 5 "Readiness"

# Test readiness endpoint manually
kubectl exec pod/<pod-name> -n alphintra -- curl http://localhost:8000/health

# Check probe logs
kubectl logs pod/<pod-name> -n alphintra | grep -i health
```

#### Check Application Startup
```bash
# View application logs
kubectl logs -f pod/<pod-name> -n alphintra

# Check if application is listening on correct port
kubectl exec pod/<pod-name> -n alphintra -- netstat -tulpn
kubectl exec pod/<pod-name> -n alphintra -- ss -tulpn
```

---

## Service Issues

### Service Not Accessible

#### Check Service Configuration
```bash
# Verify service exists
kubectl get svc -n alphintra

# Check service details
kubectl describe svc no-code-service -n alphintra

# Verify endpoints
kubectl get endpoints no-code-service -n alphintra
```

#### Check Selector Matching
```bash
# Compare service selector with pod labels
kubectl get svc no-code-service -n alphintra -o yaml | grep -A 5 selector
kubectl get pods -n alphintra -l app=no-code-service --show-labels
```

#### Test Service Connectivity
```bash
# Test from within cluster
kubectl run test-pod --image=curlimages/curl -n alphintra --rm -it -- sh
# Inside pod:
curl http://no-code-service:8000/health

# Test via port forward
kubectl port-forward svc/no-code-service 8080:8000 -n alphintra
curl http://localhost:8080/health
```

### Ingress Issues

#### Check Ingress Status
```bash
# Check ingress configuration
kubectl get ingress -n alphintra
kubectl describe ingress no-code-service-ingress -n alphintra

# Check ingress controller
kubectl get pods -n ingress-nginx
```

#### Test Ingress Rules
```bash
# Add to /etc/hosts if using custom domain
echo "127.0.0.1 no-code-service.local" >> /etc/hosts

# Test ingress endpoint
curl -H "Host: no-code-service.local" http://localhost/health
curl http://no-code-service.local/health
```

---

## Network Issues

### DNS Resolution Problems

#### Test DNS Resolution
```bash
# From within a pod
kubectl exec -it deployment/no-code-service -n alphintra -- nslookup auth-service
kubectl exec -it deployment/no-code-service -n alphintra -- nslookup auth-service.alphintra.svc.cluster.local

# Check CoreDNS
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns
```

#### Check Network Policies
```bash
# List network policies
kubectl get networkpolicies -n alphintra

# Test connectivity between pods
kubectl exec -it deployment/no-code-service -n alphintra -- curl http://auth-service:8000/health
```

### Port Connectivity Issues

#### Check Port Binding
```bash
# Verify service is listening on correct port
kubectl exec deployment/no-code-service -n alphintra -- netstat -tulpn | grep 8000

# Check if port is accessible from pod
kubectl exec deployment/no-code-service -n alphintra -- curl http://localhost:8000/health
```

#### Test Inter-Service Communication
```bash
# Create debug pod for testing
kubectl run debug-pod --image=nicolaka/netshoot -n alphintra --rm -it

# Inside debug pod, test connectivity
curl http://no-code-service:8000/health
curl http://auth-service:8000/health
telnet no-code-service 8000
```

---

## Resource Issues

### Memory Issues

#### Check Memory Usage
```bash
# Check current usage
kubectl top pods -n alphintra

# Check memory limits
kubectl describe pod <pod-name> -n alphintra | grep -A 10 "Limits\|Requests"

# Check for OOMKilled
kubectl describe pod <pod-name> -n alphintra | grep -i oom
```

#### Monitor Memory Over Time
```bash
# Watch resource usage
watch kubectl top pods -n alphintra

# Check historical events
kubectl get events -n alphintra --sort-by='.lastTimestamp' | grep -i memory
```

### CPU Issues

#### Check CPU Usage
```bash
# Current CPU usage
kubectl top pods -n alphintra

# Check CPU throttling
kubectl describe pod <pod-name> -n alphintra | grep -i cpu
```

#### Adjust Resource Limits
```bash
# Increase memory limit
kubectl patch deployment no-code-service -n alphintra -p '{"spec":{"template":{"spec":{"containers":[{"name":"no-code-service","resources":{"limits":{"memory":"1Gi","cpu":"1000m"}}}]}}}}'

# Remove resource limits temporarily
kubectl patch deployment no-code-service -n alphintra -p '{"spec":{"template":{"spec":{"containers":[{"name":"no-code-service","resources":null}]}}}}'
```

### Storage Issues

#### Check Persistent Volumes
```bash
# Check PVC status
kubectl get pvc -n alphintra

# Check PV status
kubectl get pv

# Check storage events
kubectl get events -n alphintra | grep -i volume
```

---

## Application Issues

### Database Connection Issues

#### Check Database Connectivity
```bash
# Test database connection from pod
kubectl exec deployment/no-code-service -n alphintra -- python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://alphintra:alphintra@alphintra-postgres:5432/alphintra')
    print('Database connection successful')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

#### Check Database Service
```bash
# Check if database pod is running
kubectl get pods -n alphintra | grep postgres

# Check database service
kubectl get svc -n alphintra | grep postgres

# Test database port
kubectl exec deployment/no-code-service -n alphintra -- telnet alphintra-postgres 5432
```

### Redis Connection Issues

#### Test Redis Connectivity
```bash
# Test Redis connection
kubectl exec deployment/no-code-service -n alphintra -- python -c "
import redis
try:
    r = redis.Redis(host='alphintra-redis', port=6379, db=0)
    r.ping()
    print('Redis connection successful')
except Exception as e:
    print(f'Redis connection failed: {e}')
"
```

### API Issues

#### Test API Endpoints
```bash
# Port forward and test
kubectl port-forward svc/no-code-service 8080:8000 -n alphintra &

# Test various endpoints
curl http://localhost:8080/health
curl http://localhost:8080/docs
curl http://localhost:8080/openapi.json

# Kill port forward
pkill -f "kubectl port-forward"
```

#### Check API Logs
```bash
# Filter API-specific logs
kubectl logs -f deployment/no-code-service -n alphintra | grep -E "(ERROR|WARN|Exception)"

# Check for specific error patterns
kubectl logs deployment/no-code-service -n alphintra | grep -E "(500|400|401|403|404)"
```

---

## Common Error Patterns

### Error: "connection refused"
```bash
# Check if service is running
kubectl get pods -n alphintra -l app=no-code-service

# Check if port is correct
kubectl get svc no-code-service -n alphintra -o yaml | grep port

# Test port binding in pod
kubectl exec deployment/no-code-service -n alphintra -- netstat -tulpn
```

### Error: "no such host"
```bash
# Check DNS resolution
kubectl exec deployment/no-code-service -n alphintra -- nslookup auth-service

# Check service name spelling
kubectl get svc -n alphintra

# Try FQDN
kubectl exec deployment/no-code-service -n alphintra -- nslookup auth-service.alphintra.svc.cluster.local
```

### Error: "ImagePullBackOff"
```bash
# List local images
docker images

# Import image to k3d
k3d image import <image-name>:latest -c alphintra-dev

# Check image name in deployment
kubectl get deployment <deployment-name> -n alphintra -o yaml | grep image
```

### Error: "CrashLoopBackOff"
```bash
# Check logs from crashed container
kubectl logs pod/<pod-name> -n alphintra --previous

# Check if health checks are too aggressive
kubectl describe pod <pod-name> -n alphintra | grep -A 10 "Liveness\|Readiness"

# Temporarily disable health checks for debugging
kubectl patch deployment no-code-service -n alphintra -p '{"spec":{"template":{"spec":{"containers":[{"name":"no-code-service","livenessProbe":null,"readinessProbe":null}]}}}}'
```

## Debugging Tools

### Essential Commands
```bash
# Create debugging pod
kubectl run debug --image=nicolaka/netshoot -n alphintra --rm -it

# Copy files from pod
kubectl cp alphintra/<pod-name>:/app/logs ./logs

# Execute commands in pod
kubectl exec -it deployment/no-code-service -n alphintra -- /bin/bash
```

### Useful Docker Images for Debugging
- `nicolaka/netshoot` - Network debugging tools
- `curlimages/curl` - Simple HTTP testing
- `busybox` - Basic Unix utilities
- `alpine` - Minimal Linux with package manager

### Logging and Monitoring
```bash
# Aggregate logs from all containers
kubectl logs -f -l app=no-code-service -n alphintra --all-containers

# Watch events in real-time
kubectl get events -n alphintra -w

# Monitor resource usage
watch kubectl top pods -n alphintra
```

---

## Quick Debugging Checklist

When a service isn't working:

1. **Check Pod Status**
   ```bash
   kubectl get pods -n alphintra
   kubectl describe pod <pod-name> -n alphintra
   ```

2. **Check Logs**
   ```bash
   kubectl logs deployment/<service-name> -n alphintra
   ```

3. **Check Service**
   ```bash
   kubectl get svc -n alphintra
   kubectl get endpoints <service-name> -n alphintra
   ```

4. **Test Connectivity**
   ```bash
   kubectl port-forward svc/<service-name> 8080:8000 -n alphintra
   curl http://localhost:8080/health
   ```

5. **Check Resources**
   ```bash
   kubectl top pods -n alphintra
   kubectl describe node
   ```

6. **Check Events**
   ```bash
   kubectl get events -n alphintra --sort-by='.lastTimestamp'
   ```

This debugging guide should help you quickly identify and resolve common Kubernetes issues in your Alphintra cluster.