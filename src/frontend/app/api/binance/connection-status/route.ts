import { NextResponse } from 'next/server';

const WALLET_SERVICE_URL =
  process.env.WALLET_SERVICE_URL ?? 'http://localhost:8011';

export async function GET() {
  try {
    const response = await fetch(
      `${WALLET_SERVICE_URL}/binance/connection-status`,
      {
        method: 'GET',
        headers: { Accept: 'application/json' },
        cache: 'no-store',
      },
    );

    if (!response.ok) {
      let detail = response.statusText;
      try {
        const body = await response.json();
        detail = body?.detail ?? body?.error ?? detail;
      } catch {
        // ignore parse errors
      }

      return NextResponse.json(
        { error: detail ?? 'Failed to fetch connection status' },
        { status: response.status },
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error checking connection status:', error);
    return NextResponse.json(
      { error: 'Failed to reach wallet service' },
      { status: 502 },
    );
  }
}
