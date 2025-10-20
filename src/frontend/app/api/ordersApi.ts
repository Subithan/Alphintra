import { getUserId } from '@/lib/auth';

const MARKETPLACE_API_URL =
  process.env.NEXT_PUBLIC_MARKETPLACE_API_URL ?? 'http://api.alphintra.com';

export interface PurchasedStrategy {
  orderId: number;
  status: string;
  notes?: string | null;
  strategy: {
    id: number;
    name: string;
    description: string;
    priceCents: number;
    subscriberCount: number;
  };
}

interface RawOrder {
  id: number;
  strategy_id: number;
  buyer_id: number;
  status: string;
  notes?: string | null;
  strategy: {
    id: number;
    name: string;
    price_cents: number;
    description: string;
    subscriber_count: number;
  };
}

export async function fetchOrdersForCurrentUser(): Promise<PurchasedStrategy[]> {
  const userId = getUserId();
  if (!userId) {
    throw new Error('User is not authenticated.');
  }

  const response = await fetch(
    `${MARKETPLACE_API_URL}/orders/by-buyer/${userId}`,
    {
      headers: {
        Accept: 'application/json',
      },
    }
  );

  if (!response.ok) {
    let message = `Failed to load purchases (${response.status})`;
    try {
      const body = await response.json();
      if (body?.detail) {
        message = body.detail;
      }
    } catch {
      // ignore parsing failure
    }
    throw new Error(message);
  }

  const data = (await response.json()) as RawOrder[];

  return data.map((order) => ({
    orderId: order.id,
    status: order.status,
    notes: order.notes,
    strategy: {
      id: order.strategy.id,
      name: order.strategy.name,
      description: order.strategy.description,
      priceCents: order.strategy.price_cents,
      subscriberCount: order.strategy.subscriber_count,
    },
  }));
}
