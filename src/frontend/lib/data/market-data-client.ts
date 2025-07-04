import { EventEmitter } from 'events';

// Market data interfaces
export interface MarketDataPoint {
  symbol: string;
  timestamp: Date;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  source: string;
  quality: 'good' | 'delayed' | 'stale' | 'error';
  latency?: number; // milliseconds from market time
}

export interface MarketDataSubscription {
  id: string;
  symbol: string;
  timeframe: string;
  source: string;
  isActive: boolean;
  lastUpdate?: Date;
  errorCount: number;
  qualityScore: number; // 0-100
}

export interface DataSourceConfig {
  name: string;
  type: 'websocket' | 'rest' | 'file' | 'simulation';
  url: string;
  apiKey?: string;
  rateLimits: {
    requestsPerSecond: number;
    requestsPerMinute: number;
    requestsPerHour: number;
  };
  retryConfig: {
    maxRetries: number;
    backoffMs: number;
    maxBackoffMs: number;
  };
  healthCheck: {
    intervalMs: number;
    timeoutMs: number;
    endpoint?: string;
  };
}

// Data quality metrics
export interface DataQuality {
  symbol: string;
  timeframe: string;
  completeness: number; // 0-100 percentage of expected data points
  timeliness: number; // 0-100 how fresh the data is
  accuracy: number; // 0-100 based on validation checks
  consistency: number; // 0-100 consistency with other sources
  overallScore: number; // 0-100 weighted average
  issues: DataQualityIssue[];
  lastChecked: Date;
}

export interface DataQualityIssue {
  type: 'missing_data' | 'delayed_data' | 'invalid_price' | 'volume_anomaly' | 'gap_detected';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  timestamp: Date;
  affectedBars: number;
  suggestion: string;
}

// Market data sources
export abstract class MarketDataSource extends EventEmitter {
  protected config: DataSourceConfig;
  protected subscriptions = new Map<string, MarketDataSubscription>();
  protected isConnected = false;
  protected reconnectAttempts = 0;
  protected healthCheckInterval?: NodeJS.Timeout;
  protected rateLimitBucket: number[] = [];

  constructor(config: DataSourceConfig) {
    super();
    this.config = config;
    this.setupHealthCheck();
  }

  abstract connect(): Promise<void>;
  abstract disconnect(): Promise<void>;
  abstract subscribe(symbol: string, timeframe: string): Promise<string>;
  abstract unsubscribe(subscriptionId: string): Promise<void>;
  abstract getHistoricalData(symbol: string, startDate: Date, endDate: Date, timeframe: string): Promise<MarketDataPoint[]>;

  protected setupHealthCheck(): void {
    this.healthCheckInterval = setInterval(async () => {
      try {
        await this.performHealthCheck();
      } catch (error) {
        console.error(`Health check failed for ${this.config.name}:`, error);
        this.emit('healthCheckFailed', error);
      }
    }, this.config.healthCheck.intervalMs);
  }

  protected async performHealthCheck(): Promise<void> {
    // Override in subclasses for specific health checks
    if (this.config.healthCheck.endpoint) {
      const response = await fetch(this.config.healthCheck.endpoint, {
        method: 'GET',
        signal: AbortSignal.timeout(this.config.healthCheck.timeoutMs)
      });
      
      if (!response.ok) {
        throw new Error(`Health check endpoint returned ${response.status}`);
      }
    }
  }

  protected checkRateLimit(): boolean {
    const now = Date.now();
    const oneSecondAgo = now - 1000;
    const oneMinuteAgo = now - 60000;
    const oneHourAgo = now - 3600000;

    // Clean old entries
    this.rateLimitBucket = this.rateLimitBucket.filter(t => t > oneHourAgo);

    const requestsLastSecond = this.rateLimitBucket.filter(t => t > oneSecondAgo).length;
    const requestsLastMinute = this.rateLimitBucket.filter(t => t > oneMinuteAgo).length;
    const requestsLastHour = this.rateLimitBucket.length;

    if (requestsLastSecond >= this.config.rateLimits.requestsPerSecond ||
        requestsLastMinute >= this.config.rateLimits.requestsPerMinute ||
        requestsLastHour >= this.config.rateLimits.requestsPerHour) {
      return false;
    }

    this.rateLimitBucket.push(now);
    return true;
  }

