import { MarketData } from './execution-engine';
import { buildGatewayWsUrl } from './config/gateway';
import { getToken } from './auth';

export interface DataProviderConfig {
  provider_type: 'polygon' | 'alpaca' | 'yahoo' | 'iex' | 'websocket' | 'mock';
  api_key?: string;
  base_url?: string;
  websocket_url?: string;
  rate_limit: number; // Requests per second
  retry_attempts: number;
  timeout_ms: number;
  data_quality_checks: boolean;
}

export interface SubscriptionConfig {
  symbols: string[];
  data_types: ('trades' | 'quotes' | 'bars' | 'news' | 'fundamentals')[];
  timeframes?: string[]; // For bars: '1m', '5m', '1h', '1d'
  quality_level: 'basic' | 'premium' | 'institutional';
  buffer_size: number; // Number of data points to keep in memory
  persistence: boolean; // Whether to persist data to storage
}

export interface StreamingData {
  symbol: string;
  data_type: 'trade' | 'quote' | 'bar' | 'news' | 'fundamental';
  timestamp: Date;
  data: any;
  sequence_number: number;
  provider: string;
  quality_score: number; // 0-1, data quality indicator
}

export interface TradeData {
  symbol: string;
  timestamp: Date;
  price: number;
  size: number;
  exchange: string;
  conditions: string[];
  tape: string;
}

export interface QuoteData {
  symbol: string;
  timestamp: Date;
  bid_price: number;
  bid_size: number;
  ask_price: number;
  ask_size: number;
  exchange: string;
  conditions: string[];
}

export interface BarData extends MarketData {
  timeframe: string;
  vwap: number; // Volume Weighted Average Price
  trade_count: number;
}

export interface NewsData {
  symbol: string;
  timestamp: Date;
  headline: string;
  summary: string;
  source: string;
  sentiment: number; // -1 to 1
  relevance: number; // 0 to 1
  url: string;
}

export interface FundamentalData {
  symbol: string;
  timestamp: Date;
  data_type: 'earnings' | 'dividends' | 'splits' | 'financials';
  data: any;
}

export interface DataQualityMetrics {
  symbol: string;
  total_messages: number;
  valid_messages: number;
  error_rate: number;
  latency_avg_ms: number;
  latency_p99_ms: number;
  gaps_detected: number;
  duplicates_detected: number;
  out_of_sequence: number;
  last_update: Date;
}

export interface ConnectionStatus {
  provider: string;
  status: 'connected' | 'connecting' | 'disconnected' | 'error';
  connected_since: Date | null;
  last_message: Date | null;
  reconnect_attempts: number;
  error_message?: string;
  subscriptions_active: number;
  latency_ms: number;
}

export interface DataBuffer {
  symbol: string;
  data_type: string;
  timeframe?: string;
  data: StreamingData[];
  max_size: number;
  last_cleanup: Date;
}

export interface DataAlert {
  alert_id: string;
  timestamp: Date;
  severity: 'info' | 'warning' | 'error' | 'critical';
  type: 'connection' | 'quality' | 'latency' | 'gap' | 'rate_limit';
  provider: string;
  symbol?: string;
  message: string;
  auto_resolved: boolean;
}

export class RealTimeDataEngine {
  private providers: Map<string, DataProviderConfig> = new Map();
  private connections: Map<string, WebSocket | any> = new Map();
  private subscriptions: Map<string, SubscriptionConfig> = new Map();
  private dataBuffers: Map<string, DataBuffer> = new Map();
  private qualityMetrics: Map<string, DataQualityMetrics> = new Map();
  private connectionStatus: Map<string, ConnectionStatus> = new Map();
  private alerts: DataAlert[] = [];
  private eventListeners: Map<string, Function[]> = new Map();
  private sequenceNumbers: Map<string, number> = new Map();
  private rateLimiters: Map<string, RateLimiter> = new Map();

  constructor() {
    this.initializeEventListeners();
    setInterval(() => this.performMaintenanceTasks(), 30000); // Every 30 seconds
  }

  private initializeEventListeners(): void {
    this.eventListeners.set('data', []);
    this.eventListeners.set('connection', []);
    this.eventListeners.set('error', []);
    this.eventListeners.set('quality', []);
  }

