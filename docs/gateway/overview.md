# Service Gateway Overview

The service gateway fronts Alphintra backend services, providing a single entry point with JWT verification, rate limiting, and observability hooks.

## Architecture

- **Stack**: Spring Boot 3.2, Spring Cloud Gateway (2023.0.1), Reactor Netty, Redis-backed rate limiting.
- **Security**: HMAC JWT validation aligned with the auth service secret; configurable public paths; correlation IDs injected on every request.
- **Resilience**: Retry and circuit breaker filters per route with `/ _fallback/unavailable` response for brownout conditions.
- **Rate limiting**: `RedisRateLimiter` using Memorystore/Redis (`GATEWAY_RATE_LIMIT_REPLENISH`, `GATEWAY_RATE_LIMIT_BURST`). Key resolver prefers JWT subject, falls back to client IP.
- **Observability**: JSON logs (`service=service-gateway`), actuator probes enabled for readiness/liveness metrics.

## Routing Table

| Route ID | Incoming Paths | Upstream URI (default) | Notes |
| --- | --- | --- | --- |
| `auth-service` | `/api/auth/**`, `/api/users/**`, `/api/kyc/**` | `http://auth-service.auth-service:8009` | `Cookie` header stripped to avoid leaking browser cookies. |
| `trading-engine` | `/api/trading/**`, `/api/orders/**` | `http://trading-engine.platform:8100` | Requires JWT. |
| `marketplace-service` | `/api/marketplace/**` | `http://marketplace-service.platform:8200` | |
| `graphql-service` | `/graphql/**` | `http://graphql-service.platform:8300` | Supports GraphQL queries and subscriptions. |
| `market-data-websocket` | `/ws/market/**` | `ws://market-data.platform:8082` | Gateway preserves host headers and negotiates WebSocket upgrades. |

Update environment-specific URIs via the `service-gateway-config` ConfigMap overlays (`infra/kubernetes/environments/*`).

## Configuration

Environment variables consumed by the deployment:

| Variable | Description |
| --- | --- |
| `GATEWAY_JWT_SECRET` | Base64-encoded HMAC secret shared with the auth service |
| `GATEWAY_RATE_LIMIT_REPLENISH`/`GATEWAY_RATE_LIMIT_BURST` | Rate limiter tokens per second and burst capacity |
| `AUTH_SERVICE_URI`, `TRADING_ENGINE_URI`, etc. | Upstream service URIs injected via ConfigMap |
| `MARKET_DATA_WS_URI` | Backend WebSocket endpoint |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` | Redis / Memorystore connection details |
| `GATEWAY_MAX_REQUEST_SIZE` | Request payload limit (default 10MB) |

## Deployment

- Base manifests: `infra/kubernetes/base/gateway` (Deployment, Service, ConfigMap, HPA, ServiceAccount).
- Overlays: `infra/kubernetes/environments/{dev,staging,prod}` adjust replicas, URIs, Redis hosts, and autoscaling thresholds.
- Docker image: `gcr.io/$PROJECT/alphintra/service-gateway:<tag>` built by `src/backend/service-gateway/cloudbuild.yaml`.
- Istio manifests: `infra/kubernetes/istio` defines the ingress `Gateway`, `VirtualService`, JWT policies, and DestinationRules.

Apply with:

```bash
kubectl apply -k infra/kubernetes/environments/dev
```

## Local Development

```bash
cd src/backend/service-gateway
export GATEWAY_JWT_SECRET=$(openssl rand -base64 64)
export AUTH_SERVICE_URI=http://localhost:8009
export REDIS_HOST=localhost
redis-server --daemonize yes
mvn spring-boot:run
```

### Load Testing

Use the K6 script in `tests/performance/gateway-load.js`:

```bash
k6 run tests/performance/gateway-load.js \
  --env GATEWAY_URL=http://localhost:8080 \
  --env JWT_TOKEN=$(./scripts/generate-test-jwt.sh)
```

Tune `VUS` and `DURATION` via environment variables to simulate expected traffic.

## Future Enhancements

- Integrate OpenTelemetry exporter for request tracing.
- Propagate JWT claims to downstream gRPC services via `X-Jwt-Claims` header (redaction pipeline).
- Configure custom error responses per route (JSON body, correlation ID echo).
- Expand Grafana dashboards with Redis hit rate and Istio mTLS success metrics.