  protected async retryWithBackoff<T>(
    operation: () => Promise<T>,
    operationName: string
  ): Promise<T> {
    let lastError: Error;
    
    for (let attempt = 0; attempt <= this.config.retryConfig.maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error as Error;
        
        if (attempt === this.config.retryConfig.maxRetries) {
          break;
        }
        
        const backoffMs = Math.min(
          this.config.retryConfig.backoffMs * Math.pow(2, attempt),
          this.config.retryConfig.maxBackoffMs
        );
        
        console.warn(`${operationName} attempt ${attempt + 1} failed, retrying in ${backoffMs}ms:`, error);
        await new Promise(resolve => setTimeout(resolve, backoffMs));
      }
    }
    
    throw new Error(`${operationName} failed after ${this.config.retryConfig.maxRetries} retries: ${lastError!.message}`);
  }

  getSubscriptions(): MarketDataSubscription[] {
    return Array.from(this.subscriptions.values());
  }

  getConnectionStatus(): boolean {
    return this.isConnected;
  }

  getSourceInfo(): DataSourceConfig {
    return { ...this.config };
  }

  destroy(): void {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
    }
    this.disconnect();
    this.removeAllListeners();
  }
}

// WebSocket-based market data source
export class WebSocketMarketDataSource extends MarketDataSource {
  private ws?: WebSocket;
  private pingInterval?: NodeJS.Timeout;
  private reconnectTimeout?: NodeJS.Timeout;

  async connect(): Promise<void> {
    return this.retryWithBackoff(async () => {
      this.ws = new WebSocket(this.config.url);
      
      return new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('WebSocket connection timeout'));
        }, this.config.healthCheck.timeoutMs);

        this.ws!.onopen = () => {
          clearTimeout(timeout);
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.setupPing();
          this.emit('connected');
          resolve();
        };

        this.ws!.onclose = (event) => {
          clearTimeout(timeout);
          this.isConnected = false;
          this.emit('disconnected', event);
          this.scheduleReconnect();
        };

        this.ws!.onerror = (error) => {
          clearTimeout(timeout);
          this.emit('error', error);
          reject(error);
        };

