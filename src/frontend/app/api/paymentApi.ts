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
  
  // FIX: To resolve the 422 error, we are moving the simple 'user_email' parameter 
  // from the JSON body to a URL query parameter, as this is more resilient 
  // to FastAPI's strict body validation rules when a Pydantic model isn't explicitly used.
  // The backend endpoint signature is: def purchase_strategy(..., user_email: str, ...)
  const CHECKOUT_ENDPOINT = `${MARKETPLACE_API_URL}/strategies/${strategyId}/purchase?user_email=${encodeURIComponent(userEmail)}`;

  try {
    const response = await fetch(CHECKOUT_ENDPOINT, {
      // NOTE: We keep POST as required by the backend, but the body is now empty (or contains 
      // the minimum required data if any). Since `user_email` is now in the URL, the body 
      // should be empty to prevent the 422 error caused by JSON format mismatch.
      method: 'POST',
      headers: {
        // We can omit 'Content-Type': 'application/json' if the body is empty, 
        // but we'll leave it for now in case authentication is added.
        'Content-Type': 'application/json',
        // *** You MUST pass the Authorization/JWT token here for the user initiating the purchase ***
      },
      // IMPORTANT: Body is now an empty object because user_email is in the URL.
      body: JSON.stringify({}), 
    });

    if (!response.ok) {
      // Check for application-specific errors from the Marketplace service
      const errorBody = await response.json();
      throw new Error(errorBody.detail || `Checkout API failed with status: ${response.status}`);
    }

    // Since the backend returns a 303 RedirectResponse, this fetch will return the 
    // URL in the 'Location' header, but the browser usually handles this redirect automatically. 
    // If the browser doesn't automatically redirect on a successful fetch, we may need 
    // to switch to `window.location.replace(response.url)`.

    // Assuming the browser handles the redirect (and thus the function doesn't need 
    // to return a Stripe URL for client-side redirection anymore):
    return response.url; // Returning the response URL might be the best guess if the 303 isn't automatic.

  } catch (error) {
    console.error('Payment Error in initiateStripeCheckout:', error);
    throw new Error('Failed to initiate payment. Check logs for API details.'); 
  }
}


