import { EventEmitter } from 'events';

// Performance monitoring interfaces
export interface SystemMetrics {
  timestamp: Date;
  cpu: {
    usage: number; // 0-100%
    cores: number;
    loadAverage: number[];
  };
  memory: {
    total: number; // bytes
    used: number; // bytes
    free: number; // bytes
    usage: number; // 0-100%
  };
  disk: {
    total: number; // bytes
    used: number; // bytes
    free: number; // bytes
    usage: number; // 0-100%
    iops: number; // operations per second
  };
  network: {
    bytesReceived: number;
    bytesSent: number;
    packetsReceived: number;
    packetsSent: number;
    latency: number; // milliseconds
  };
  processes: {
    active: number;
    threads: number;
    fileDescriptors: number;
  };
}

export interface ApplicationMetrics {
  timestamp: Date;
  performance: {
    responseTime: number; // milliseconds
    throughput: number; // requests per second
    errorRate: number; // 0-100%
    activeConnections: number;
    queueLength: number;
  };
  database: {
    connectionPool: {
      active: number;
      idle: number;
      total: number;
    };
    queryTime: {
      average: number;
      p50: number;
      p95: number;
      p99: number;
    };
    slowQueries: number;
  };
  cache: {
    hitRate: number; // 0-100%
    missRate: number; // 0-100%
    evictions: number;
    memory: number; // bytes
  };
  garbageCollection: {
    frequency: number; // per minute
    duration: number; // milliseconds
    youngGenCollections: number;
    oldGenCollections: number;
  };
}

export interface TradingMetrics {
  timestamp: Date;
  strategies: {
    active: number;
    running: number;
    paused: number;
    stopped: number;
    errors: number;
  };
  executions: {
    total: number;
    successful: number;
    failed: number;
    avgExecutionTime: number; // milliseconds
    throughput: number; // executions per minute
  };
  marketData: {
    dataPoints: number;
    latency: number; // milliseconds
    qualityScore: number; // 0-100%
    sources: {
      connected: number;
      disconnected: number;
      total: number;
    };
  };
  trading: {
    ordersPlaced: number;
    ordersFilled: number;
    ordersRejected: number;
    avgSlippage: number; // basis points
    totalVolume: number;
    pnl: {
      realized: number;
      unrealized: number;
      total: number;
    };
  };
}

export interface AlertThreshold {
  id: string;
  name: string;
  description: string;
  metric: string;
  condition: 'gt' | 'lt' | 'eq' | 'gte' | 'lte' | 'change';
  value: number;
  duration: number; // milliseconds
  severity: 'low' | 'medium' | 'high' | 'critical';
  enabled: boolean;
  cooldown: number; // milliseconds
  actions: AlertAction[];
}

export interface AlertAction {
  type: 'email' | 'slack' | 'webhook' | 'log' | 'stop_strategy';
  configuration: Record<string, any>;
}

export interface Alert {
  id: string;
  thresholdId: string;
  timestamp: Date;
  severity: AlertThreshold['severity'];
  metric: string;
  value: number;
  threshold: number;
  message: string;
  resolved: boolean;
  resolvedAt?: Date;
  acknowledgedBy?: string;
  acknowledgedAt?: Date;
}

export interface MetricsSnapshot {
  timestamp: Date;
  system: SystemMetrics;
  application: ApplicationMetrics;
  trading: TradingMetrics;
}

export interface PerformanceReport {
  id: string;
  period: {
    start: Date;
    end: Date;
  };
  summary: {
    avgResponseTime: number;
    maxResponseTime: number;
    avgThroughput: number;
    totalRequests: number;
    errorCount: number;
    uptime: number; // percentage
  };
  trends: {
    responseTime: number[]; // hourly averages
    throughput: number[]; // hourly averages
    errorRate: number[]; // hourly averages
    cpuUsage: number[]; // hourly averages
    memoryUsage: number[]; // hourly averages
  };
  alerts: Alert[];
  recommendations: PerformanceRecommendation[];
  generatedAt: Date;
}

