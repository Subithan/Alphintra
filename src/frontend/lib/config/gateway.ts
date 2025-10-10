const rawGatewayUrl = process.env.NEXT_PUBLIC_GATEWAY_URL ?? 'http://localhost:8080';

const normalize = () => {
  try {
    const parsed = new URL(rawGatewayUrl);
    const normalizedPath = parsed.pathname.endsWith('/') && parsed.pathname !== '/' ? parsed.pathname.slice(0, -1) : parsed.pathname;
    const httpBase = `${parsed.origin}${normalizedPath === '/' ? '' : normalizedPath}`;
    const wsProtocol = parsed.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsBase = `${wsProtocol}//${parsed.host}${normalizedPath === '/' ? '' : normalizedPath}`;
    return { httpBase, wsBase };
  } catch (error) {
    const fallbackHttp = 'http://localhost:8080';
    const fallbackWs = 'ws://localhost:8080';
    return { httpBase: fallbackHttp, wsBase: fallbackWs };
  }
};

const join = (base: string, path = ''): string => {
  if (!path) {
    return base;
  }
  return `${base}${path.startsWith('/') ? path : `/${path}`}`;
};

const { httpBase, wsBase } = normalize();

export const gatewayHttpBaseUrl = httpBase;
export const gatewayWsBaseUrl = wsBase;

export const buildGatewayUrl = (path = ''): string => join(gatewayHttpBaseUrl, path);
export const buildGatewayWsUrl = (path = ''): string => join(gatewayWsBaseUrl, path);