  public addProvider(providerId: string, config: DataProviderConfig): void {
    this.providers.set(providerId, config);
    this.rateLimiters.set(providerId, new RateLimiter(config.rate_limit, 1000));
    
    this.connectionStatus.set(providerId, {
      provider: providerId,
      status: 'disconnected',
      connected_since: null,
      last_message: null,
      reconnect_attempts: 0,
      subscriptions_active: 0,
      latency_ms: 0
    });

    console.log(`Data provider ${providerId} added`);
  }

  public async connectProvider(providerId: string): Promise<void> {
    const config = this.providers.get(providerId);
    if (!config) {
      throw new Error(`Provider ${providerId} not found`);
    }

    const status = this.connectionStatus.get(providerId)!;
    status.status = 'connecting';
    status.reconnect_attempts++;

    try {
      switch (config.provider_type) {
        case 'websocket':
          await this.connectWebSocket(providerId, config);
          break;
        case 'polygon':
          await this.connectPolygon(providerId, config);
          break;
        case 'alpaca':
          await this.connectAlpaca(providerId, config);
          break;
        case 'mock':
          await this.connectMockProvider(providerId, config);
          break;
        default:
          throw new Error(`Provider type ${config.provider_type} not supported`);
      }

      status.status = 'connected';
      status.connected_since = new Date();
      status.error_message = undefined;

      this.emitEvent('connection', { provider: providerId, status: 'connected' });
      console.log(`Connected to provider ${providerId}`);

    } catch (error) {
      status.status = 'error';
      status.error_message = error instanceof Error ? error.message : String(error);
      
      this.createAlert({
        severity: 'error',
        type: 'connection',
        provider: providerId,
        message: `Failed to connect to ${providerId}: ${status.error_message}`
      });

      console.error(`Failed to connect to provider ${providerId}:`, error);
      throw error;
    }
  }

  private async connectWebSocket(providerId: string, config: DataProviderConfig): Promise<void> {
    return new Promise((resolve, reject) => {
      const token = getToken();
      const defaultWs = buildGatewayWsUrl(`/ws/market${token ? `?token=${encodeURIComponent(token)}` : ''}`);
      const wsUrl = config.websocket_url ? `${config.websocket_url}${token ? (config.websocket_url.includes('?') ? `&token=${encodeURIComponent(token)}` : `?token=${encodeURIComponent(token)}`) : ''}` : defaultWs;
      const ws = new WebSocket(wsUrl);
      
      const timeout = setTimeout(() => {
        ws.close();
        reject(new Error('Connection timeout'));
      }, config.timeout_ms);

      ws.onopen = () => {
        clearTimeout(timeout);
        this.connections.set(providerId, ws);
        this.setupWebSocketHandlers(providerId, ws);
        resolve();
      };

      ws.onerror = (error) => {
        clearTimeout(timeout);
        reject(error);
      };
    });
  }

