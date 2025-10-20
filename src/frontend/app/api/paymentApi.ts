// Marketplace API base URL (override with NEXT_PUBLIC_MARKETPLACE_API_URL if needed)
const MARKETPLACE_API_URL =
  process.env.NEXT_PUBLIC_MARKETPLACE_API_URL ?? 'http://localhost:8012';

// Stripe Publishable Key - This is safe to expose in the frontend
const STRIPE_PUBLISHABLE_KEY = 
  process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || 
  'pk_test_51SJrdmI8b6luJNpeyPm1TkxA1ZJTolJ1AfcNvW8zeaLHdB2V81YyqbXQeVJNxzfEgiOtAOt3t3Yq6gxRbWgvNvbe00c3VIQ4Eu';

/**
 * Calls the marketplace service to record a purchase for a strategy.
 * The backend will create an order with status `paid` and increment subscriber count.
 */
export async function purchaseStrategy(
  strategyId: string | number,
  payload: PurchasePayload
): Promise<PurchaseResponse> {
  const endpoint = `${MARKETPLACE_API_URL}/strategies/${strategyId}/purchase`;

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      buyer_id: payload.buyerId,
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