export interface PerformanceRecommendation {
  id: string;
  type: 'optimization' | 'scaling' | 'configuration' | 'monitoring';
  priority: 'low' | 'medium' | 'high';
  title: string;
  description: string;
  impact: string;
  effort: 'low' | 'medium' | 'high';
  category: string;
  metrics: string[];
}

// Performance monitoring system
export class PerformanceMonitor extends EventEmitter {
  private isRunning = false;
  private metrics: MetricsSnapshot[] = [];
  private alerts: Alert[] = [];
  private thresholds: Map<string, AlertThreshold> = new Map();
  private collectors: Map<string, MetricsCollector> = new Map();
  private monitoringInterval?: NodeJS.Timeout;
  private retentionPeriod = 7 * 24 * 60 * 60 * 1000; // 7 days

  constructor() {
    super();
    this.setupDefaultThresholds();
  }

  /**
   * Start performance monitoring
   */
  start(intervalMs: number = 60000): void {
    if (this.isRunning) {
      console.warn('Performance monitor is already running');
      return;
    }

    this.isRunning = true;
    console.log('Starting performance monitoring...');

    this.monitoringInterval = setInterval(async () => {
      try {
        await this.collectMetrics();
        this.checkThresholds();
        this.cleanupOldMetrics();
      } catch (error) {
        console.error('Error during metrics collection:', error);
        this.emit('error', error);
      }
    }, intervalMs);

    this.emit('started');
  }

  /**
   * Stop performance monitoring
   */
  stop(): void {
    if (!this.isRunning) {
      return;
    }

    this.isRunning = false;

    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = undefined;
    }

