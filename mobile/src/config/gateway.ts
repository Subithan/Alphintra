const rawGatewayUrl = process.env.EXPO_PUBLIC_GATEWAY_URL ?? 'http://localhost:8080';

export const gatewayHttpUrl = rawGatewayUrl.replace(/\/+$/, '');

export const buildGatewayUrl = (path = ''): string =>
  `${gatewayHttpUrl}${path.startsWith('/') ? path : `/${path}`}`;