        this.ws!.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };
      });
    }, 'WebSocket connection');
  }

  async disconnect(): Promise<void> {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
    }
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.close();
    }
    
    this.isConnected = false;
  }

  async subscribe(symbol: string, timeframe: string): Promise<string> {
    if (!this.isConnected) {
      throw new Error('WebSocket not connected');
    }

    const subscriptionId = `${symbol}_${timeframe}_${Date.now()}`;
    const subscription: MarketDataSubscription = {
      id: subscriptionId,
      symbol,
      timeframe,
      source: this.config.name,
      isActive: true,
      errorCount: 0,
      qualityScore: 100
    };

    // Send subscription message
    const subscribeMessage = {
      action: 'subscribe',
      symbol,
      timeframe,
      id: subscriptionId
    };

    this.ws!.send(JSON.stringify(subscribeMessage));
    this.subscriptions.set(subscriptionId, subscription);
    
    return subscriptionId;
  }

  async unsubscribe(subscriptionId: string): Promise<void> {
    const subscription = this.subscriptions.get(subscriptionId);
    if (!subscription) {
      throw new Error(`Subscription ${subscriptionId} not found`);
    }

    if (this.isConnected) {
      const unsubscribeMessage = {
        action: 'unsubscribe',
        id: subscriptionId
      };
      this.ws!.send(JSON.stringify(unsubscribeMessage));
    }

    this.subscriptions.delete(subscriptionId);
  }

  async getHistoricalData(symbol: string, startDate: Date, endDate: Date, timeframe: string): Promise<MarketDataPoint[]> {
    // WebSocket sources typically don't provide historical data
    // This would need to be implemented with a REST API call
    throw new Error('Historical data not supported via WebSocket');
  }

  private setupPing(): void {
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ action: 'ping' }));
      }
    }, 30000); // Ping every 30 seconds
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.config.retryConfig.maxRetries) {
      console.error(`Max reconnection attempts reached for ${this.config.name}`);
      return;
    }

    const backoffMs = Math.min(
      this.config.retryConfig.backoffMs * Math.pow(2, this.reconnectAttempts),
      this.config.retryConfig.maxBackoffMs
    );

    this.reconnectTimeout = setTimeout(() => {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect to ${this.config.name} (attempt ${this.reconnectAttempts})`);
      this.connect().catch(error => {
        console.error('Reconnection failed:', error);
      });
    }, backoffMs);
  }

  private handleMessage(data: any): void {
    try {
      if (data.type === 'marketData') {
        const marketData: MarketDataPoint = {
          symbol: data.symbol,
          timestamp: new Date(data.timestamp),
          open: data.open,
          high: data.high,
          low: data.low,
          close: data.close,
          volume: data.volume,
          source: this.config.name,
          quality: this.assessDataQuality(data),
          latency: Date.now() - new Date(data.timestamp).getTime()
        };

        this.emit('marketData', marketData);
        this.updateSubscriptionStatus(data.symbol, data.timeframe);
      } else if (data.type === 'error') {
        this.handleSubscriptionError(data);
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
    }
  }

  private assessDataQuality(data: any): 'good' | 'delayed' | 'stale' | 'error' {
    const latency = Date.now() - new Date(data.timestamp).getTime();
    
    if (latency < 1000) return 'good';
    if (latency < 5000) return 'delayed';
    if (latency < 30000) return 'stale';
    return 'error';
  }

  private updateSubscriptionStatus(symbol: string, timeframe: string): void {
    for (const subscription of this.subscriptions.values()) {
      if (subscription.symbol === symbol && subscription.timeframe === timeframe) {
        subscription.lastUpdate = new Date();
        subscription.errorCount = 0;
        break;
      }
    }
  }

  private handleSubscriptionError(errorData: any): void {
    const subscriptionId = errorData.subscriptionId;
    const subscription = this.subscriptions.get(subscriptionId);
    
    if (subscription) {
      subscription.errorCount++;
      subscription.qualityScore = Math.max(0, subscription.qualityScore - 10);
      
      this.emit('subscriptionError', {
        subscriptionId,
        error: errorData.error,
        subscription
      });
    }
  }
}

// REST API-based market data source
export class RestMarketDataSource extends MarketDataSource {
  private pollIntervals = new Map<string, NodeJS.Timeout>();

  async connect(): Promise<void> {
    // For REST APIs, "connection" means verifying the endpoint is accessible
    return this.retryWithBackoff(async () => {
      const response = await fetch(`${this.config.url}/health`, {
        headers: this.config.apiKey ? { 'Authorization': `Bearer ${this.config.apiKey}` } : {},
        signal: AbortSignal.timeout(this.config.healthCheck.timeoutMs)
      });

      if (!response.ok) {
        throw new Error(`REST API health check failed: ${response.status}`);
      }

      this.isConnected = true;
      this.emit('connected');
    }, 'REST API connection');
  }

  async disconnect(): Promise<void> {
    // Stop all polling intervals
    for (const interval of this.pollIntervals.values()) {
      clearInterval(interval);
    }
    this.pollIntervals.clear();
    this.isConnected = false;
    this.emit('disconnected');
  }

  async subscribe(symbol: string, timeframe: string): Promise<string> {
    if (!this.isConnected) {
      throw new Error('REST API not connected');
    }

    const subscriptionId = `${symbol}_${timeframe}_${Date.now()}`;
    const subscription: MarketDataSubscription = {
      id: subscriptionId,
      symbol,
      timeframe,
      source: this.config.name,
      isActive: true,
      errorCount: 0,
      qualityScore: 100
    };

    // Set up polling for this subscription
    const pollInterval = this.getTimeframeMs(timeframe);
    const interval = setInterval(async () => {
      try {
        await this.pollMarketData(subscription);
      } catch (error) {
        console.error(`Polling error for ${subscriptionId}:`, error);
        subscription.errorCount++;
        subscription.qualityScore = Math.max(0, subscription.qualityScore - 5);
      }
    }, pollInterval);

    this.pollIntervals.set(subscriptionId, interval);
    this.subscriptions.set(subscriptionId, subscription);

    // Initial data fetch
    await this.pollMarketData(subscription);

    return subscriptionId;
  }

  async unsubscribe(subscriptionId: string): Promise<void> {
    const interval = this.pollIntervals.get(subscriptionId);
    if (interval) {
      clearInterval(interval);
      this.pollIntervals.delete(subscriptionId);
    }
    this.subscriptions.delete(subscriptionId);
  }

  async getHistoricalData(symbol: string, startDate: Date, endDate: Date, timeframe: string): Promise<MarketDataPoint[]> {
    if (!this.checkRateLimit()) {
      throw new Error('Rate limit exceeded');
    }

    const params = new URLSearchParams({
      symbol,
      start: startDate.toISOString(),
      end: endDate.toISOString(),
      timeframe
    });

    const response = await fetch(`${this.config.url}/historical?${params}`, {
      headers: this.config.apiKey ? { 'Authorization': `Bearer ${this.config.apiKey}` } : {},
      signal: AbortSignal.timeout(this.config.healthCheck.timeoutMs)
    });

    if (!response.ok) {
      throw new Error(`Historical data request failed: ${response.status}`);
    }

    const data = await response.json();
    return data.map((point: any) => ({
      symbol,
      timestamp: new Date(point.timestamp),
      open: point.open,
      high: point.high,
      low: point.low,
      close: point.close,
      volume: point.volume,
      source: this.config.name,
      quality: 'good' as const
    }));
  }

  private async pollMarketData(subscription: MarketDataSubscription): Promise<void> {
    if (!this.checkRateLimit()) {
      console.warn(`Rate limit exceeded for ${subscription.symbol}`);
      return;
    }

    const params = new URLSearchParams({
      symbol: subscription.symbol,
      timeframe: subscription.timeframe,
      limit: '1'
    });

    const response = await fetch(`${this.config.url}/realtime?${params}`, {
      headers: this.config.apiKey ? { 'Authorization': `Bearer ${this.config.apiKey}` } : {},
      signal: AbortSignal.timeout(this.config.healthCheck.timeoutMs)
    });

    if (!response.ok) {
      throw new Error(`Market data request failed: ${response.status}`);
    }

    const data = await response.json();
    const point = data[0];

    if (point) {
      const marketData: MarketDataPoint = {
        symbol: subscription.symbol,
        timestamp: new Date(point.timestamp),
        open: point.open,
        high: point.high,
        low: point.low,
        close: point.close,
        volume: point.volume,
        source: this.config.name,
        quality: 'good',
        latency: Date.now() - new Date(point.timestamp).getTime()
      };

      subscription.lastUpdate = new Date();
      this.emit('marketData', marketData);
    }
  }

  private getTimeframeMs(timeframe: string): number {
    const timeframeMap: Record<string, number> = {
      '1s': 1000,
      '5s': 5000,
      '10s': 10000,
      '30s': 30000,
      '1m': 60000,
      '5m': 300000,
      '15m': 900000,
      '30m': 1800000,
      '1h': 3600000,
      '4h': 14400000,
      '1d': 86400000
    };

    return timeframeMap[timeframe] || 60000; // Default to 1 minute
  }
}

// Market data manager
export class MarketDataManager extends EventEmitter {
  private sources = new Map<string, MarketDataSource>();
  private aggregatedData = new Map<string, MarketDataPoint>();
  private qualityMonitor?: NodeJS.Timeout;

  constructor() {
    super();
    this.setupQualityMonitoring();
  }

  addSource(source: MarketDataSource): void {
    this.sources.set(source.getSourceInfo().name, source);
    
    source.on('marketData', (data: MarketDataPoint) => {
      this.handleMarketData(data);
    });

    source.on('error', (error: Error) => {
      this.emit('sourceError', { source: source.getSourceInfo().name, error });
    });

    source.on('connected', () => {
      this.emit('sourceConnected', source.getSourceInfo().name);
    });

    source.on('disconnected', () => {
      this.emit('sourceDisconnected', source.getSourceInfo().name);
    });
  }

  removeSource(sourceName: string): void {
    const source = this.sources.get(sourceName);
    if (source) {
      source.destroy();
      this.sources.delete(sourceName);
    }
  }

  async subscribe(symbol: string, timeframe: string, sourceName?: string): Promise<string[]> {
    const subscriptionIds: string[] = [];
    
    if (sourceName) {
      const source = this.sources.get(sourceName);
      if (!source) {
        throw new Error(`Source ${sourceName} not found`);
      }
      const id = await source.subscribe(symbol, timeframe);
      subscriptionIds.push(id);
    } else {
      // Subscribe to all sources
      for (const source of this.sources.values()) {
        try {
          const id = await source.subscribe(symbol, timeframe);
          subscriptionIds.push(id);
        } catch (error) {
          console.error(`Failed to subscribe to ${source.getSourceInfo().name}:`, error);
        }
      }
    }
    
    return subscriptionIds;
  }

  async connectAll(): Promise<void> {
    const connectionPromises = Array.from(this.sources.values()).map(source =>
      source.connect().catch(error => {
        console.error(`Failed to connect to ${source.getSourceInfo().name}:`, error);
        return error;
      })
    );

    await Promise.allSettled(connectionPromises);
  }

  async disconnectAll(): Promise<void> {
    const disconnectionPromises = Array.from(this.sources.values()).map(source =>
      source.disconnect().catch(error => {
        console.error(`Failed to disconnect from ${source.getSourceInfo().name}:`, error);
        return error;
      })
    );

    await Promise.allSettled(disconnectionPromises);
  }

  getLatestData(symbol: string): MarketDataPoint | undefined {
    return this.aggregatedData.get(symbol);
  }

  getSourceStatuses(): Array<{ name: string; connected: boolean; subscriptions: number }> {
    return Array.from(this.sources.values()).map(source => ({
      name: source.getSourceInfo().name,
      connected: source.getConnectionStatus(),
      subscriptions: source.getSubscriptions().length
    }));
  }

  private handleMarketData(data: MarketDataPoint): void {
    // Store the latest data point for each symbol
    const existing = this.aggregatedData.get(data.symbol);
    
    if (!existing || data.timestamp > existing.timestamp) {
      this.aggregatedData.set(data.symbol, data);
      this.emit('marketData', data);
    }
  }

  private setupQualityMonitoring(): void {
    this.qualityMonitor = setInterval(() => {
      this.checkDataQuality();
    }, 60000); // Check every minute
  }

  private checkDataQuality(): void {
    const now = new Date();
    
    for (const [symbol, data] of this.aggregatedData.entries()) {
      const ageMs = now.getTime() - data.timestamp.getTime();
      
      if (ageMs > 300000) { // 5 minutes old
        this.emit('dataQualityIssue', {
          symbol,
          issue: 'stale_data',
          ageMs,
          severity: ageMs > 900000 ? 'high' : 'medium'
        });
      }
    }
  }

  destroy(): void {
    if (this.qualityMonitor) {
      clearInterval(this.qualityMonitor);
    }
    
    for (const source of this.sources.values()) {
      source.destroy();
    }
    
    this.sources.clear();
    this.aggregatedData.clear();
    this.removeAllListeners();
  }
}