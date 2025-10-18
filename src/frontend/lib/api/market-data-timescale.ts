// TimescaleDB Market Data API Client
// Handles real-time and historical market data from TimescaleDB

import { BaseApiClient } from './api-client';
import { gatewayHttpBaseUrl } from '../config/gateway';

export interface TimescaleCandle {
  timestamp: string;
  symbol: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  vwap?: number;
  trade_count?: number;
}

export interface MarketDataQuery {
  symbols: string[];
  timeframe: '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1w';
  start_date: string;
  end_date: string;
  limit?: number;
  aggregation?: 'ohlcv' | 'tick' | 'trade';
}

export interface TimescaleMetrics {
  symbol: string;
  timestamp: string;
  price: number;
  volume_24h: number;
  price_change_24h: number;
  price_change_percentage_24h: number;
  market_cap?: number;
  volatility?: number;
}

export interface TimeseriesData {
  symbol: string;
  timeframe: string;
  data: TimescaleCandle[];
  metadata: {
    total_records: number;
    start_time: string;
    end_time: string;
    data_quality: number; // 0-1 representing completeness
    source: string;
  };
}

class TimescaleMarketDataClient extends BaseApiClient {
  constructor() {
    super({
      baseUrl: gatewayHttpBaseUrl,
    });
  }

  /**
   * Fetch historical OHLCV data from TimescaleDB
   */
  async getHistoricalData(query: MarketDataQuery): Promise<TimeseriesData[]> {
    const params = new URLSearchParams({
      symbols: query.symbols.join(','),
      timeframe: query.timeframe,
      start_date: query.start_date,
      end_date: query.end_date,
      ...(query.limit && { limit: query.limit.toString() }),
      ...(query.aggregation && { aggregation: query.aggregation })
    });

    return this.request<TimeseriesData[]>(`/api/v1/market-data/historical?${params}`);
  }

  /**
   * Get real-time market data
   */
  async getRealTimeData(symbols: string[]): Promise<TimescaleMetrics[]> {
    return this.request<TimescaleMetrics[]>('/api/v1/market-data/realtime', {
      method: 'POST',
      body: JSON.stringify({ symbols })
    });
  }

  /**
   * Get market data for backtesting
   */
  async getBacktestData(
    symbols: string[],
    startDate: string,
    endDate: string,
    timeframe: string = '1d'
  ): Promise<{
    [symbol: string]: TimescaleCandle[];
  }> {
    const query: MarketDataQuery = {
      symbols,
      timeframe: timeframe as any,
      start_date: startDate,
      end_date: endDate,
      aggregation: 'ohlcv'
    };

    const timeseriesData = await this.getHistoricalData(query);
    
    // Transform to symbol-keyed object for easier use in backtesting
    const result: { [symbol: string]: TimescaleCandle[] } = {};
    timeseriesData.forEach(series => {
      result[series.symbol] = series.data;
    });

    return result;
  }

  /**
   * Get technical indicators calculated on TimescaleDB
   */
  async getTechnicalIndicators(
    symbol: string,
    indicators: string[],
    timeframe: string = '1d',
    period: number = 252
  ): Promise<{
    [indicator: string]: Array<{
      timestamp: string;
      value: number;
    }>;
  }> {
    return this.request<any>('/api/v1/market-data/indicators', {
      method: 'POST',
      body: JSON.stringify({
        symbol,
        indicators,
        timeframe,
        period
      })
    });
  }

  /**
   * Get market volatility data from TimescaleDB
   */
  async getVolatilityData(
    symbols: string[],
    period: number = 30
  ): Promise<{
    [symbol: string]: {
      current_volatility: number;
      historical_volatility: number;
      volatility_percentile: number;
      risk_category: 'low' | 'medium' | 'high' | 'extreme';
    };
  }> {
    return this.request<any>('/api/v1/market-data/volatility', {
      method: 'POST',
      body: JSON.stringify({ symbols, period })
    });
  }

  /**
   * Get correlation matrix from TimescaleDB
   */
  async getCorrelationMatrix(
    symbols: string[],
    period: number = 252
  ): Promise<{
    [symbol: string]: {
      [symbol: string]: number;
    };
  }> {
    return this.request<any>('/api/v1/market-data/correlation', {
      method: 'POST',
      body: JSON.stringify({ symbols, period })
    });
  }

  /**
   * Subscribe to real-time data stream
   */
  subscribeToRealTime(
    symbols: string[],
    onData: (data: TimescaleMetrics[]) => void,
    onError?: (error: Error) => void
  ): () => void {
    const eventSource = new EventSource(
      `${this.config.baseUrl}/api/v1/market-data/stream?symbols=${symbols.join(',')}`
    );

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onData(data);
      } catch (error) {
        onError?.(new Error('Failed to parse real-time data'));
      }
    };

    eventSource.onerror = (event) => {
      onError?.(new Error('Real-time data stream error'));
    };

    // Return cleanup function
    return () => {
      eventSource.close();
    };
  }

  /**
   * Get data quality metrics
   */
  async getDataQuality(
    symbols: string[],
    startDate: string,
    endDate: string
  ): Promise<{
    [symbol: string]: {
      completeness: number;
      accuracy: number;
      timeliness: number;
      consistency: number;
      overall_score: number;
      issues: string[];
    };
  }> {
    return this.request<any>('/api/v1/market-data/quality', {
      method: 'POST',
      body: JSON.stringify({
        symbols,
        start_date: startDate,
        end_date: endDate
      })
    });
  }

  /**
   * Get market data statistics
   */
  async getMarketStats(
    symbols: string[],
    period: number = 30
  ): Promise<{
    [symbol: string]: {
      avg_price: number;
      avg_volume: number;
      volatility: number;
      sharpe_ratio: number;
      max_drawdown: number;
      beta: number;
      alpha: number;
      correlation_to_market: number;
    };
  }> {
    return this.request<any>('/api/v1/market-data/stats', {
      method: 'POST',
      body: JSON.stringify({ symbols, period })
    });
  }

  /**
   * Validate data availability for backtesting
   */
  async validateDataAvailability(
    symbols: string[],
    startDate: string,
    endDate: string,
    requiredCompleteness: number = 0.95
  ): Promise<{
    available: boolean;
    symbols_status: {
      [symbol: string]: {
        available: boolean;
        completeness: number;
        missing_periods: string[];
        recommendation: string;
      };
    };
    alternative_periods?: {
      start_date: string;
      end_date: string;
      completeness: number;
    }[];
  }> {
    return this.request<any>('/api/v1/market-data/validate', {
      method: 'POST',
      body: JSON.stringify({
        symbols,
        start_date: startDate,
        end_date: endDate,
        required_completeness: requiredCompleteness
      })
    });
  }
}

// Export singleton instance
export const timescaleMarketData = new TimescaleMarketDataClient();

// Export helper functions
export const formatTimescaleDate = (date: Date): string => {
  return date.toISOString().split('T')[0];
};

export const getTimescaleTimeframe = (period: string): string => {
  const mapping: { [key: string]: string } = {
    '1minute': '1m',
    '5minutes': '5m',
    '15minutes': '15m',
    '30minutes': '30m',
    '1hour': '1h',
    '4hours': '4h',
    '1day': '1d',
    '1week': '1w'
  };
  
  return mapping[period] || '1d';
};

export const calculatePeriodFromDates = (startDate: string, endDate: string): number => {
  const start = new Date(startDate);
  const end = new Date(endDate);
  const diffTime = Math.abs(end.getTime() - start.getTime());
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
};
