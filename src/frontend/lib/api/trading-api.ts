// Trading API client for managing trading bots and trade history
// This service handles bot operations, trade history, and balance information

import { BaseApiClient } from './api-client';
import { getToken } from '../auth';
import type { TradingBot, TradingPosition } from './types';

export interface TradeOrderData {
  id: number;
  botId: number;
  exchangeOrderId: string;
  symbol: string;
  type: string;
  side: string;
  price: number;
  amount: number;
  status: string;
  createdAt: string;
}

export interface BalanceInfo {
  asset: string;
  free: number;
  locked: number;
  total: number;
}

export interface UserBalance {
  id: number;
  userId: number;
  asset: string;
  free: number;
  locked: number;
  total: number;
  createdAt: string;
  updatedAt: string;
}

export interface StartBotRequest {
  userId: number;
  strategyId: number;
  capitalAllocation?: number;
  symbol?: string;
}

export interface StopBotsResponse {
  message: string;
}

class TradingApiService extends BaseApiClient {
  constructor() {
    super();
  }

  /**
   * Get trade history for the authenticated user
   * The backend filters trades based on the X-User-Id header from JWT
   * @param limit - Maximum number of trades to return (default: 20)
   */
  async getTradeHistory(limit: number = 20): Promise<TradeOrderData[]> {
    // Debug: Check token availability
    const token = getToken();
    console.log('[Trading API] getTradeHistory called', {
      hasToken: !!token,
      tokenPreview: token ? `${token.substring(0, 20)}...` : 'null',
      isClient: typeof window !== 'undefined',
    });

    const queryString = this.buildQueryString({ limit });
    return this.get<TradeOrderData[]>(`/api/trading/trades?${queryString}`);
  }

  /**
   * Get balance information from the exchange
   */
  async getBalance(): Promise<BalanceInfo> {
    return this.get<BalanceInfo>('/api/trading/balance');
  }

  /**
   * Start a trading bot
   * @param request - Bot configuration including userId, strategyId, capitalAllocation, and symbol
   */
  async startBot(request: StartBotRequest): Promise<TradingBot> {
    return this.post<TradingBot>('/api/trading/bot/start', request);
  }

  /**
   * Stop all active trading bots
   */
  async stopAllBots(): Promise<StopBotsResponse> {
    return this.post<StopBotsResponse>('/api/trading/bots/stop');
  }

  /**
   * Get all trading bots for the authenticated user
   */
  async getBots(): Promise<TradingBot[]> {
    const token = getToken();
    console.log('[Trading API] getBots called', {
      hasToken: !!token,
      isClient: typeof window !== 'undefined',
    });
    return this.get<TradingBot[]>('/api/trading/bots');
  }

  /**
   * Get all positions for the authenticated user
   */
  async getPositions(): Promise<TradingPosition[]> {
    const token = getToken();
    console.log('[Trading API] getPositions called', {
      hasToken: !!token,
      isClient: typeof window !== 'undefined',
    });
    return this.get<TradingPosition[]>('/api/trading/positions');
  }

  /**
   * Get user balances for the authenticated user
   */
  async getUserBalances(): Promise<UserBalance[]> {
    const token = getToken();
    console.log('[Trading API] getUserBalances called', {
      hasToken: !!token,
      isClient: typeof window !== 'undefined',
    });
    return this.get<UserBalance[]>('/api/trading/user/balances');
  }
}

// Export singleton instance
export const tradingApi = new TradingApiService();

// Export class for custom instances
export { TradingApiService };