    console.log('Performance monitoring stopped');
    this.emit('stopped');
  }

  /**
   * Add metrics collector
   */
  addCollector(name: string, collector: MetricsCollector): void {
    this.collectors.set(name, collector);
  }

  /**
   * Remove metrics collector
   */
  removeCollector(name: string): void {
    this.collectors.delete(name);
  }

  /**
   * Add alert threshold
   */
  addThreshold(threshold: AlertThreshold): void {
    this.thresholds.set(threshold.id, threshold);
  }

  /**
   * Remove alert threshold
   */
  removeThreshold(thresholdId: string): void {
    this.thresholds.delete(thresholdId);
  }

  /**
   * Get current metrics
   */
  getCurrentMetrics(): MetricsSnapshot | undefined {
    return this.metrics[this.metrics.length - 1];
  }

  /**
   * Get metrics history
   */
  getMetricsHistory(startTime?: Date, endTime?: Date): MetricsSnapshot[] {
    let filtered = this.metrics;

    if (startTime) {
      filtered = filtered.filter(m => m.timestamp >= startTime);
    }

    if (endTime) {
      filtered = filtered.filter(m => m.timestamp <= endTime);
    }

    return filtered;
  }

  /**
   * Get active alerts
   */
  getActiveAlerts(): Alert[] {
    return this.alerts.filter(a => !a.resolved);
  }

  /**
   * Get all alerts
   */
  getAllAlerts(limit?: number): Alert[] {
    const sorted = [...this.alerts].sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
    return limit ? sorted.slice(0, limit) : sorted;
  }

  /**
   * Acknowledge alert
   */
  acknowledgeAlert(alertId: string, user: string): void {
    const alert = this.alerts.find(a => a.id === alertId);
    if (alert && !alert.acknowledgedBy) {
      alert.acknowledgedBy = user;
      alert.acknowledgedAt = new Date();
      this.emit('alertAcknowledged', alert);
    }
  }

  /**
   * Resolve alert
   */
  resolveAlert(alertId: string): void {
    const alert = this.alerts.find(a => a.id === alertId);
    if (alert && !alert.resolved) {
      alert.resolved = true;
      alert.resolvedAt = new Date();
      this.emit('alertResolved', alert);
    }
  }

  /**
   * Generate performance report
   */
  generateReport(startDate: Date, endDate: Date): PerformanceReport {
    const metrics = this.getMetricsHistory(startDate, endDate);
    const alerts = this.alerts.filter(a => 
      a.timestamp >= startDate && a.timestamp <= endDate
    );

    if (metrics.length === 0) {
      throw new Error('No metrics available for the specified period');
    }

    // Calculate summary statistics
    const responseTimes = metrics.map(m => m.application.performance.responseTime);
    const throughputs = metrics.map(m => m.application.performance.throughput);
    const errorRates = metrics.map(m => m.application.performance.errorRate);

    const summary = {
      avgResponseTime: this.average(responseTimes),
      maxResponseTime: Math.max(...responseTimes),
      avgThroughput: this.average(throughputs),
      totalRequests: throughputs.reduce((sum, t) => sum + t, 0),
      errorCount: alerts.length,
      uptime: this.calculateUptime(metrics)
    };

    // Generate hourly trends
    const trends = this.generateTrends(metrics, startDate, endDate);

    // Generate recommendations
    const recommendations = this.generateRecommendations(metrics, alerts);

    return {
      id: `report_${Date.now()}`,
      period: { start: startDate, end: endDate },
      summary,
      trends,
      alerts,
      recommendations,
      generatedAt: new Date()
    };
  }

  /**
   * Get system health status
   */
  getHealthStatus(): {
    status: 'healthy' | 'warning' | 'critical';
    score: number; // 0-100
    issues: string[];
    metrics: any;
  } {
    const current = this.getCurrentMetrics();
    if (!current) {
      return {
        status: 'critical',
        score: 0,
        issues: ['No metrics available'],
        metrics: null
      };
    }

    const issues: string[] = [];
    let score = 100;

    // Check CPU usage
    if (current.system.cpu.usage > 90) {
      issues.push('High CPU usage');
      score -= 20;
    } else if (current.system.cpu.usage > 75) {
      issues.push('Elevated CPU usage');
      score -= 10;
    }

    // Check memory usage
    if (current.system.memory.usage > 90) {
      issues.push('High memory usage');
      score -= 20;
    } else if (current.system.memory.usage > 80) {
      issues.push('Elevated memory usage');
      score -= 10;
    }

    // Check disk usage
    if (current.system.disk.usage > 95) {
      issues.push('Critical disk space');
      score -= 30;
    } else if (current.system.disk.usage > 85) {
      issues.push('Low disk space');
      score -= 15;
    }

    // Check error rate
    if (current.application.performance.errorRate > 5) {
      issues.push('High error rate');
      score -= 25;
    } else if (current.application.performance.errorRate > 1) {
      issues.push('Elevated error rate');
      score -= 10;
    }

    // Check response time
    if (current.application.performance.responseTime > 5000) {
      issues.push('Slow response times');
      score -= 15;
    } else if (current.application.performance.responseTime > 2000) {
      issues.push('Elevated response times');
      score -= 5;
    }

    let status: 'healthy' | 'warning' | 'critical';
    if (score >= 80) {
      status = 'healthy';
    } else if (score >= 60) {
      status = 'warning';
    } else {
      status = 'critical';
    }

    return {
      status,
      score: Math.max(0, score),
      issues,
      metrics: current
    };
  }

  private async collectMetrics(): Promise<void> {
    const timestamp = new Date();

    // Collect system metrics
    const systemMetrics = await this.collectSystemMetrics();

    // Collect application metrics
    const applicationMetrics = await this.collectApplicationMetrics();

    // Collect trading metrics
    const tradingMetrics = await this.collectTradingMetrics();

    const snapshot: MetricsSnapshot = {
      timestamp,
      system: systemMetrics,
      application: applicationMetrics,
      trading: tradingMetrics
    };

    this.metrics.push(snapshot);
    this.emit('metricsCollected', snapshot);
  }

  private async collectSystemMetrics(): Promise<SystemMetrics> {
    // In a browser environment, we can't access real system metrics
    // This would typically use Node.js APIs like os, process, etc.
    return {
      timestamp: new Date(),
      cpu: {
        usage: Math.random() * 100,
        cores: 4,
        loadAverage: [1.2, 1.5, 1.8]
      },
      memory: {
        total: 8 * 1024 * 1024 * 1024, // 8GB
        used: Math.random() * 6 * 1024 * 1024 * 1024, // Random usage up to 6GB
        free: 0,
        usage: 0
      },
      disk: {
        total: 500 * 1024 * 1024 * 1024, // 500GB
        used: Math.random() * 400 * 1024 * 1024 * 1024, // Random usage up to 400GB
        free: 0,
        usage: 0,
        iops: Math.random() * 1000
      },
      network: {
        bytesReceived: Math.random() * 1000000,
        bytesSent: Math.random() * 1000000,
        packetsReceived: Math.random() * 10000,
        packetsSent: Math.random() * 10000,
        latency: Math.random() * 100
      },
      processes: {
        active: Math.floor(Math.random() * 200) + 50,
        threads: Math.floor(Math.random() * 1000) + 200,
        fileDescriptors: Math.floor(Math.random() * 5000) + 1000
      }
    };
  }

  private async collectApplicationMetrics(): Promise<ApplicationMetrics> {
    // Collect metrics from various collectors
    const metrics: ApplicationMetrics = {
      timestamp: new Date(),
      performance: {
        responseTime: Math.random() * 1000 + 100,
        throughput: Math.random() * 1000 + 100,
        errorRate: Math.random() * 5,
        activeConnections: Math.floor(Math.random() * 100) + 10,
        queueLength: Math.floor(Math.random() * 50)
      },
      database: {
        connectionPool: {
          active: Math.floor(Math.random() * 20) + 5,
          idle: Math.floor(Math.random() * 10) + 2,
          total: 25
        },
        queryTime: {
          average: Math.random() * 100 + 10,
          p50: Math.random() * 80 + 5,
          p95: Math.random() * 200 + 50,
          p99: Math.random() * 500 + 100
        },
        slowQueries: Math.floor(Math.random() * 5)
      },
      cache: {
        hitRate: 80 + Math.random() * 15,
        missRate: 0,
        evictions: Math.floor(Math.random() * 10),
        memory: Math.random() * 100 * 1024 * 1024 // Random up to 100MB
      },
      garbageCollection: {
        frequency: Math.random() * 10 + 1,
        duration: Math.random() * 100 + 10,
        youngGenCollections: Math.floor(Math.random() * 20),
        oldGenCollections: Math.floor(Math.random() * 5)
      }
    };

    // Calculate derived metrics
    metrics.cache.missRate = 100 - metrics.cache.hitRate;

    return metrics;
  }

  private async collectTradingMetrics(): Promise<TradingMetrics> {
    return {
      timestamp: new Date(),
      strategies: {
        active: Math.floor(Math.random() * 10) + 5,
        running: Math.floor(Math.random() * 8) + 3,
        paused: Math.floor(Math.random() * 3),
        stopped: Math.floor(Math.random() * 2),
        errors: Math.floor(Math.random() * 2)
      },
      executions: {
        total: Math.floor(Math.random() * 1000) + 100,
        successful: Math.floor(Math.random() * 900) + 90,
        failed: Math.floor(Math.random() * 50),
        avgExecutionTime: Math.random() * 5000 + 500,
        throughput: Math.random() * 60 + 10
      },
      marketData: {
        dataPoints: Math.floor(Math.random() * 10000) + 1000,
        latency: Math.random() * 100 + 10,
        qualityScore: 85 + Math.random() * 10,
        sources: {
          connected: Math.floor(Math.random() * 5) + 3,
          disconnected: Math.floor(Math.random() * 2),
          total: 5
        }
      },
      trading: {
        ordersPlaced: Math.floor(Math.random() * 100) + 20,
        ordersFilled: Math.floor(Math.random() * 90) + 15,
        ordersRejected: Math.floor(Math.random() * 5),
        avgSlippage: Math.random() * 10 + 1,
        totalVolume: Math.random() * 1000000 + 100000,
        pnl: {
          realized: (Math.random() - 0.5) * 10000,
          unrealized: (Math.random() - 0.5) * 5000,
          total: 0
        }
      }
    };
  }

  private checkThresholds(): void {
    const current = this.getCurrentMetrics();
    if (!current) return;

    for (const threshold of this.thresholds.values()) {
      if (!threshold.enabled) continue;

      const value = this.getMetricValue(current, threshold.metric);
      if (value === undefined) continue;

      const shouldAlert = this.evaluateThreshold(value, threshold);
      
      if (shouldAlert) {
        // Check if we're in cooldown period
        const lastAlert = this.alerts
          .filter(a => a.thresholdId === threshold.id)
          .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())[0];

        if (lastAlert && (Date.now() - lastAlert.timestamp.getTime()) < threshold.cooldown) {
          continue; // Still in cooldown
        }

        this.createAlert(threshold, value);
      }
    }
  }

  private evaluateThreshold(value: number, threshold: AlertThreshold): boolean {
    switch (threshold.condition) {
      case 'gt': return value > threshold.value;
      case 'lt': return value < threshold.value;
      case 'gte': return value >= threshold.value;
      case 'lte': return value <= threshold.value;
      case 'eq': return value === threshold.value;
      case 'change':
        // For change detection, we'd need historical values
        return false;
      default: return false;
    }
  }

  private createAlert(threshold: AlertThreshold, value: number): void {
    const alert: Alert = {
      id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      thresholdId: threshold.id,
      timestamp: new Date(),
      severity: threshold.severity,
      metric: threshold.metric,
      value,
      threshold: threshold.value,
      message: `${threshold.name}: ${threshold.metric} is ${value} (threshold: ${threshold.value})`,
      resolved: false
    };

    this.alerts.push(alert);
    this.emit('alert', alert);

    // Execute alert actions
    this.executeAlertActions(alert, threshold);
  }

  private async executeAlertActions(alert: Alert, threshold: AlertThreshold): Promise<void> {
    for (const action of threshold.actions) {
      try {
        await this.executeAlertAction(action, alert);
      } catch (error) {
        console.error(`Failed to execute alert action ${action.type}:`, error);
      }
    }
  }

  private async executeAlertAction(action: AlertAction, alert: Alert): Promise<void> {
    switch (action.type) {
      case 'log':
        console.log(`ALERT: ${alert.message}`);
        break;
      
      case 'email':
        // Implementation would send email
        console.log(`Email alert: ${alert.message}`);
        break;
      
      case 'slack':
        // Implementation would send Slack message
        console.log(`Slack alert: ${alert.message}`);
        break;
      
      case 'webhook':
        // Implementation would call webhook
        console.log(`Webhook alert: ${alert.message}`);
        break;
      
      case 'stop_strategy':
        // Implementation would stop trading strategies
        console.log(`Stopping strategies due to alert: ${alert.message}`);
        this.emit('stopStrategies', alert);
        break;
    }
  }

  private getMetricValue(metrics: MetricsSnapshot, path: string): number | undefined {
    const parts = path.split('.');
    let current: any = metrics;
    
    for (const part of parts) {
      if (current && typeof current === 'object' && part in current) {
        current = current[part];
      } else {
        return undefined;
      }
    }
    
    return typeof current === 'number' ? current : undefined;
  }

  private cleanupOldMetrics(): void {
    const cutoff = Date.now() - this.retentionPeriod;
    this.metrics = this.metrics.filter(m => m.timestamp.getTime() > cutoff);
    this.alerts = this.alerts.filter(a => a.timestamp.getTime() > cutoff);
  }

  private setupDefaultThresholds(): void {
    const defaultThresholds: AlertThreshold[] = [
      {
        id: 'high_cpu_usage',
        name: 'High CPU Usage',
        description: 'CPU usage exceeds 90%',
        metric: 'system.cpu.usage',
        condition: 'gt',
        value: 90,
        duration: 60000, // 1 minute
        severity: 'high',
        enabled: true,
        cooldown: 300000, // 5 minutes
        actions: [{ type: 'log', configuration: {} }]
      },
      {
        id: 'high_memory_usage',
        name: 'High Memory Usage',
        description: 'Memory usage exceeds 90%',
        metric: 'system.memory.usage',
        condition: 'gt',
        value: 90,
        duration: 60000,
        severity: 'high',
        enabled: true,
        cooldown: 300000,
        actions: [{ type: 'log', configuration: {} }]
      },
      {
        id: 'high_error_rate',
        name: 'High Error Rate',
        description: 'Application error rate exceeds 5%',
        metric: 'application.performance.errorRate',
        condition: 'gt',
        value: 5,
        duration: 120000, // 2 minutes
        severity: 'critical',
        enabled: true,
        cooldown: 600000, // 10 minutes
        actions: [
          { type: 'log', configuration: {} },
          { type: 'stop_strategy', configuration: {} }
        ]
      },
      {
        id: 'slow_response_time',
        name: 'Slow Response Time',
        description: 'Response time exceeds 5 seconds',
        metric: 'application.performance.responseTime',
        condition: 'gt',
        value: 5000,
        duration: 180000, // 3 minutes
        severity: 'medium',
        enabled: true,
        cooldown: 300000,
        actions: [{ type: 'log', configuration: {} }]
      }
    ];

    defaultThresholds.forEach(threshold => {
      this.thresholds.set(threshold.id, threshold);
    });
  }

  private average(numbers: number[]): number {
    return numbers.length > 0 ? numbers.reduce((sum, n) => sum + n, 0) / numbers.length : 0;
  }

  private calculateUptime(metrics: MetricsSnapshot[]): number {
    // Simplified uptime calculation based on error rates
    const errorRates = metrics.map(m => m.application.performance.errorRate);
    const uptimeSlices = errorRates.map(rate => rate < 10 ? 1 : 0);
    return uptimeSlices.length > 0 ? (uptimeSlices.reduce((sum: number, u: number) => sum + u, 0) / uptimeSlices.length) * 100 : 0;
  }

  private generateTrends(metrics: MetricsSnapshot[], startDate: Date, endDate: Date): PerformanceReport['trends'] {
    // Generate hourly averages
    const hourlyBuckets = new Map<number, MetricsSnapshot[]>();
    
    metrics.forEach(m => {
      const hour = Math.floor(m.timestamp.getTime() / (60 * 60 * 1000));
      if (!hourlyBuckets.has(hour)) {
        hourlyBuckets.set(hour, []);
      }
      hourlyBuckets.get(hour)!.push(m);
    });

    const hours = Array.from(hourlyBuckets.keys()).sort();
    
    return {
      responseTime: hours.map(hour => {
        const hourMetrics = hourlyBuckets.get(hour)!;
        return this.average(hourMetrics.map(m => m.application.performance.responseTime));
      }),
      throughput: hours.map(hour => {
        const hourMetrics = hourlyBuckets.get(hour)!;
        return this.average(hourMetrics.map(m => m.application.performance.throughput));
      }),
      errorRate: hours.map(hour => {
        const hourMetrics = hourlyBuckets.get(hour)!;
        return this.average(hourMetrics.map(m => m.application.performance.errorRate));
      }),
      cpuUsage: hours.map(hour => {
        const hourMetrics = hourlyBuckets.get(hour)!;
        return this.average(hourMetrics.map(m => m.system.cpu.usage));
      }),
      memoryUsage: hours.map(hour => {
        const hourMetrics = hourlyBuckets.get(hour)!;
        return this.average(hourMetrics.map(m => m.system.memory.usage));
      })
    };
  }

  private generateRecommendations(metrics: MetricsSnapshot[], alerts: Alert[]): PerformanceRecommendation[] {
    const recommendations: PerformanceRecommendation[] = [];

    // Analyze metrics for optimization opportunities
    if (metrics.length > 0) {
      const latest = metrics[metrics.length - 1];
      const avgCpu = this.average(metrics.map(m => m.system.cpu.usage));
      const avgMemory = this.average(metrics.map(m => m.system.memory.usage));
      const avgResponseTime = this.average(metrics.map(m => m.application.performance.responseTime));

      if (avgCpu > 80) {
        recommendations.push({
          id: 'cpu_optimization',
          type: 'optimization',
          priority: 'high',
          title: 'Optimize CPU Usage',
          description: 'CPU usage is consistently high. Consider optimizing algorithms or scaling horizontally.',
          impact: 'Reduce response times and improve system stability',
          effort: 'medium',
          category: 'performance',
          metrics: ['system.cpu.usage']
        });
      }

      if (avgMemory > 85) {
        recommendations.push({
          id: 'memory_optimization',
          type: 'optimization',
          priority: 'high',
          title: 'Optimize Memory Usage',
          description: 'Memory usage is high. Review memory leaks and optimize data structures.',
          impact: 'Prevent out-of-memory errors and improve performance',
          effort: 'medium',
          category: 'performance',
          metrics: ['system.memory.usage']
        });
      }

      if (avgResponseTime > 2000) {
        recommendations.push({
          id: 'response_time_optimization',
          type: 'optimization',
          priority: 'medium',
          title: 'Improve Response Times',
          description: 'Response times are slower than optimal. Consider caching, database optimization, or CDN.',
          impact: 'Better user experience and higher throughput',
          effort: 'medium',
          category: 'performance',
          metrics: ['application.performance.responseTime']
        });
      }
    }

    // Analyze alert patterns
    const criticalAlerts = alerts.filter(a => a.severity === 'critical');
    if (criticalAlerts.length > 5) {
      recommendations.push({
        id: 'alert_frequency',
        type: 'monitoring',
        priority: 'high',
        title: 'Review Alert Thresholds',
        description: 'High number of critical alerts suggests thresholds may need adjustment.',
        impact: 'Reduce alert fatigue and improve monitoring effectiveness',
        effort: 'low',
        category: 'monitoring',
        metrics: []
      });
    }

    return recommendations;
  }
}

// Base class for metrics collectors
export abstract class MetricsCollector {
  abstract collect(): Promise<Record<string, number>>;
}

// Example collector for database metrics
export class DatabaseMetricsCollector extends MetricsCollector {
  constructor(private connectionString: string) {
    super();
  }

  async collect(): Promise<Record<string, number>> {
    // Implementation would query database for metrics
    return {
      activeConnections: Math.floor(Math.random() * 20) + 5,
      queryTime: Math.random() * 100 + 10,
      slowQueries: Math.floor(Math.random() * 5)
    };
  }
}

// Example collector for custom application metrics
export class ApplicationMetricsCollector extends MetricsCollector {
  private metrics = new Map<string, number>();

  increment(name: string, value: number = 1): void {
    this.metrics.set(name, (this.metrics.get(name) || 0) + value);
  }

  gauge(name: string, value: number): void {
    this.metrics.set(name, value);
  }

  async collect(): Promise<Record<string, number>> {
    return Object.fromEntries(this.metrics);
  }
}