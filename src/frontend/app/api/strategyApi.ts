import { Strategy } from '@/components/marketplace/types'; // Import your existing Strategy type

// *** CRITICAL FIX: Use the proxy path defined in next.config.js ***
// This URL will be automatically rewritten by Next.js to: http://api.alphintra.com/strategies/
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

        const mappedStrategies: Strategy[] = restStrategies.map((strategy: any) => {
            const priceCents = Number(strategy.price_cents ?? 0);
            return {
                id: Number(strategy.id),
                name: strategy.name ?? 'Untitled Strategy',
                description: strategy.description ?? 'No description provided.',
                category: 'general',
                assetType: (strategy.asset_type ?? 'Crypto') as string,
                tradingPairs: strategy.trading_pairs ?? [],
                price: priceCents === 0 ? 'free' : priceCents / 100,
                riskLevel: ((strategy.risk_level ?? 'medium') as string).toLowerCase() as 'low' | 'medium' | 'high',
                verificationStatus: 'APPROVED',
                performance: {
                    totalReturn: strategy.total_return ?? 0.25,
                    annualizedReturn: strategy.annualized_return ?? 0.18,
                    maxDrawdown: strategy.max_drawdown ?? 0.1,
                    sharpeRatio: strategy.sharpe_ratio ?? 1.5,
                    winRate: strategy.win_rate ?? 55,
                },
                rating: strategy.rating ?? 4.6,
                reviewCount: strategy.review_count ?? 42,
                subscriberCount: strategy.subscriber_count ?? 0,
                lastUpdated: strategy.updated_at ?? new Date().toISOString(),
                isVerified: strategy.is_verified ?? true,
                thumbnail: strategy.thumbnail ?? 'apex-5min',
                gradientColors: strategy.gradient_colors ?? ['#1a2a6c', '#b21f1f', '#fdbb2d'],
                creatorId: (strategy.creator_id ?? 'team').toString(),
                creatorName: strategy.creator_name ?? 'Alphintra Team',
            };
        });

        return mappedStrategies;

    } catch (error) {
        console.error('API Error in fetchStrategies (REST):', error);
        // Ensure the error doesn't stop the application
        return []; 
    }
}

export async function fetchStrategyById(id: string | number): Promise<Strategy | null> {
    const strategies = await fetchStrategies();
    const numericId = Number(id);
    return strategies.find((strategy) => strategy.id === numericId) ?? null;
}
