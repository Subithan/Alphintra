// API service for strategy-related operations
// This replaces direct database access with proper API calls

import { gatewayHttpBaseUrl } from '../config/gateway';

export interface StrategyData {
  id: string;
  name: string;
  description: string;
  code: string;
  parameters: Record<string, any>;
  performance: PerformanceMetrics;
  created_at: string;
  updated_at: string;
}

export interface PerformanceMetrics {
  total_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  total_trades: number;
}

export interface BacktestRequest {
  strategy_id: string;
  symbol: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  parameters?: Record<string, any>;
}

export interface BacktestResult {
  id: string;
  strategy_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  performance: PerformanceMetrics;
  trades: Trade[];
  equity_curve: EquityPoint[];
  created_at: string;
  completed_at?: string;
}

export interface Trade {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  timestamp: string;
  pnl: number;
}

export interface EquityPoint {
  timestamp: string;
  equity: number;
  drawdown: number;
}

class StrategyApiService {
  private baseUrl: string;

  constructor() {
    // Route through the gateway
    this.baseUrl = gatewayHttpBaseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const base = this.baseUrl.replace(/\/+$/, '');
    const url = `${base}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Strategy management
  async createStrategy(strategy: Omit<StrategyData, 'id' | 'created_at' | 'updated_at'>): Promise<StrategyData> {
    return this.request<StrategyData>('/api/strategies', {
      method: 'POST',
      body: JSON.stringify(strategy),
    });
  }

  async getStrategy(id: string): Promise<StrategyData> {
    return this.request<StrategyData>(`/api/strategies/${id}`);
  }

  async updateStrategy(id: string, updates: Partial<StrategyData>): Promise<StrategyData> {
    return this.request<StrategyData>(`/api/strategies/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteStrategy(id: string): Promise<void> {
    return this.request<void>(`/api/strategies/${id}`, {
      method: 'DELETE',
    });
  }

  async listStrategies(params?: {
    limit?: number;
    offset?: number;
    sort?: string;
    filter?: string;
  }): Promise<{
    strategies: StrategyData[];
    total: number;
    limit: number;
    offset: number;
  }> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());
    if (params?.sort) searchParams.set('sort', params.sort);
    if (params?.filter) searchParams.set('filter', params.filter);

    const queryString = searchParams.toString();
    const endpoint = `/api/strategies${queryString ? `?${queryString}` : ''}`;
    
    return this.request(endpoint);
  }

  // Backtesting
  async startBacktest(request: BacktestRequest): Promise<{ backtest_id: string }> {
    return this.request<{ backtest_id: string }>('/api/backtests', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getBacktestResult(id: string): Promise<BacktestResult> {
    return this.request<BacktestResult>(`/api/backtests/${id}`);
  }

  async listBacktests(strategyId?: string): Promise<BacktestResult[]> {
    const endpoint = strategyId 
      ? `/api/backtests?strategy_id=${strategyId}`
      : '/api/backtests';
    return this.request<BacktestResult[]>(endpoint);
  }

  async cancelBacktest(id: string): Promise<void> {
    return this.request<void>(`/api/backtests/${id}/cancel`, {
      method: 'POST',
    });
  }

  // Live trading
  async startLiveTrading(strategyId: string, parameters?: Record<string, any>): Promise<{ execution_id: string }> {
    return this.request<{ execution_id: string }>('/api/live-trading/start', {
      method: 'POST',
      body: JSON.stringify({
        strategy_id: strategyId,
        parameters,
      }),
    });
  }

  async stopLiveTrading(executionId: string): Promise<void> {
    return this.request<void>(`/api/live-trading/${executionId}/stop`, {
      method: 'POST',
    });
  }

  async getLiveTradingStatus(executionId: string): Promise<{
    id: string;
    strategy_id: string;
    status: 'running' | 'stopped' | 'paused' | 'error';
    performance: PerformanceMetrics;
    current_positions: any[];
    recent_trades: Trade[];
  }> {
    return this.request(`/api/live-trading/${executionId}`);
  }
}

// Export singleton instance
export const strategyApi = new StrategyApiService();
