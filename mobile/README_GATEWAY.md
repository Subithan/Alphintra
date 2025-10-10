# Mobile Gateway Configuration

All mobile API calls should target the service gateway. Configure Expo with the public URL before starting Metro:

```bash
cp .env.example .env
# point to localhost when using `expo start --dev-client`
EXPO_PUBLIC_GATEWAY_URL=http://localhost:8080
```

The helper in `src/config/gateway.ts` exposes `buildGatewayUrl()` to keep all requests aligned with the web client.
