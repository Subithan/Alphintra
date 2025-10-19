import { Strategy } from '@/components/marketplace/types'; // Import your existing Strategy type

// *** CRITICAL FIX: Use the proxy path defined in next.config.js ***
// This URL will be automatically rewritten by Next.js to: http://localhost:8012/strategies/
const STRATEGIES_API_URL = '/api/v1/strategies/'; 

/**
 * Fetches the list of trading strategies from the FastAPI REST service.
 * NOTE: The data structure returned by the REST service is flat and does not match the
 * complex structure expected by the old GraphQL client (e.g., performance, assetType).
 * We will perform basic mapping here to avoid crashing the frontend.
 * @returns A promise that resolves to an array of Strategy objects.
 */
export async function fetchStrategies(): Promise<Strategy[]> {
    try {
        // Use a simple GET request for the REST endpoint
        // It now uses the proxied URL, which Next.js forwards to the Docker container
        const response = await fetch(STRATEGIES_API_URL, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            },
        });

        if (!response.ok) {
            // Updated error message for REST
            throw new Error(`REST fetch failed with status: ${response.status}`);
        }

        const restStrategies = await response.json();

        // The REST service returns a simpler object (name, id, price_cents, description, subscriber_count).
        // The old GraphQL type expects more fields (creatorName, assetType, performance).
        // We must map the REST data to the expected Strategy type format to avoid frontend errors.
        const mappedStrategies: Strategy[] = restStrategies.map((strategy: any) => ({
            id: strategy.id,
            name: strategy.name,
            price: strategy.price_cents / 100, // Convert cents to dollars for the frontend
            subscriberCount: strategy.subscriber_count,

            // *** MOCK DATA FOR MISSING FIELDS ***
            creatorName: "Alphintra Team", 
            rating: 5,
            assetType: "Crypto", 
            riskLevel: "Medium", 
            performance: { 
                totalReturn: 0.25, 
                maxDrawdown: 0.10, 
                sharpeRatio: 1.5 
            }
        }));

        return mappedStrategies;

    } catch (error) {
        console.error('API Error in fetchStrategies (REST):', error);
        // Ensure the error doesn't stop the application
        return []; 
    }
}
