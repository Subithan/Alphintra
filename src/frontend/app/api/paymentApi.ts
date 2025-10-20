import { getUserId } from '@/lib/auth';

const MARKETPLACE_API_URL =
  process.env.NEXT_PUBLIC_MARKETPLACE_API_URL ?? 'http://localhost:8012';

export interface PurchasePayload {
  buyerId?: number;
  notes?: string;
}

export interface PurchaseResponse {
  id: number;
  strategy_id: number;
  buyer_id: number;
  status: string;
  notes?: string | null;
}

export async function purchaseStrategy(
  strategyId: string | number,
  payload: PurchasePayload = {}
): Promise<PurchaseResponse> {
  const buyerId = payload.buyerId ?? getUserId();
  if (!buyerId) {
    throw new Error('Unable to determine current user. Please sign in again.');
  }

  const endpoint = `${MARKETPLACE_API_URL}/strategies/${strategyId}/purchase`;

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      buyer_id: buyerId,
      notes: payload.notes ?? null,
    }),
  });

  if (!response.ok) {
    let message = `Purchase request failed with status ${response.status}`;
    try {
      const body = await response.json();
      if (body?.detail) {
        message = body.detail;
      }
    } catch {
      // ignore JSON parse errors; fall back to generic message
    }
    throw new Error(message);
  }

  return (await response.json()) as PurchaseResponse;
}