  private async connectPolygon(providerId: string, config: DataProviderConfig): Promise<void> {
    const wsUrl = `wss://socket.polygon.io/stocks`;
    const ws = new WebSocket(wsUrl);

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        ws.close();
        reject(new Error('Polygon connection timeout'));
      }, config.timeout_ms);

      ws.onopen = () => {
        // Authenticate with Polygon
        ws.send(JSON.stringify({
          action: 'auth',
          params: config.api_key
        }));
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data[0]?.ev === 'status' && data[0]?.status === 'auth_success') {
          clearTimeout(timeout);
          this.connections.set(providerId, ws);
          this.setupPolygonHandlers(providerId, ws);
          resolve();
        } else if (data[0]?.ev === 'status' && data[0]?.status === 'auth_failed') {
          clearTimeout(timeout);
          reject(new Error('Polygon authentication failed'));
        }
      };

      ws.onerror = (error) => {
        clearTimeout(timeout);
        reject(error);
      };
    });
  }

  private async connectAlpaca(providerId: string, config: DataProviderConfig): Promise<void> {
    const wsUrl = `wss://stream.data.alpaca.markets/v2/iex`;
    const ws = new WebSocket(wsUrl);

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        ws.close();
        reject(new Error('Alpaca connection timeout'));
      }, config.timeout_ms);

      ws.onopen = () => {
        // Authenticate with Alpaca
        ws.send(JSON.stringify({
          action: 'auth',
          key: config.api_key,
          secret: 'your_secret_key' // In production, this would be properly configured
        }));
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data[0]?.T === 'success' && data[0]?.msg === 'authenticated') {
          clearTimeout(timeout);
          this.connections.set(providerId, ws);
          this.setupAlpacaHandlers(providerId, ws);
          resolve();
        } else if (data[0]?.T === 'error') {
          clearTimeout(timeout);
          reject(new Error(`Alpaca error: ${data[0]?.msg}`));
        }
      };

      ws.onerror = (error) => {
        clearTimeout(timeout);
        reject(error);
      };
    });
  }

  private async connectMockProvider(providerId: string, config: DataProviderConfig): Promise<void> {
    // Mock connection for testing
    const mockConnection = {
      readyState: WebSocket.OPEN,
      send: (data: string) => console.log(`Mock send: ${data}`),
      close: () => console.log('Mock connection closed')
    };

    this.connections.set(providerId, mockConnection);
    this.setupMockDataGeneration(providerId);
  }

  private setupWebSocketHandlers(providerId: string, ws: WebSocket): void {
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.processIncomingData(providerId, data);
      } catch (error) {
        console.error(`Error processing WebSocket message from ${providerId}:`, error);
      }
    };

    ws.onclose = () => {
      this.handleConnectionClose(providerId);
    };

    ws.onerror = (error) => {
      this.handleConnectionError(providerId, error);
    };
  }

  private setupPolygonHandlers(providerId: string, ws: WebSocket): void {
    ws.onmessage = (event) => {
      try {
        const messages = JSON.parse(event.data);
        messages.forEach((msg: any) => {
          if (msg.ev === 'T') { // Trade
            this.processPolygonTrade(providerId, msg);
          } else if (msg.ev === 'Q') { // Quote
            this.processPolygonQuote(providerId, msg);
          } else if (msg.ev === 'AM') { // Aggregate (Bar)
            this.processPolygonBar(providerId, msg);
          }
        });
      } catch (error) {
        console.error(`Error processing Polygon message:`, error);
      }
    };

    ws.onclose = () => this.handleConnectionClose(providerId);
    ws.onerror = (error) => this.handleConnectionError(providerId, error);
  }

  private setupAlpacaHandlers(providerId: string, ws: WebSocket): void {
    ws.onmessage = (event) => {
      try {
        const messages = JSON.parse(event.data);
        messages.forEach((msg: any) => {
          if (msg.T === 't') { // Trade
            this.processAlpacaTrade(providerId, msg);
          } else if (msg.T === 'q') { // Quote
            this.processAlpacaQuote(providerId, msg);
          } else if (msg.T === 'b') { // Bar
            this.processAlpacaBar(providerId, msg);
          }
        });
      } catch (error) {
        console.error(`Error processing Alpaca message:`, error);
      }
    };

    ws.onclose = () => this.handleConnectionClose(providerId);
    ws.onerror = (error) => this.handleConnectionError(providerId, error);
  }

  private setupMockDataGeneration(providerId: string): void {
    // Generate mock market data every second
    setInterval(() => {
      const symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA'];
      
      symbols.forEach(symbol => {
        // Generate mock trade
        const tradeData: TradeData = {
          symbol,
          timestamp: new Date(),
          price: 150 + Math.random() * 100,
          size: Math.floor(Math.random() * 1000) + 100,
          exchange: 'NASDAQ',
          conditions: [],
          tape: 'C'
        };

        this.processStreamingData(providerId, {
          symbol,
          data_type: 'trade',
          timestamp: tradeData.timestamp,
          data: tradeData,
          sequence_number: this.getNextSequenceNumber(providerId),
          provider: providerId,
          quality_score: 1.0
        });

        // Generate mock quote
        const bid = tradeData.price - Math.random() * 0.5;
        const ask = tradeData.price + Math.random() * 0.5;
        
        const quoteData: QuoteData = {
          symbol,
          timestamp: new Date(),
          bid_price: bid,
          bid_size: Math.floor(Math.random() * 500) + 100,
          ask_price: ask,
          ask_size: Math.floor(Math.random() * 500) + 100,
          exchange: 'NASDAQ',
          conditions: []
        };

        this.processStreamingData(providerId, {
          symbol,
          data_type: 'quote',
          timestamp: quoteData.timestamp,
          data: quoteData,
          sequence_number: this.getNextSequenceNumber(providerId),
          provider: providerId,
          quality_score: 1.0
        });
      });
    }, 1000);
  }

  public async subscribe(subscriptionId: string, config: SubscriptionConfig): Promise<void> {
    this.subscriptions.set(subscriptionId, config);

    // Initialize data buffers for each symbol/data_type combination
    config.symbols.forEach(symbol => {
      config.data_types.forEach(dataType => {
        const bufferId = `${symbol}_${dataType}`;
        
        if (!this.dataBuffers.has(bufferId)) {
          this.dataBuffers.set(bufferId, {
            symbol,
            data_type: dataType,
            data: [],
            max_size: config.buffer_size,
            last_cleanup: new Date()
          });
        }

        // Initialize quality metrics
        if (!this.qualityMetrics.has(symbol)) {
          this.qualityMetrics.set(symbol, {
            symbol,
            total_messages: 0,
            valid_messages: 0,
            error_rate: 0,
            latency_avg_ms: 0,
            latency_p99_ms: 0,
            gaps_detected: 0,
            duplicates_detected: 0,
            out_of_sequence: 0,
            last_update: new Date()
          });
        }
      });
    });

    // Send subscription requests to connected providers
    for (const [providerId, connection] of this.connections.entries()) {
      if (this.connectionStatus.get(providerId)?.status === 'connected') {
        await this.sendSubscriptionRequest(providerId, config);
      }
    }

    console.log(`Subscription ${subscriptionId} created for ${config.symbols.length} symbols`);
  }

  private async sendSubscriptionRequest(providerId: string, config: SubscriptionConfig): Promise<void> {
    const provider = this.providers.get(providerId);
    const connection = this.connections.get(providerId);

    if (!provider || !connection) return;

    try {
      switch (provider.provider_type) {
        case 'polygon':
          this.sendPolygonSubscription(connection, config);
          break;
        case 'alpaca':
          this.sendAlpacaSubscription(connection, config);
          break;
        case 'websocket':
        case 'mock':
          // Already handled in mock setup
          break;
      }

      // Update subscription count
      const status = this.connectionStatus.get(providerId)!;
      status.subscriptions_active++;

    } catch (error) {
      console.error(`Error sending subscription to ${providerId}:`, error);
    }
  }

  private sendPolygonSubscription(connection: any, config: SubscriptionConfig): void {
    const subscriptions: string[] = [];
    
    config.symbols.forEach(symbol => {
      config.data_types.forEach(dataType => {
        switch (dataType) {
          case 'trades':
            subscriptions.push(`T.${symbol}`);
            break;
          case 'quotes':
            subscriptions.push(`Q.${symbol}`);
            break;
          case 'bars':
            subscriptions.push(`AM.${symbol}`);
            break;
        }
      });
    });

    connection.send(JSON.stringify({
      action: 'subscribe',
      params: subscriptions.join(',')
    }));
  }

  private sendAlpacaSubscription(connection: any, config: SubscriptionConfig): void {
    const message: any = { action: 'subscribe' };
    
    config.data_types.forEach(dataType => {
      switch (dataType) {
        case 'trades':
          message.trades = config.symbols;
          break;
        case 'quotes':
          message.quotes = config.symbols;
          break;
        case 'bars':
          message.bars = config.symbols;
          break;
      }
    });

    connection.send(JSON.stringify(message));
  }

  private processIncomingData(providerId: string, data: any): void {
    // Generic data processing for custom WebSocket providers
    if (data.symbol && data.type && data.timestamp) {
      const streamingData: StreamingData = {
        symbol: data.symbol,
        data_type: data.type,
        timestamp: new Date(data.timestamp),
        data: data,
        sequence_number: this.getNextSequenceNumber(providerId),
        provider: providerId,
        quality_score: 1.0
      };

      this.processStreamingData(providerId, streamingData);
    }
  }

  private processPolygonTrade(providerId: string, msg: any): void {
    const tradeData: TradeData = {
      symbol: msg.sym,
      timestamp: new Date(msg.t),
      price: msg.p,
      size: msg.s,
      exchange: msg.x?.toString() || '',
      conditions: msg.c || [],
      tape: msg.z || ''
    };

    this.processStreamingData(providerId, {
      symbol: msg.sym,
      data_type: 'trade',
      timestamp: new Date(msg.t),
      data: tradeData,
      sequence_number: this.getNextSequenceNumber(providerId),
      provider: providerId,
      quality_score: this.calculateQualityScore(tradeData)
    });
  }

  private processPolygonQuote(providerId: string, msg: any): void {
    const quoteData: QuoteData = {
      symbol: msg.sym,
      timestamp: new Date(msg.t),
      bid_price: msg.bp,
      bid_size: msg.bs,
      ask_price: msg.ap,
      ask_size: msg.as,
      exchange: msg.x?.toString() || '',
      conditions: msg.c || []
    };

    this.processStreamingData(providerId, {
      symbol: msg.sym,
      data_type: 'quote',
      timestamp: new Date(msg.t),
      data: quoteData,
      sequence_number: this.getNextSequenceNumber(providerId),
      provider: providerId,
      quality_score: this.calculateQualityScore(quoteData)
    });
  }

  private processPolygonBar(providerId: string, msg: any): void {
    const barData: BarData = {
      symbol: msg.sym,
      timestamp: new Date(msg.s), // Start time
      timeframe: '1m', // Polygon aggregates are typically 1-minute
      open: msg.o,
      high: msg.h,
      low: msg.l,
      close: msg.c,
      volume: msg.v,
      vwap: msg.vw || (msg.o + msg.h + msg.l + msg.c) / 4,
      trade_count: msg.n || 0
    };

    this.processStreamingData(providerId, {
      symbol: msg.sym,
      data_type: 'bar',
      timestamp: new Date(msg.s),
      data: barData,
      sequence_number: this.getNextSequenceNumber(providerId),
      provider: providerId,
      quality_score: this.calculateQualityScore(barData)
    });
  }

  private processAlpacaTrade(providerId: string, msg: any): void {
    const tradeData: TradeData = {
      symbol: msg.S,
      timestamp: new Date(msg.t),
      price: msg.p,
      size: msg.s,
      exchange: msg.x || '',
      conditions: msg.c || [],
      tape: msg.z || ''
    };

    this.processStreamingData(providerId, {
      symbol: msg.S,
      data_type: 'trade',
      timestamp: new Date(msg.t),
      data: tradeData,
      sequence_number: this.getNextSequenceNumber(providerId),
      provider: providerId,
      quality_score: this.calculateQualityScore(tradeData)
    });
  }

  private processAlpacaQuote(providerId: string, msg: any): void {
    const quoteData: QuoteData = {
      symbol: msg.S,
      timestamp: new Date(msg.t),
      bid_price: msg.bp,
      bid_size: msg.bs,
      ask_price: msg.ap,
      ask_size: msg.as,
      exchange: msg.bx || '',
      conditions: msg.c || []
    };

    this.processStreamingData(providerId, {
      symbol: msg.S,
      data_type: 'quote',
      timestamp: new Date(msg.t),
      data: quoteData,
      sequence_number: this.getNextSequenceNumber(providerId),
      provider: providerId,
      quality_score: this.calculateQualityScore(quoteData)
    });
  }

  private processAlpacaBar(providerId: string, msg: any): void {
    const barData: BarData = {
      symbol: msg.S,
      timestamp: new Date(msg.t),
      timeframe: '1m',
      open: msg.o,
      high: msg.h,
      low: msg.l,
      close: msg.c,
      volume: msg.v,
      vwap: msg.vw || (msg.o + msg.h + msg.l + msg.c) / 4,
      trade_count: msg.n || 0
    };

    this.processStreamingData(providerId, {
      symbol: msg.S,
      data_type: 'bar',
      timestamp: new Date(msg.t),
      data: barData,
      sequence_number: this.getNextSequenceNumber(providerId),
      provider: providerId,
      quality_score: this.calculateQualityScore(barData)
    });
  }

  private processStreamingData(providerId: string, streamingData: StreamingData): void {
    // Update connection status
    const status = this.connectionStatus.get(providerId);
    if (status) {
      status.last_message = new Date();
      status.latency_ms = Date.now() - streamingData.timestamp.getTime();
    }

    // Quality checks
    if (this.providers.get(providerId)?.data_quality_checks) {
      if (!this.performQualityChecks(streamingData)) {
        this.updateQualityMetrics(streamingData.symbol, false);
        return;
      }
    }

    // Update quality metrics
    this.updateQualityMetrics(streamingData.symbol, true);

    // Store in buffer
    this.addToBuffer(streamingData);

    // Emit data event
    this.emitEvent('data', streamingData);

    // Convert to MarketData format for bars
    if (streamingData.data_type === 'bar') {
      const barData = streamingData.data as BarData;
      const marketData: MarketData = {
        symbol: barData.symbol,
        timestamp: barData.timestamp,
        open: barData.open,
        high: barData.high,
        low: barData.low,
        close: barData.close,
        volume: barData.volume
      };

      this.emitEvent('bar', marketData);
    }
  }

  private performQualityChecks(data: StreamingData): boolean {
    // Basic quality checks
    if (!data.symbol || !data.timestamp || !data.data) {
      return false;
    }

    // Price reasonableness checks for trades and quotes
    if (data.data_type === 'trade' || data.data_type === 'quote') {
      const priceData = data.data as TradeData | QuoteData;
      
      if (data.data_type === 'trade') {
        const trade = priceData as TradeData;
        if (trade.price <= 0 || trade.size <= 0) return false;
        if (trade.price > 100000) return false; // Unreasonable high price
      } else {
        const quote = priceData as QuoteData;
        if (quote.bid_price <= 0 || quote.ask_price <= 0) return false;
        if (quote.ask_price <= quote.bid_price) return false; // Crossed market
        if (quote.bid_size <= 0 || quote.ask_size <= 0) return false;
      }
    }

    // Bar data checks
    if (data.data_type === 'bar') {
      const bar = data.data as BarData;
      if (bar.open <= 0 || bar.high <= 0 || bar.low <= 0 || bar.close <= 0) return false;
      if (bar.high < bar.low) return false;
      if (bar.high < bar.open || bar.high < bar.close) return false;
      if (bar.low > bar.open || bar.low > bar.close) return false;
      if (bar.volume < 0) return false;
    }

    // Timestamp checks
    const now = Date.now();
    const dataTime = data.timestamp.getTime();
    if (dataTime > now + 60000) return false; // More than 1 minute in future
    if (now - dataTime > 86400000) return false; // More than 1 day old

    return true;
  }

  private calculateQualityScore(data: any): number {
    let score = 1.0;

    // Reduce score for missing optional fields
    if (data.conditions && data.conditions.length > 0) {
      score -= 0.1; // Conditions might indicate irregular trade
    }

    if (data.data_type === 'trade') {
      const trade = data as TradeData;
      if (!trade.exchange) score -= 0.1;
      if (trade.size < 100) score -= 0.1; // Small trades might be less reliable
    }

    if (data.data_type === 'quote') {
      const quote = data as QuoteData;
      const spread = quote.ask_price - quote.bid_price;
      const midpoint = (quote.ask_price + quote.bid_price) / 2;
      const spreadPercent = (spread / midpoint) * 100;
      
      if (spreadPercent > 5) score -= 0.2; // Wide spreads indicate poor liquidity
    }

    return Math.max(0, Math.min(1, score));
  }

  private updateQualityMetrics(symbol: string, isValid: boolean): void {
    const metrics = this.qualityMetrics.get(symbol);
    if (!metrics) return;

    metrics.total_messages++;
    if (isValid) {
      metrics.valid_messages++;
    }

    metrics.error_rate = 1 - (metrics.valid_messages / metrics.total_messages);
    metrics.last_update = new Date();

    // Emit quality alert if error rate is high
    if (metrics.error_rate > 0.1 && metrics.total_messages > 100) {
      this.createAlert({
        severity: 'warning',
        type: 'quality',
        provider: 'system',
        symbol,
        message: `High error rate detected for ${symbol}: ${(metrics.error_rate * 100).toFixed(1)}%`
      });
    }
  }

  private addToBuffer(data: StreamingData): void {
    const bufferId = `${data.symbol}_${data.data_type}`;
    const buffer = this.dataBuffers.get(bufferId);
    
    if (!buffer) return;

    buffer.data.push(data);

    // Maintain buffer size
    if (buffer.data.length > buffer.max_size) {
      buffer.data = buffer.data.slice(-buffer.max_size);
    }

    buffer.last_cleanup = new Date();
  }

  private getNextSequenceNumber(providerId: string): number {
    const current = this.sequenceNumbers.get(providerId) || 0;
    const next = current + 1;
    this.sequenceNumbers.set(providerId, next);
    return next;
  }

  private handleConnectionClose(providerId: string): void {
    const status = this.connectionStatus.get(providerId);
    if (status) {
      status.status = 'disconnected';
      status.connected_since = null;
      status.subscriptions_active = 0;
    }

    this.connections.delete(providerId);

    this.createAlert({
      severity: 'warning',
      type: 'connection',
      provider: providerId,
      message: `Connection to ${providerId} lost`
    });

    this.emitEvent('connection', { provider: providerId, status: 'disconnected' });

    // Attempt reconnection
    setTimeout(() => {
      this.attemptReconnection(providerId);
    }, 5000);
  }

  private handleConnectionError(providerId: string, error: any): void {
    const status = this.connectionStatus.get(providerId);
    if (status) {
      status.status = 'error';
      status.error_message = error.message || String(error);
    }

    this.createAlert({
      severity: 'error',
      type: 'connection',
      provider: providerId,
      message: `Connection error for ${providerId}: ${status?.error_message}`
    });

    this.emitEvent('error', { provider: providerId, error });
  }

  private async attemptReconnection(providerId: string): Promise<void> {
    const status = this.connectionStatus.get(providerId);
    if (!status || status.status === 'connected') return;

    const config = this.providers.get(providerId);
    if (!config) return;

    if (status.reconnect_attempts >= config.retry_attempts) {
      this.createAlert({
        severity: 'critical',
        type: 'connection',
        provider: providerId,
        message: `Max reconnection attempts reached for ${providerId}`
      });
      return;
    }

    try {
      await this.connectProvider(providerId);
      
      // Resubscribe to all active subscriptions
      for (const [subscriptionId, subscriptionConfig] of this.subscriptions.entries()) {
        await this.sendSubscriptionRequest(providerId, subscriptionConfig);
      }

    } catch (error) {
      console.error(`Reconnection failed for ${providerId}:`, error);
      
      // Exponential backoff
      const delay = Math.min(30000, 1000 * Math.pow(2, status.reconnect_attempts));
      setTimeout(() => {
        this.attemptReconnection(providerId);
      }, delay);
    }
  }

  private performMaintenanceTasks(): void {
    // Clean up old data from buffers
    this.dataBuffers.forEach((buffer, bufferId) => {
      const now = new Date();
      const cutoffTime = now.getTime() - (24 * 60 * 60 * 1000); // 24 hours ago
      
      buffer.data = buffer.data.filter(item => item.timestamp.getTime() > cutoffTime);
    });

    // Clean up old alerts
    this.alerts = this.alerts.slice(-1000); // Keep last 1000 alerts

    // Update latency metrics
    this.connectionStatus.forEach((status, providerId) => {
      if (status.status === 'connected' && status.last_message) {
        const latency = Date.now() - status.last_message.getTime();
        status.latency_ms = latency;

        if (latency > 10000) { // 10 seconds
          this.createAlert({
            severity: 'warning',
            type: 'latency',
            provider: providerId,
            message: `High latency detected for ${providerId}: ${(latency/1000).toFixed(1)}s`
          });
        }
      }
    });
  }

  private createAlert(params: {
    severity: DataAlert['severity'];
    type: DataAlert['type'];
    provider: string;
    symbol?: string;
    message: string;
  }): void {
    const alert: DataAlert = {
      alert_id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      severity: params.severity,
      type: params.type,
      provider: params.provider,
      symbol: params.symbol,
      message: params.message,
      auto_resolved: false
    };

    this.alerts.push(alert);
    this.emitEvent('error', alert);
  }

  private emitEvent(eventType: string, data: any): void {
    const listeners = this.eventListeners.get(eventType) || [];
    listeners.forEach(listener => {
      try {
        listener(data);
      } catch (error) {
        console.error(`Error in event listener for ${eventType}:`, error);
      }
    });
  }

  // Public API methods
  public addEventListener(eventType: string, listener: Function): void {
    const listeners = this.eventListeners.get(eventType) || [];
    listeners.push(listener);
    this.eventListeners.set(eventType, listeners);
  }

  public removeEventListener(eventType: string, listener: Function): void {
    const listeners = this.eventListeners.get(eventType) || [];
    const index = listeners.indexOf(listener);
    if (index > -1) {
      listeners.splice(index, 1);
    }
  }

  public getLatestData(symbol: string, dataType: string, count: number = 100): StreamingData[] {
    const bufferId = `${symbol}_${dataType}`;
    const buffer = this.dataBuffers.get(bufferId);
    
    if (!buffer) return [];
    
    return buffer.data.slice(-count);
  }

  public getLatestBars(symbol: string, count: number = 100): MarketData[] {
    const barData = this.getLatestData(symbol, 'bar', count);
    return barData.map(item => item.data as BarData);
  }

  public getConnectionStatus(providerId?: string): ConnectionStatus | ConnectionStatus[] {
    if (providerId) {
      return this.connectionStatus.get(providerId) || {} as ConnectionStatus;
    }
    
    return Array.from(this.connectionStatus.values());
  }

  public getQualityMetrics(symbol?: string): DataQualityMetrics | DataQualityMetrics[] {
    if (symbol) {
      return this.qualityMetrics.get(symbol) || {} as DataQualityMetrics;
    }
    
    return Array.from(this.qualityMetrics.values());
  }

  public getAlerts(severity?: DataAlert['severity']): DataAlert[] {
    if (severity) {
      return this.alerts.filter(alert => alert.severity === severity);
    }
    
    return [...this.alerts];
  }

  public async unsubscribe(subscriptionId: string): Promise<void> {
    const config = this.subscriptions.get(subscriptionId);
    if (!config) return;

    // Send unsubscribe requests to all connected providers
    for (const [providerId, connection] of this.connections.entries()) {
      const provider = this.providers.get(providerId);
      if (!provider || !connection) continue;

      try {
        switch (provider.provider_type) {
          case 'polygon':
            this.sendPolygonUnsubscribe(connection, config);
            break;
          case 'alpaca':
            this.sendAlpacaUnsubscribe(connection, config);
            break;
        }

        const status = this.connectionStatus.get(providerId)!;
        status.subscriptions_active = Math.max(0, status.subscriptions_active - 1);

      } catch (error) {
        console.error(`Error unsubscribing from ${providerId}:`, error);
      }
    }

    this.subscriptions.delete(subscriptionId);
    console.log(`Subscription ${subscriptionId} removed`);
  }

  private sendPolygonUnsubscribe(connection: any, config: SubscriptionConfig): void {
    const subscriptions: string[] = [];
    
    config.symbols.forEach(symbol => {
      config.data_types.forEach(dataType => {
        switch (dataType) {
          case 'trades':
            subscriptions.push(`T.${symbol}`);
            break;
          case 'quotes':
            subscriptions.push(`Q.${symbol}`);
            break;
          case 'bars':
            subscriptions.push(`AM.${symbol}`);
            break;
        }
      });
    });

    connection.send(JSON.stringify({
      action: 'unsubscribe',
      params: subscriptions.join(',')
    }));
  }

  private sendAlpacaUnsubscribe(connection: any, config: SubscriptionConfig): void {
    const message: any = { action: 'unsubscribe' };
    
    config.data_types.forEach(dataType => {
      switch (dataType) {
        case 'trades':
          message.trades = config.symbols;
          break;
        case 'quotes':
          message.quotes = config.symbols;
          break;
        case 'bars':
          message.bars = config.symbols;
          break;
      }
    });

    connection.send(JSON.stringify(message));
  }

  public async disconnect(providerId: string): Promise<void> {
    const connection = this.connections.get(providerId);
    if (connection && connection.close) {
      connection.close();
    }

    this.connections.delete(providerId);
    
    const status = this.connectionStatus.get(providerId);
    if (status) {
      status.status = 'disconnected';
      status.connected_since = null;
      status.subscriptions_active = 0;
    }

    console.log(`Disconnected from provider ${providerId}`);
  }

  public async disconnectAll(): Promise<void> {
    const disconnectPromises = Array.from(this.connections.keys()).map(providerId =>
      this.disconnect(providerId)
    );

    await Promise.all(disconnectPromises);
    console.log('Disconnected from all providers');
  }
}

// Rate limiter utility class
class RateLimiter {
  private requests: number[] = [];
  private maxRequests: number;
  private windowMs: number;

  constructor(maxRequests: number, windowMs: number) {
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
  }

  public canMakeRequest(): boolean {
    const now = Date.now();
    
    // Remove old requests outside the window
    this.requests = this.requests.filter(time => now - time < this.windowMs);
    
    return this.requests.length < this.maxRequests;
  }

  public recordRequest(): void {
    this.requests.push(Date.now());
  }
}

// Export function for creating real-time data engine
export const createRealTimeDataEngine = (): RealTimeDataEngine => {
  return new RealTimeDataEngine();
};
