import { EventEmitter } from 'events';

// Notification interfaces
export interface Notification {
  id: string;
  type: NotificationType;
  severity: NotificationSeverity;
  title: string;
  message: string;
  timestamp: Date;
  source: string;
  category: NotificationCategory;
  data?: Record<string, any>;
  actions?: NotificationAction[];
  expiry?: Date;
  read: boolean;
  acknowledged: boolean;
  persistent: boolean;
}

export type NotificationType = 
  | 'alert'           // System alerts and warnings
  | 'trade'           // Trading-related notifications
  | 'system'          // System status updates
  | 'security'        // Security-related notifications
  | 'performance'     // Performance monitoring alerts
  | 'data'            // Data quality and availability
  | 'strategy'        // Strategy execution updates
  | 'user'            // User-initiated notifications
  | 'market'          // Market events and news
  | 'maintenance';    // Maintenance and updates

export type NotificationSeverity = 'info' | 'warning' | 'error' | 'critical' | 'success';

export type NotificationCategory = 
  | 'trading'
  | 'system'
  | 'security'
  | 'performance'
  | 'data_quality'
  | 'strategy'
  | 'market'
  | 'user'
  | 'maintenance';

export interface NotificationAction {
  id: string;
  label: string;
  type: 'button' | 'link' | 'command';
  style: 'primary' | 'secondary' | 'danger' | 'success';
  command?: string;
  url?: string;
  data?: Record<string, any>;
}

export interface NotificationChannel {
  id: string;
  name: string;
  type: ChannelType;
  enabled: boolean;
  configuration: ChannelConfiguration;
  filters: NotificationFilter[];
  rateLimits: RateLimit[];
}

export type ChannelType = 
  | 'inapp'           // In-application notifications
  | 'email'           // Email notifications
  | 'sms'             // SMS notifications
  | 'slack'           // Slack integration
  | 'discord'         // Discord integration
  | 'webhook'         // Custom webhook
  | 'push'            // Push notifications
  | 'telegram'        // Telegram bot
  | 'teams';          // Microsoft Teams

export interface ChannelConfiguration {
  // Email configuration
  smtpHost?: string;
  smtpPort?: number;
  smtpUser?: string;
  smtpPassword?: string;
  fromEmail?: string;
  toEmails?: string[];
  
  // SMS configuration
  twilioAccountSid?: string;
  twilioAuthToken?: string;
  twilioFromNumber?: string;
  toNumbers?: string[];
  
  // Slack configuration
  slackWebhookUrl?: string;
  slackChannel?: string;
  slackToken?: string;
  
  // Discord configuration
  discordWebhookUrl?: string;
  discordChannel?: string;
  
  // Webhook configuration
  webhookUrl?: string;
  webhookHeaders?: Record<string, string>;
  webhookMethod?: 'POST' | 'PUT' | 'PATCH';
  
  // Push notification configuration
  vapidPublicKey?: string;
  vapidPrivateKey?: string;
  
  // Telegram configuration
  telegramBotToken?: string;
  telegramChatId?: string;
}

export interface NotificationFilter {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  conditions: FilterCondition[];
  action: 'include' | 'exclude';
}

export interface FilterCondition {
  field: keyof Notification;
  operator: 'equals' | 'contains' | 'regex' | 'gt' | 'lt' | 'gte' | 'lte';
  value: any;
}

export interface RateLimit {
  timeWindow: number; // milliseconds
  maxNotifications: number;
  type: 'global' | 'per_type' | 'per_severity' | 'per_category';
}

export interface NotificationTemplate {
  id: string;
  name: string;
  type: NotificationType;
  severity: NotificationSeverity;
  titleTemplate: string;
  messageTemplate: string;
  channelOverrides: Record<string, Partial<NotificationTemplate>>;
  variables: TemplateVariable[];
}

export interface TemplateVariable {
  name: string;
  type: 'string' | 'number' | 'date' | 'boolean' | 'object';
  description: string;
  required: boolean;
  defaultValue?: any;
}

export interface NotificationSubscription {
  id: string;
  userId: string;
  channels: string[];
  types: NotificationType[];
  severities: NotificationSeverity[];
  categories: NotificationCategory[];
  filters: NotificationFilter[];
  quietHours?: {
    enabled: boolean;
    startTime: string; // HH:MM format
    endTime: string;   // HH:MM format
    timezone: string;
  };
  enabled: boolean;
}

