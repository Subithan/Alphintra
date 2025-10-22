import { NextRequest, NextResponse } from 'next/server';

const WALLET_SERVICE_URL =
  process.env.WALLET_SERVICE_URL ?? 'http://localhost:8011';

export async function POST(request: NextRequest) {
  try {
    const payload = await request.json();
    const environment =
      typeof payload?.environment === 'string'
        ? payload.environment
        : 'production';
    const requestBody = {
      ...payload,
      environment,
    };

    const response = await fetch(
      `${WALLET_SERVICE_URL}/binance/connect`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify(requestBody),
        cache: 'no-store',
      },
    );

    if (!response.ok) {
      let detail = response.statusText;
      try {
        const body = await response.json();
        detail = body?.detail ?? body?.error ?? detail;
      } catch {
        // ignore parsing error
      }

      return NextResponse.json(
        { error: detail ?? 'Failed to connect to Binance' },
        { status: response.status },
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Binance connection error:', error);
    return NextResponse.json(
      { error: 'Failed to reach wallet service' },
      { status: 502 },
    );
  }
}
