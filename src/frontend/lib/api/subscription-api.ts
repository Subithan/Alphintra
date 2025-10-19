// file path: "src/frontend/lib/api/subscription-api.ts"

import axios from 'axios';
import { gatewayHttpBaseUrl } from '../config/gateway';
import { getToken } from '../auth';

// Types for Subscription API
export interface CheckoutSessionRequest {
  priceId: string;
  planName: string;
}

export interface CheckoutSessionResponse {
  success: boolean;
  sessionId?: string;
  sessionUrl?: string;
  message?: string;
}

export interface SubscriptionDto {
  id?: number;
  planName?: string;
  status?: string;
  currentPeriodStart?: string;
  currentPeriodEnd?: string;
  cancelAtPeriodEnd?: boolean;
  amount?: string;
  currency?: string;
  interval?: string;
}

export interface SubscriptionStatus {
  hasSubscription: boolean;
  subscription?: SubscriptionDto;
}

// Stripe Price IDs - These should match your .env configuration
export const STRIPE_PRICE_IDS = {
  BASIC: process.env.NEXT_PUBLIC_STRIPE_PRICE_ID_BASIC || '',
  PRO: process.env.NEXT_PUBLIC_STRIPE_PRICE_ID_PRO || '',
  ENTERPRISE: process.env.NEXT_PUBLIC_STRIPE_PRICE_ID_ENTERPRISE || '',
};

// Subscription plans with details
export const SUBSCRIPTION_PLANS = {
  BASIC: {
    name: 'Basic',
    priceId: STRIPE_PRICE_IDS.BASIC,
    price: '$9.99',
    interval: 'month',
    features: [
      'Basic trading strategies',
      'Limited backtesting',
      '5 active strategies',
      'Email support',
    ],
  },
  PRO: {
    name: 'Pro',
    priceId: STRIPE_PRICE_IDS.PRO,
    price: '$19.99',
    interval: 'month',
    features: [
      'Advanced trading strategies',
      'Unlimited backtesting',
      '20 active strategies',
      'Priority support',
      'Real-time market data',
    ],
  },
  ENTERPRISE: {
    name: 'Enterprise',
    priceId: STRIPE_PRICE_IDS.ENTERPRISE,
    price: '$49.99',
    interval: 'month',
    features: [
      'All Pro features',
      'Unlimited strategies',
      'Custom integrations',
      'Dedicated support',
      'White-label options',
    ],
  },
};

export class SubscriptionApiClient {
  private api: ReturnType<typeof axios.create>;

  constructor() {
    this.api = axios.create({
      baseURL: gatewayHttpBaseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to all requests
    this.api.interceptors.request.use((config) => {
      const token = getToken();
      if (token) {
        config.headers = config.headers ?? {};
        if (!config.headers['Authorization']) {
          config.headers['Authorization'] = `Bearer ${token}`;
        }
      }
      return config;
    });

    if (process.env.NODE_ENV === 'development' && process.env.NEXT_PUBLIC_DEBUG_API === 'true') {
      console.log('🔧 SubscriptionApiClient Debug:', {
        baseUrl: this.api.defaults.baseURL,
      });
    }
  }

  /**
   * Create a Stripe checkout session for subscription
   */
  async createCheckoutSession(
    request: CheckoutSessionRequest
  ): Promise<CheckoutSessionResponse> {
    const response = await this.api.post<CheckoutSessionResponse>(
      '/api/subscriptions/create-checkout-session',
      request
    );
    return response.data;
  }

  /**
   * Get current user's subscription details
   */
  async getCurrentSubscription(): Promise<SubscriptionDto> {
    const response = await this.api.get<SubscriptionDto>('/api/subscriptions/current');
    return response.data;
  }

  /**
   * Check if user has an active subscription
   */
  async getSubscriptionStatus(): Promise<SubscriptionStatus> {
    try {
      const subscription = await this.getCurrentSubscription();
      const hasActiveSubscription =
        subscription &&
        subscription.status === 'active' &&
        subscription.planName !== undefined;

      return {
        hasSubscription: hasActiveSubscription,
        subscription: hasActiveSubscription ? subscription : undefined,
      };
    } catch (error) {
      return {
        hasSubscription: false,
      };
    }
  }

  /**
   * Redirect to Stripe Checkout
   */
  async redirectToCheckout(planName: 'BASIC' | 'PRO' | 'ENTERPRISE'): Promise<void> {
    const plan = SUBSCRIPTION_PLANS[planName];
    if (!plan.priceId) {
      throw new Error(`Price ID not configured for plan: ${planName}`);
    }

    const response = await this.createCheckoutSession({
      priceId: plan.priceId,
      planName: planName.toLowerCase(),
    });

    if (response.success && response.sessionUrl) {
      // Redirect to Stripe Checkout
      window.location.href = response.sessionUrl;
    } else {
      throw new Error(response.message || 'Failed to create checkout session');
    }
  }
}

export const subscriptionApiClient = new SubscriptionApiClient();
