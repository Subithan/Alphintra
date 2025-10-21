// Trading API client for managing trading bots and trade history
// This service handles bot operations, trade history, and balance information

import { BaseApiClient } from './api-client';
import { getToken } from '../auth';
import { tradingHttpBaseUrl } from '../config/gateway';

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

export interface StartBotRequest {
  userId: number;
  strategyId: number;
  capitalAllocation?: number;
  symbol?: string;
}

export interface TradingBot {
  id: number;
  userId: number;
  status: 'RUNNING' | 'STOPPED' | 'ERROR';
  capitalAllocationPercentage: number;
  symbol: string;
  startedAt: string;

}

export interface StopBotsResponse {
  message: string;
  botsStoppedCount: number;
}

export interface Position {
  id: number;
  userId: number;
  botId: number;
  asset: string;
  symbol: string;
  entryPrice: number;
  quantity: number;
  openedAt: string;
  closedAt?: string | null;
  status: 'OPEN' | 'CLOSED';
  pnl?: number | null;
}

export interface PendingOrder {
  id: number;
  positionId: number;
  takeProfitPrice: number | null;
  stopLossPrice: number | null;
  quantity: number;
  status: 'PENDING' | 'TRIGGERED' | 'CANCELLED';
  symbol: string;
  createdAt: string;
  triggeredAt?: string | null;
  triggeredType?: string | null;
  cancelledAt?: string | null;
}

class TradingApiService extends BaseApiClient {
  constructor() {
    super({ baseUrl: tradingHttpBaseUrl });
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
   * Get all bots for a user
   */
  async getAllBots(userId?: number): Promise<TradingBot[]> {
    const queryString = userId ? this.buildQueryString({ userId }) : '';
    return this.get<TradingBot[]>(`/api/trading/bots${queryString ? `?${queryString}` : ''}`);
  }

  /**
   * Get running bots for a user
   */
  async getRunningBots(userId?: number): Promise<TradingBot[]> {
    const queryString = userId ? this.buildQueryString({ userId }) : '';
    return this.get<TradingBot[]>(`/api/trading/bots/running${queryString ? `?${queryString}` : ''}`);
  }

  /**
   * Get all positions
   */
  async getPositions(userId?: number, status?: string): Promise<Position[]> {
    const params: any = {};
    if (userId) params.userId = userId;
    if (status) params.status = status;
    const queryString = this.buildQueryString(params);
    return this.get<Position[]>(`/api/trading/positions${queryString ? `?${queryString}` : ''}`);
  }

  /**
   * Get open positions for a user
   */
  async getOpenPositions(userId: number): Promise<Position[]> {
    const queryString = this.buildQueryString({ userId });
    return this.get<Position[]>(`/api/trading/positions/open?${queryString}`);
  }

  /**
   * Get all pending orders
   */
  async getPendingOrders(userId?: number, status?: string, symbol?: string): Promise<PendingOrder[]> {
    const params: any = {};
    if (userId) params.userId = userId;
    if (status) params.status = status;
    if (symbol) params.symbol = symbol;
    const queryString = this.buildQueryString(params);
    return this.get<PendingOrder[]>(`/api/trading/pending-orders${queryString ? `?${queryString}` : ''}`);
  }

  /**
   * Get pending orders for a specific position
   */
  async getPendingOrdersByPosition(positionId: number): Promise<PendingOrder[]> {
    return this.get<PendingOrder[]>(`/api/trading/pending-orders/position/${positionId}`);
  }
}

// Export singleton instance
export const tradingApi = new TradingApiService();

// Export class for custom instances
export { TradingApiService };