export interface NotificationStats {
  period: {
    start: Date;
    end: Date;
  };
  total: number;
  byType: Record<NotificationType, number>;
  bySeverity: Record<NotificationSeverity, number>;
  byChannel: Record<string, number>;
  deliveryStats: {
    sent: number;
    delivered: number;
    failed: number;
    rate: number;
  };
  responseStats: {
    read: number;
    acknowledged: number;
    actionsClicked: number;
  };
}

// Main notification system
export class AlertSystem extends EventEmitter {
  private notifications: Map<string, Notification> = new Map();
  private channels: Map<string, NotificationChannel> = new Map();
  private templates: Map<string, NotificationTemplate> = new Map();
  private subscriptions: Map<string, NotificationSubscription> = new Map();
  private deliveryQueue: NotificationDelivery[] = [];
  private processing = false;
  private retentionPeriod = 30 * 24 * 60 * 60 * 1000; // 30 days

  constructor() {
    super();
    this.setupDefaultChannels();
    this.setupDefaultTemplates();
    this.startDeliveryProcessor();
  }

  /**
   * Send a notification
   */
  async notify(notification: Omit<Notification, 'id' | 'timestamp' | 'read' | 'acknowledged'>): Promise<string> {
    const id = `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const fullNotification: Notification = {
      id,
      timestamp: new Date(),
      read: false,
      acknowledged: false,
      ...notification,
      persistent: notification.persistent ?? (notification.severity === 'critical' || notification.severity === 'error')
    };

    this.notifications.set(id, fullNotification);
    
    // Queue for delivery
    await this.queueNotificationDelivery(fullNotification);
    
    this.emit('notification', fullNotification);
    return id;
  }

  /**
   * Send notification using template
   */
  async notifyFromTemplate(
    templateId: string, 
    variables: Record<string, any>,
    overrides?: Partial<Omit<Notification, 'id' | 'timestamp' | 'read' | 'acknowledged'>>
  ): Promise<string> {
    const template = this.templates.get(templateId);
    if (!template) {
      throw new Error(`Template ${templateId} not found`);
    }

    const title = this.renderTemplate(template.titleTemplate, variables);
    const message = this.renderTemplate(template.messageTemplate, variables);

    return this.notify({
      type: template.type,
      severity: template.severity,
      title,
      message,
      source: 'template',
      category: 'system',
      data: variables,
      persistent: template.severity === 'critical' || template.severity === 'error',
      ...overrides
    });
  }

  /**
   * Quick alert methods for common scenarios
   */
  async alertCritical(title: string, message: string, source: string = 'system', data?: any): Promise<string> {
    return this.notify({
      type: 'alert',
      severity: 'critical',
      title,
      message,
      source,
      category: 'system',
      data,
      persistent: true,
      actions: [{
        id: 'acknowledge',
        label: 'Acknowledge',
        type: 'button',
        style: 'danger',
        command: 'acknowledge'
      }]
    });
  }

  async alertWarning(title: string, message: string, source: string = 'system', data?: any): Promise<string> {
    return this.notify({
      type: 'alert',
      severity: 'warning',
      title,
      message,
      source,
      category: 'system',
      data,
      persistent: false
    });
  }

  async alertInfo(title: string, message: string, source: string = 'system', data?: any): Promise<string> {
    return this.notify({
      type: 'alert',
      severity: 'info',
      title,
      message,
      source,
      category: 'system',
      data,
      persistent: false
    });
  }

  async alertSuccess(title: string, message: string, source: string = 'system', data?: any): Promise<string> {
    return this.notify({
      type: 'alert',
      severity: 'success',
      title,
      message,
      source,
      category: 'system',
      data,
      persistent: false
    });
  }

  /**
   * Trading-specific alert methods
   */
  async alertTrade(action: string, symbol: string, quantity: number, price: number, data?: any): Promise<string> {
    return this.notify({
      type: 'trade',
      severity: 'info',
      title: `Trade Executed: ${action.toUpperCase()}`,
      message: `${action.toUpperCase()} ${quantity} ${symbol} at ${price}`,
      source: 'trading_engine',
      category: 'trading',
      data: { action, symbol, quantity, price, ...data },
      persistent: false
    });
  }

  async alertStrategyStart(strategyName: string, data?: any): Promise<string> {
    return this.notify({
      type: 'strategy',
      severity: 'info',
      title: 'Strategy Started',
      message: `Strategy "${strategyName}" has been started`,
      source: 'strategy_engine',
      category: 'strategy',
      data,
      persistent: false
    });
  }

  async alertStrategyStop(strategyName: string, reason: string, data?: any): Promise<string> {
    return this.notify({
      type: 'strategy',
      severity: 'warning',
      title: 'Strategy Stopped',
      message: `Strategy "${strategyName}" has been stopped: ${reason}`,
      source: 'strategy_engine',
      category: 'strategy',
      data,
      persistent: false
    });
  }

  async alertStrategyError(strategyName: string, error: string, data?: any): Promise<string> {
    return this.notify({
      type: 'strategy',
      severity: 'error',
      title: 'Strategy Error',
      message: `Strategy "${strategyName}" encountered an error: ${error}`,
      source: 'strategy_engine',
      category: 'strategy',
      data,
      persistent: true,
      actions: [{
        id: 'view_logs',
        label: 'View Logs',
        type: 'button',
        style: 'secondary',
        command: 'view_strategy_logs'
      }]
    });
  }

  /**
   * Market data alerts
   */
  async alertDataQuality(symbol: string, issue: string, severity: NotificationSeverity = 'warning', data?: any): Promise<string> {
    return this.notify({
      type: 'data',
      severity,
      title: 'Data Quality Issue',
      message: `Data quality issue for ${symbol}: ${issue}`,
      source: 'data_validator',
      category: 'data_quality',
      data: { symbol, issue, ...data },
      persistent: severity === 'critical' || severity === 'error'
    });
  }

  async alertDataConnection(source: string, status: 'connected' | 'disconnected', data?: any): Promise<string> {
    return this.notify({
      type: 'data',
      severity: status === 'connected' ? 'success' : 'error',
      title: `Data Source ${status === 'connected' ? 'Connected' : 'Disconnected'}`,
      message: `Data source "${source}" is now ${status}`,
      source: 'data_manager',
      category: 'data_quality',
      data,
      persistent: status === 'disconnected'
    });
  }

  /**
   * Performance alerts
   */
  async alertPerformance(metric: string, value: number, threshold: number, data?: any): Promise<string> {
    const severity: NotificationSeverity = value > threshold * 2 ? 'critical' : 
                                          value > threshold * 1.5 ? 'error' : 'warning';
    
    return this.notify({
      type: 'performance',
      severity,
      title: 'Performance Alert',
      message: `${metric} is ${value} (threshold: ${threshold})`,
      source: 'performance_monitor',
      category: 'performance',
      data: { metric, value, threshold, ...data },
      persistent: severity === 'critical' || severity === 'error'
    });
  }

  /**
   * Mark notification as read
   */
  markAsRead(notificationId: string): void {
    const notification = this.notifications.get(notificationId);
    if (notification && !notification.read) {
      notification.read = true;
      this.emit('notificationRead', notification);
    }
  }

  /**
   * Mark notification as acknowledged
   */
  acknowledge(notificationId: string): void {
    const notification = this.notifications.get(notificationId);
    if (notification && !notification.acknowledged) {
      notification.acknowledged = true;
      this.emit('notificationAcknowledged', notification);
    }
  }

  /**
   * Execute notification action
   */
  async executeAction(notificationId: string, actionId: string): Promise<void> {
    const notification = this.notifications.get(notificationId);
    if (!notification) {
      throw new Error('Notification not found');
    }

    const action = notification.actions?.find(a => a.id === actionId);
    if (!action) {
      throw new Error('Action not found');
    }

    switch (action.command) {
      case 'acknowledge':
        this.acknowledge(notificationId);
        break;
      case 'view_strategy_logs':
        this.emit('viewStrategyLogs', notification.data);
        break;
      default:
        this.emit('actionExecuted', { notification, action });
        break;
    }
  }

  /**
   * Get notifications with filtering and pagination
   */
  getNotifications(options?: {
    types?: NotificationType[];
    severities?: NotificationSeverity[];
    categories?: NotificationCategory[];
    read?: boolean;
    acknowledged?: boolean;
    limit?: number;
    offset?: number;
    sortBy?: 'timestamp' | 'severity';
    sortOrder?: 'asc' | 'desc';
  }): Notification[] {
    let notifications = Array.from(this.notifications.values());

    // Apply filters
    if (options?.types) {
      notifications = notifications.filter(n => options.types!.includes(n.type));
    }
    
    if (options?.severities) {
      notifications = notifications.filter(n => options.severities!.includes(n.severity));
    }
    
    if (options?.categories) {
      notifications = notifications.filter(n => options.categories!.includes(n.category));
    }
    
    if (options?.read !== undefined) {
      notifications = notifications.filter(n => n.read === options.read);
    }
    
    if (options?.acknowledged !== undefined) {
      notifications = notifications.filter(n => n.acknowledged === options.acknowledged);
    }

    // Sort
    const sortBy = options?.sortBy || 'timestamp';
    const sortOrder = options?.sortOrder || 'desc';
    
    notifications.sort((a, b) => {
      let compareValue = 0;
      
      if (sortBy === 'timestamp') {
        compareValue = a.timestamp.getTime() - b.timestamp.getTime();
      } else if (sortBy === 'severity') {
        const severityOrder = { 'critical': 4, 'error': 3, 'warning': 2, 'info': 1, 'success': 0 };
        compareValue = severityOrder[a.severity] - severityOrder[b.severity];
      }
      
      return sortOrder === 'asc' ? compareValue : -compareValue;
    });

    // Pagination
    const offset = options?.offset || 0;
    const limit = options?.limit;
    
    if (limit) {
      notifications = notifications.slice(offset, offset + limit);
    } else if (offset > 0) {
      notifications = notifications.slice(offset);
    }

    return notifications;
  }

  /**
   * Get unread notification count
   */
  getUnreadCount(types?: NotificationType[]): number {
    let notifications = Array.from(this.notifications.values()).filter(n => !n.read);
    
    if (types) {
      notifications = notifications.filter(n => types.includes(n.type));
    }
    
    return notifications.length;
  }

  /**
   * Clear notifications
   */
  clearNotifications(options?: {
    types?: NotificationType[];
    severities?: NotificationSeverity[];
    readOnly?: boolean;
    olderThan?: Date;
  }): number {
    let toDelete = Array.from(this.notifications.values());
    
    // Apply filters
    if (options?.types) {
      toDelete = toDelete.filter(n => options.types!.includes(n.type));
    }
    
    if (options?.severities) {
      toDelete = toDelete.filter(n => options.severities!.includes(n.severity));
    }
    
    if (options?.readOnly) {
      toDelete = toDelete.filter(n => n.read);
    }
    
    if (options?.olderThan) {
      toDelete = toDelete.filter(n => n.timestamp < options.olderThan!);
    }
    
    // Don't delete persistent notifications unless they're acknowledged
    toDelete = toDelete.filter(n => !n.persistent || n.acknowledged);
    
    toDelete.forEach(n => this.notifications.delete(n.id));
    
    return toDelete.length;
  }

  /**
   * Channel management
   */
  addChannel(channel: NotificationChannel): void {
    this.channels.set(channel.id, channel);
  }

  removeChannel(channelId: string): void {
    this.channels.delete(channelId);
  }

  getChannels(): NotificationChannel[] {
    return Array.from(this.channels.values());
  }

  /**
   * Template management
   */
  addTemplate(template: NotificationTemplate): void {
    this.templates.set(template.id, template);
  }

  removeTemplate(templateId: string): void {
    this.templates.delete(templateId);
  }

  getTemplates(): NotificationTemplate[] {
    return Array.from(this.templates.values());
  }

  /**
   * Subscription management
   */
  subscribe(subscription: NotificationSubscription): void {
    this.subscriptions.set(subscription.id, subscription);
  }

  unsubscribe(subscriptionId: string): void {
    this.subscriptions.delete(subscriptionId);
  }

  getUserSubscriptions(userId: string): NotificationSubscription[] {
    return Array.from(this.subscriptions.values()).filter(s => s.userId === userId);
  }

  /**
   * Statistics
   */
  getStats(startDate: Date, endDate: Date): NotificationStats {
    const notifications = Array.from(this.notifications.values()).filter(n => 
      n.timestamp >= startDate && n.timestamp <= endDate
    );

    const byType = notifications.reduce((acc, n) => {
      acc[n.type] = (acc[n.type] || 0) + 1;
      return acc;
    }, {} as Record<NotificationType, number>);

    const bySeverity = notifications.reduce((acc, n) => {
      acc[n.severity] = (acc[n.severity] || 0) + 1;
      return acc;
    }, {} as Record<NotificationSeverity, number>);

    // Mock delivery and response stats
    const total = notifications.length;
    const delivered = Math.floor(total * 0.95);
    const read = notifications.filter(n => n.read).length;
    const acknowledged = notifications.filter(n => n.acknowledged).length;

    return {
      period: { start: startDate, end: endDate },
      total,
      byType,
      bySeverity,
      byChannel: { 'inapp': total }, // Simplified
      deliveryStats: {
        sent: total,
        delivered,
        failed: total - delivered,
        rate: total > 0 ? (delivered / total) * 100 : 0
      },
      responseStats: {
        read,
        acknowledged,
        actionsClicked: Math.floor(acknowledged * 0.8)
      }
    };
  }

  // Private methods
  private async queueNotificationDelivery(notification: Notification): Promise<void> {
    // Find matching subscriptions
    const relevantSubscriptions = Array.from(this.subscriptions.values()).filter(sub => 
      this.matchesSubscription(notification, sub)
    );

    for (const subscription of relevantSubscriptions) {
      for (const channelId of subscription.channels) {
        const channel = this.channels.get(channelId);
        if (channel?.enabled) {
          this.deliveryQueue.push({
            id: `delivery_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            notificationId: notification.id,
            channelId,
            subscriptionId: subscription.id,
            status: 'pending',
            attempts: 0,
            scheduledAt: new Date(),
            notification,
            channel
          });
        }
      }
    }
  }

  private matchesSubscription(notification: Notification, subscription: NotificationSubscription): boolean {
    if (!subscription.enabled) return false;
    
    // Check quiet hours
    if (subscription.quietHours?.enabled && this.isInQuietHours(subscription.quietHours)) {
      return false;
    }
    
    // Check type filter
    if (subscription.types.length > 0 && !subscription.types.includes(notification.type)) {
      return false;
    }
    
    // Check severity filter
    if (subscription.severities.length > 0 && !subscription.severities.includes(notification.severity)) {
      return false;
    }
    
    // Check category filter
    if (subscription.categories.length > 0 && !subscription.categories.includes(notification.category)) {
      return false;
    }
    
    // Apply custom filters
    for (const filter of subscription.filters) {
      if (!this.evaluateFilter(notification, filter)) {
        return false;
      }
    }
    
    return true;
  }

  private isInQuietHours(quietHours: NonNullable<NotificationSubscription['quietHours']>): boolean {
    const now = new Date();
    const timeZone = quietHours.timezone;
    
    // Simplified implementation - would use proper timezone library in production
    const currentTime = now.toLocaleTimeString('en-US', { 
      hour12: false, 
      hour: '2-digit', 
      minute: '2-digit',
      timeZone 
    });
    
    return currentTime >= quietHours.startTime && currentTime <= quietHours.endTime;
  }

  private evaluateFilter(notification: Notification, filter: NotificationFilter): boolean {
    if (!filter.enabled) return true;
    
    const shouldInclude = filter.conditions.every(condition => {
      const fieldValue = notification[condition.field];
      
      switch (condition.operator) {
        case 'equals':
          return fieldValue === condition.value;
        case 'contains':
          return String(fieldValue).includes(String(condition.value));
        case 'regex':
          return new RegExp(condition.value).test(String(fieldValue));
        case 'gt':
          return Number(fieldValue) > Number(condition.value);
        case 'lt':
          return Number(fieldValue) < Number(condition.value);
        case 'gte':
          return Number(fieldValue) >= Number(condition.value);
        case 'lte':
          return Number(fieldValue) <= Number(condition.value);
        default:
          return true;
      }
    });
    
    return filter.action === 'include' ? shouldInclude : !shouldInclude;
  }

  private startDeliveryProcessor(): void {
    setInterval(() => {
      this.processDeliveryQueue();
    }, 5000); // Process every 5 seconds
  }

  private async processDeliveryQueue(): Promise<void> {
    if (this.processing) return;
    
    this.processing = true;
    
    try {
      const pendingDeliveries = this.deliveryQueue.filter(d => d.status === 'pending');
      
      for (const delivery of pendingDeliveries.slice(0, 10)) { // Process up to 10 at a time
        try {
          await this.deliverNotification(delivery);
          delivery.status = 'delivered';
          delivery.deliveredAt = new Date();
        } catch (error) {
          delivery.attempts++;
          delivery.lastError = String(error);
          
          if (delivery.attempts >= 3) {
            delivery.status = 'failed';
          } else {
            delivery.scheduledAt = new Date(Date.now() + Math.pow(2, delivery.attempts) * 60000); // Exponential backoff
          }
        }
      }
      
      // Clean up old deliveries
      this.deliveryQueue = this.deliveryQueue.filter(d => 
        d.status === 'pending' || 
        (d.deliveredAt && Date.now() - d.deliveredAt.getTime() < 24 * 60 * 60 * 1000)
      );
      
    } finally {
      this.processing = false;
    }
  }

  private async deliverNotification(delivery: NotificationDelivery): Promise<void> {
    const { channel, notification } = delivery;
    
    switch (channel.type) {
      case 'inapp':
        // In-app notifications are already available through getNotifications()
        break;
        
      case 'email':
        await this.sendEmailNotification(notification, channel);
        break;
        
      case 'slack':
        await this.sendSlackNotification(notification, channel);
        break;
        
      case 'webhook':
        await this.sendWebhookNotification(notification, channel);
        break;
        
      default:
        console.log(`Notification delivery for channel type ${channel.type} not implemented`);
    }
  }

  private async sendEmailNotification(notification: Notification, channel: NotificationChannel): Promise<void> {
    // Email delivery implementation would go here
    console.log(`Email notification: ${notification.title} - ${notification.message}`);
  }

  private async sendSlackNotification(notification: Notification, channel: NotificationChannel): Promise<void> {
    // Slack delivery implementation would go here
    console.log(`Slack notification: ${notification.title} - ${notification.message}`);
  }

  private async sendWebhookNotification(notification: Notification, channel: NotificationChannel): Promise<void> {
    // Webhook delivery implementation would go here
    console.log(`Webhook notification: ${notification.title} - ${notification.message}`);
  }

  private renderTemplate(template: string, variables: Record<string, any>): string {
    return template.replace(/\{\{(\w+)\}\}/g, (match, variable) => {
      return variables[variable] || match;
    });
  }

  private setupDefaultChannels(): void {
    // In-app notification channel
    this.channels.set('inapp', {
      id: 'inapp',
      name: 'In-App Notifications',
      type: 'inapp',
      enabled: true,
      configuration: {},
      filters: [],
      rateLimits: []
    });
  }

  private setupDefaultTemplates(): void {
    // Trading templates
    this.templates.set('trade_execution', {
      id: 'trade_execution',
      name: 'Trade Execution',
      type: 'trade',
      severity: 'info',
      titleTemplate: 'Trade Executed: {{action}}',
      messageTemplate: '{{action}} {{quantity}} {{symbol}} at {{price}}',
      channelOverrides: {},
      variables: [
        { name: 'action', type: 'string', description: 'Trade action (BUY/SELL)', required: true },
        { name: 'quantity', type: 'number', description: 'Trade quantity', required: true },
        { name: 'symbol', type: 'string', description: 'Trading symbol', required: true },
        { name: 'price', type: 'number', description: 'Execution price', required: true }
      ]
    });

    // Performance templates
    this.templates.set('performance_alert', {
      id: 'performance_alert',
      name: 'Performance Alert',
      type: 'performance',
      severity: 'warning',
      titleTemplate: 'Performance Alert: {{metric}}',
      messageTemplate: '{{metric}} is {{value}} (threshold: {{threshold}})',
      channelOverrides: {},
      variables: [
        { name: 'metric', type: 'string', description: 'Performance metric name', required: true },
        { name: 'value', type: 'number', description: 'Current value', required: true },
        { name: 'threshold', type: 'number', description: 'Alert threshold', required: true }
      ]
    });
  }

  private cleanupOldNotifications(): void {
    const cutoff = Date.now() - this.retentionPeriod;
    
    for (const [id, notification] of this.notifications.entries()) {
      if (notification.timestamp.getTime() < cutoff && !notification.persistent) {
        this.notifications.delete(id);
      }
    }
  }
}

// Delivery tracking interface
interface NotificationDelivery {
  id: string;
  notificationId: string;
  channelId: string;
  subscriptionId: string;
  status: 'pending' | 'delivered' | 'failed';
  attempts: number;
  scheduledAt: Date;
  deliveredAt?: Date;
  lastError?: string;
  notification: Notification;
  channel: NotificationChannel;
}

// Export singleton instance
export const alertSystem = new AlertSystem();