import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: __ENV.VUS ? parseInt(__ENV.VUS, 10) : 25,
  duration: __ENV.DURATION || '1m',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};

const BASE_URL = __ENV.GATEWAY_URL || 'https://api.alphintra.com';
const TOKEN = __ENV.JWT_TOKEN || '';

export default function () {
  const headers = TOKEN
    ? { Authorization: `Bearer ${TOKEN}`, 'Content-Type': 'application/json' }
    : { 'Content-Type': 'application/json' };

  const res = http.get(`${BASE_URL}/api/trading/orders`, { headers });
  check(res, {
    'status is 200 or 401': (r) => r.status === 200 || r.status === 401,
  });

  sleep(1);
}
