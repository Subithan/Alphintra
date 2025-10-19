// *** IMPORTANT: Verify this URL matches your marketplace service ***
const MARKETPLACE_API_URL = 'http://localhost:8012';

/**
 * Initiates the Stripe Checkout process for a given strategy.
 * @param strategyId The unique ID of the strategy to purchase.
 * @returns A promise that resolves to the Stripe Session URL for immediate client-side redirection.
 */
export async function initiateStripeCheckout(strategyId: string): Promise<string> {
  // NOTE: The frontend Modal must be updated to capture the user_email. Assuming a hardcoded 
  // placeholder for now based on the backend definition.
  const userEmail = "testuser@alphintra.com"; 
  
  // The backend endpoint now returns JSON with the checkout URL instead of redirecting
  const CHECKOUT_ENDPOINT = `${MARKETPLACE_API_URL}/strategies/${strategyId}/purchase?user_email=${encodeURIComponent(userEmail)}`;

  try {
    const response = await fetch(CHECKOUT_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // *** You MUST pass the Authorization/JWT token here for the user initiating the purchase ***
      },
      body: JSON.stringify({}), 
    });

    if (!response.ok) {
      // Check for application-specific errors from the Marketplace service
      const errorBody = await response.json();
      throw new Error(errorBody.detail || `Checkout API failed with status: ${response.status}`);
    }

    // Parse the JSON response to get the Stripe checkout URL
    const data = await response.json();
    
    if (!data.checkout_url) {
      throw new Error('No checkout URL received from server');
    }

    // Return the Stripe checkout URL for the frontend to redirect to
    return data.checkout_url;

  } catch (error) {
    console.error('Payment Error in initiateStripeCheckout:', error);
    throw new Error('Failed to initiate payment. Check logs for API details.'); 
  }
}


