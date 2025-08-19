'use client';

import SockJS from 'sockjs-client';
import { Client, StompSubscription, IMessage } from '@stomp/stompjs';

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

interface WebSocketConfig {
  url: string;
  reconnectInterval: number;
  maxReconnectAttempts: number;
  heartbeatInterval: number;
}

type WebSocketEventHandler = (data: any) => void;

export class SupportWebSocketClient {
  private stompClient: Client | null = null;
  private config: WebSocketConfig;
  private handlers: Map<string, WebSocketEventHandler[]> = new Map();
  private reconnectAttempts = 0;
  private isConnecting = false;
  private isDestroyed = false;
  private subscriptions: Map<string, StompSubscription> = new Map();
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private currentTicketId: string | null = null;

  constructor(config: Partial<WebSocketConfig> = {}) {
    this.config = {
      url: process.env.NEXT_PUBLIC_SUPPORT_API_URL || 'http://localhost:8010/api/customer-support',
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
      heartbeatInterval: 30000,
      ...config,
    };
  }

  connect(ticketId?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isDestroyed) {
        reject(new Error('WebSocket client has been destroyed'));
        return;
      }

      if (this.isConnecting || (this.stompClient && this.stompClient.connected)) {
        return;
      }

      this.isConnecting = true;
      
      try {
        // Create STOMP client with SockJS
        const wsEndpoint = ticketId 
          ? `${this.config.url}/ws/tickets/${ticketId}` 
          : `${this.config.url}/ws/support`;
        
        this.stompClient = new Client({
          webSocketFactory: () => new SockJS(wsEndpoint),
          debug: (str: string) => {
            console.log('STOMP Debug:', str);
          },
          reconnectDelay: this.config.reconnectInterval,
          heartbeatIncoming: this.config.heartbeatInterval,
          heartbeatOutgoing: this.config.heartbeatInterval,
        });

        this.stompClient.onConnect = (frame) => {
          console.log('STOMP connected:', frame);
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.currentTicketId = ticketId || null;
          
          // Subscribe to topics
          this.setupSubscriptions();
          
          this.emit('connected', {});
          resolve();
        };

        this.stompClient.onStompError = (frame) => {
          console.error('STOMP error:', frame);
          this.isConnecting = false;
          this.emit('error', { error: frame });
          reject(new Error(`STOMP error: ${frame.headers['message']}`));
        };

        this.stompClient.onWebSocketClose = (event) => {
          console.log('STOMP WebSocket closed:', event);
          this.isConnecting = false;
          this.clearSubscriptions();
          this.emit('disconnected', { code: event.code, reason: event.reason });
          
          // Auto-reconnect if appropriate
          if (!this.isDestroyed && this.shouldReconnect(event.code)) {
            this.scheduleReconnect();
          }
        };

        this.stompClient.onWebSocketError = (error) => {
          console.error('STOMP WebSocket error:', error);
          this.isConnecting = false;
          this.emit('error', { error });
          reject(error);
        };

        // Activate the client
        this.stompClient.activate();

      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  disconnect(): void {
    this.isDestroyed = true;
    this.clearSubscriptions();
    this.clearReconnectTimer();
    this.stopHeartbeat();
    
    if (this.stompClient && this.stompClient.connected) {
      this.stompClient.deactivate();
      this.stompClient = null;
    }
  }

  send(type: string, data: any): boolean {
    if (!this.stompClient || !this.stompClient.connected) {
      console.warn('STOMP client not connected, cannot send message');
      return false;
    }

    try {
      const message = {
        type,
        data,
        timestamp: new Date().toISOString(),
      };

      this.stompClient.publish({
        destination: `/app/${type}`,
        body: JSON.stringify(message)
      });
      return true;
    } catch (error) {
      console.error('Failed to send STOMP message:', error);
      return false;
    }
  }

  // Event handling
  on(event: string, handler: WebSocketEventHandler): void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, []);
    }
    this.handlers.get(event)!.push(handler);
  }

  off(event: string, handler?: WebSocketEventHandler): void {
    if (!this.handlers.has(event)) return;

    if (handler) {
      const handlers = this.handlers.get(event)!;
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    } else {
      this.handlers.delete(event);
    }
  }

  private emit(event: string, data: any): void {
    const handlers = this.handlers.get(event);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error('Error in WebSocket event handler:', error);
        }
      });
    }
  }

  private handleMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'ping':
        this.send('pong', {});
        break;
      case 'pong':
        // Heartbeat response received
        break;
      case 'new_message':
        this.emit('message', message.data);
        break;
      case 'ticket_updated':
        this.emit('ticket_update', message.data);
        break;
      case 'typing_start':
        this.emit('typing_start', message.data);
        break;
      case 'typing_stop':
        this.emit('typing_stop', message.data);
        break;
      case 'agent_status_changed':
        this.emit('agent_status_change', message.data);
        break;
      case 'notification':
        this.emit('notification', message.data);
        break;
      default:
        console.log('Unknown WebSocket message type:', message.type);
        this.emit('unknown_message', message);
    }
  }

  private getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token');
    }
    return null;
  }

  private shouldReconnect(closeCode: number): boolean {
    // Don't reconnect on certain close codes
    if (closeCode === 1000 || closeCode === 1001 || closeCode === 1005) {
      return false;
    }
    
    return this.reconnectAttempts < this.config.maxReconnectAttempts;
  }

  private setupSubscriptions(): void {
    if (!this.stompClient || !this.stompClient.connected) {
      return;
    }

    // Subscribe to user-specific messages
    const userSub = this.stompClient.subscribe('/user/queue/messages', (message: IMessage) => {
      try {
        const data = JSON.parse(message.body);
        this.handleMessage(data);
      } catch (error) {
        console.error('Error parsing user message:', error);
      }
    });
    this.subscriptions.set('user-messages', userSub);

    // Subscribe to general support topic
    const supportSub = this.stompClient.subscribe('/topic/support', (message: IMessage) => {
      try {
        const data = JSON.parse(message.body);
        this.handleMessage(data);
      } catch (error) {
        console.error('Error parsing support message:', error);
      }
    });
    this.subscriptions.set('support-topic', supportSub);

    // Subscribe to notifications
    const notificationSub = this.stompClient.subscribe('/topic/notifications', (message: IMessage) => {
      try {
        const data = JSON.parse(message.body);
        this.emit('notification', data);
      } catch (error) {
        console.error('Error parsing notification:', error);
      }
    });
    this.subscriptions.set('notifications', notificationSub);

    // Subscribe to ticket-specific topics if connected to a specific ticket
    if (this.currentTicketId) {
      const ticketSub = this.stompClient.subscribe(`/topic/tickets/${this.currentTicketId}`, (message: IMessage) => {
        try {
          const data = JSON.parse(message.body);
          this.handleMessage(data);
        } catch (error) {
          console.error('Error parsing ticket message:', error);
        }
      });
      this.subscriptions.set(`ticket-${this.currentTicketId}`, ticketSub);

      // Subscribe to ticket-specific typing indicators
      const typingSub = this.stompClient.subscribe(`/topic/tickets/${this.currentTicketId}/typing`, (message: IMessage) => {
        try {
          const data = JSON.parse(message.body);
          this.handleMessage(data);
        } catch (error) {
          console.error('Error parsing typing message:', error);
        }
      });
      this.subscriptions.set(`typing-${this.currentTicketId}`, typingSub);
    }
  }

  private clearSubscriptions(): void {
    this.subscriptions.forEach(subscription => {
      try {
        subscription.unsubscribe();
      } catch (error) {
        console.error('Error unsubscribing:', error);
      }
    });
    this.subscriptions.clear();
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    const delay = Math.min(
      this.config.reconnectInterval * Math.pow(2, this.reconnectAttempts),
      30000
    );

    console.log(`Scheduling reconnect in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    this.heartbeatTimer = setInterval(() => {
      if (this.stompClient && this.stompClient.connected) {
        this.send('ping', {});
      }
    }, this.config.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  // Utility methods
  isConnected(): boolean {
    return this.stompClient?.connected ?? false;
  }

  getConnectionState(): string {
    if (!this.stompClient) return 'disconnected';
    
    if (this.isConnecting) return 'connecting';
    if (this.stompClient.connected) return 'connected';
    if (this.isDestroyed) return 'destroyed';
    return 'disconnected';
  }

  // Specific support methods
  joinTicketRoom(ticketId: string): boolean {
    return this.send('join_ticket', { ticketId });
  }

  leaveTicketRoom(ticketId: string): boolean {
    return this.send('leave_ticket', { ticketId });
  }

  sendChatMessage(ticketId: string, message: string): boolean {
    return this.send('chat_message', {
      ticketId,
      message,
      timestamp: new Date().toISOString()
    });
  }

  sendTypingStart(ticketId: string, userId: string, userName: string): boolean {
    return this.send('typing_start', {
      ticketId,
      userId,
      userName
    });
  }

  sendTypingStop(ticketId: string, userId: string, userName: string): boolean {
    return this.send('typing_stop', {
      ticketId,
      userId,
      userName
    });
  }

  updateAgentStatus(agentId: string, status: string): boolean {
    return this.send('agent_status_update', {
      agentId,
      status
    });
  }
}

// Create singleton instance
export const supportWebSocket = new SupportWebSocketClient();

// Export default
export default supportWebSocket;