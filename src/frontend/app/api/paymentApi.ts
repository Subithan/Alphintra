// *** IMPORTANT: Verify this URL matches your marketplace service ***
const MARKETPLACE_API_URL = 'http://localhost:8012';

// Stripe Publishable Key - This is safe to expose in the frontend
const STRIPE_PUBLISHABLE_KEY = 
  process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || 
  'pk_test_51SJrdmI8b6luJNpeyPm1TkxA1ZJTolJ1AfcNvW8zeaLHdB2V81YyqbXQeVJNxzfEgiOtAOt3t3Yq6gxRbWgvNvbe00c3VIQ4Eu';

/**
 * Initiates the Stripe Checkout process for a given strategy.
 * @param strategyId The unique ID of the strategy to purchase.
 * @returns A promise that resolves to the Stripe Session ID for use with Stripe.js
 */
export async function initiateStripeCheckout(strategyId: string): Promise<string> {
  // NOTE: The frontend Modal must be updated to capture the user_email. Assuming a hardcoded 
  // placeholder for now based on the backend definition.
  const userEmail = "testuser@alphintra.com"; 
  
  // The backend endpoint now returns JSON with the checkout session ID
  const CHECKOUT_ENDPOINT = `${MARKETPLACE_API_URL}/strategies/${strategyId}/purchase?user_email=${encodeURIComponent(userEmail)}`;

  try {
    console.log('[Payment API] Initiating checkout for strategy:', strategyId);
    console.log('[Payment API] Calling endpoint:', CHECKOUT_ENDPOINT);
    
    const response = await fetch(CHECKOUT_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // *** You MUST pass the Authorization/JWT token here for the user initiating the purchase ***
      },
      body: JSON.stringify({}), 
    });

    console.log('[Payment API] Response status:', response.status);

    if (!response.ok) {
      // Check for application-specific errors from the Marketplace service
      const errorBody = await response.json();
      console.error('[Payment API] Error response:', errorBody);
      throw new Error(errorBody.detail || `Checkout API failed with status: ${response.status}`);
    }

    // Parse the JSON response to get the Stripe checkout session ID
    const data = await response.json();
    console.log('[Payment API] Received data:', data);
    
    if (!data.session_id) {
      console.error('[Payment API] No session_id in response:', data);
      throw new Error('No session ID received from server');
    }

    console.log('[Payment API] Returning session ID:', data.session_id);
    // Return the Stripe session ID (not the URL) for use with Stripe.js
    return data.session_id;

  } catch (error) {
    console.error('[Payment API] Exception caught:', error);
    throw error; // Re-throw the original error instead of wrapping it
  }
}

/**
 * Get the Stripe publishable key
 */
export function getStripePublishableKey(): string {
  return STRIPE_PUBLISHABLE_KEY;
}


