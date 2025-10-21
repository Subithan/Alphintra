const rawGatewayUrl = process.env.NEXT_PUBLIC_GATEWAY_URL ?? 'https://api.alphintra.com';
const rawAuthUrl = process.env.NEXT_PUBLIC_AUTH_URL ?? rawGatewayUrl;
const rawTradingUrl = process.env.NEXT_PUBLIC_TRADING_URL ?? rawGatewayUrl;

const normalize = (url: string) => {
  try {
    const parsed = new URL(url);
    const normalizedPath = parsed.pathname.endsWith('/') && parsed.pathname !== '/' ? parsed.pathname.slice(0, -1) : parsed.pathname;
    const httpBase = `${parsed.origin}${normalizedPath === '/' ? '' : normalizedPath}`;
    const wsProtocol = parsed.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsBase = `${wsProtocol}//${parsed.host}${normalizedPath === '/' ? '' : normalizedPath}`;
    return { httpBase, wsBase };
  } catch (error) {
    const fallbackHttp = 'https://api.alphintra.com';
    const fallbackWs = 'ws://34.172.120.224';
    return { httpBase: fallbackHttp, wsBase: fallbackWs };
  }
};

const join = (base: string, path = ''): string => {
  if (!path) {
    return base;
  }
  return `${base}${path.startsWith('/') ? path : `/${path}`}`;
};

const gateway = normalize(rawGatewayUrl);
const auth = normalize(rawAuthUrl);
const trading = normalize(rawTradingUrl);

export const gatewayHttpBaseUrl = gateway.httpBase;
export const gatewayWsBaseUrl = gateway.wsBase;
export const authHttpBaseUrl = auth.httpBase;
export const tradingHttpBaseUrl = trading.httpBase;

export const buildGatewayUrl = (path = ''): string => join(gatewayHttpBaseUrl, path);
export const buildGatewayWsUrl = (path = ''): string => join(gatewayWsBaseUrl, path);
export const buildAuthUrl = (path = ''): string => join(authHttpBaseUrl, path);
export const buildTradingUrl = (path = ''): string => join(tradingHttpBaseUrl, path);
