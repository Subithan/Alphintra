// API service for market data operations
// This replaces direct database access with proper API calls to backend services

import { buildGatewayUrl } from '../config/gateway';
import { getToken } from '../auth';

export interface MarketDataPoint {
  symbol: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  source: string;
  quality: 'good' | 'fair' | 'poor';
}

export interface DataSourceConfig {
  id: string;
  name: string;
  type: 'rest' | 'websocket' | 'file';
  url: string;
  api_key?: string;
  symbols: string[];
  timeframes: string[];
  enabled: boolean;
  rate_limit?: {
    requests_per_minute: number;
    requests_per_day: number;
  };
}

export interface DataQualityReport {
  symbol: string;
  timeframe: string;
  period: {
    start: string;
    end: string;
  };
  quality_score: number;
  total_points: number;
  missing_points: number;
  invalid_points: number;
  issues: DataQualityIssue[];
}

export interface DataQualityIssue {
  type: string;
  severity: 'low' | 'medium' | 'high';
  message: string;
  timestamp: string;
  affected_points: number;
}

class MarketDataApiService {
  private baseUrl: string;

  constructor() {
    // Use environment variable or default to market data service
    this.baseUrl = buildGatewayUrl('/api/market-data');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const base = this.baseUrl.replace(/\/+$/, '');
    const url = `${base}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    const token = getToken();
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      headers,
      ...options,
    });

    if (!response.ok) {
      throw new Error(`Market Data API request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Historical data retrieval
  async getHistoricalData(params: {
    symbol: string;
    timeframe: string;
    start_date: string;
    end_date: string;
    source?: string;
  }): Promise<MarketDataPoint[]> {
    const searchParams = new URLSearchParams({
      symbol: params.symbol,
      timeframe: params.timeframe,
      start_date: params.start_date,
      end_date: params.end_date,
    });

    if (params.source) {
      searchParams.set('source', params.source);
    }

    return this.request<MarketDataPoint[]>(`/api/historical?${searchParams.toString()}`);
  }

  // Real-time data subscription
  async subscribeToSymbol(symbol: string, timeframe: string): Promise<{ subscription_id: string }> {
    return this.request<{ subscription_id: string }>('/api/subscriptions', {
      method: 'POST',
      body: JSON.stringify({
        symbol,
        timeframe,
      }),
    });
  }

  async unsubscribeFromSymbol(subscriptionId: string): Promise<void> {
    return this.request<void>(`/api/subscriptions/${subscriptionId}`, {
      method: 'DELETE',
    });
  }

  async getActiveSubscriptions(): Promise<{
    id: string;
    symbol: string;
    timeframe: string;
    created_at: string;
    last_update: string;
  }[]> {
    return this.request<any[]>('/api/subscriptions');
  }

  // Data source management
  async getDataSources(): Promise<DataSourceConfig[]> {
    return this.request<DataSourceConfig[]>('/api/sources');
  }

  async createDataSource(source: Omit<DataSourceConfig, 'id'>): Promise<DataSourceConfig> {
    return this.request<DataSourceConfig>('/api/sources', {
      method: 'POST',
      body: JSON.stringify(source),
    });
  }

  async updateDataSource(id: string, updates: Partial<DataSourceConfig>): Promise<DataSourceConfig> {
    return this.request<DataSourceConfig>(`/api/sources/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteDataSource(id: string): Promise<void> {
    return this.request<void>(`/api/sources/${id}`, {
      method: 'DELETE',
    });
  }

  async testDataSource(id: string): Promise<{
    success: boolean;
    message: string;
    latency_ms?: number;
    sample_data?: MarketDataPoint[];
  }> {
    return this.request(`/api/sources/${id}/test`, {
      method: 'POST',
    });
  }

  // Data quality monitoring
  async getDataQualityReport(params: {
    symbol: string;
    timeframe: string;
    start_date: string;
    end_date: string;
  }): Promise<DataQualityReport> {
    const searchParams = new URLSearchParams(params);
    return this.request<DataQualityReport>(`/api/quality/report?${searchParams.toString()}`);
  }

  async getDataQualityAlerts(params?: {
    severity?: string;
    limit?: number;
    offset?: number;
  }): Promise<{
    alerts: DataQualityIssue[];
    total: number;
  }> {
    const searchParams = new URLSearchParams();
    if (params?.severity) searchParams.set('severity', params.severity);
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());

    const queryString = searchParams.toString();
    const endpoint = `/api/quality/alerts${queryString ? `?${queryString}` : ''}`;
    
    return this.request(endpoint);
  }

  // Symbol and market information
  async getAvailableSymbols(exchange?: string): Promise<{
    symbol: string;
    name: string;
    exchange: string;
    type: string;
    active: boolean;
  }[]> {
    const endpoint = exchange ? `/api/symbols?exchange=${exchange}` : '/api/symbols';
    return this.request(endpoint);
  }

  async getSymbolInfo(symbol: string): Promise<{
    symbol: string;
    name: string;
    exchange: string;
    type: string;
    price_precision: number;
    volume_precision: number;
    min_order_size: number;
    max_order_size: number;
    active: boolean;
    trading_hours: {
      timezone: string;
      open: string;
      close: string;
      days: string[];
    };
  }> {
    return this.request(`/api/symbols/${symbol}`);
  }

  async getMarketStatus(): Promise<{
    market: string;
    status: 'open' | 'closed' | 'pre_open' | 'post_close';
    next_open: string;
    next_close: string;
    timezone: string;
  }[]> {
    return this.request('/api/market-status');
  }
}

// Export singleton instance
export const marketDataApi = new MarketDataApiService();
