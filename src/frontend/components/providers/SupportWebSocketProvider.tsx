'use client';

import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { supportWebSocket, SupportWebSocketClient } from '@/lib/websocket/support-websocket';
import { useAuth } from './AuthProvider';
import { toast } from 'react-hot-toast';

interface WebSocketContextType {
  ws: SupportWebSocketClient;
  isConnected: boolean;
  connectionState: string;
  connect: (ticketId?: string) => Promise<void>;
  disconnect: () => void;
  sendMessage: (type: string, data: any) => boolean;
  joinTicketRoom: (ticketId: string) => boolean;
  leaveTicketRoom: (ticketId: string) => boolean;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const useSupportWebSocket = (): WebSocketContextType => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useSupportWebSocket must be used within a SupportWebSocketProvider');
  }
  return context;
};

interface SupportWebSocketProviderProps {
  children: React.ReactNode;
}

export default function SupportWebSocketProvider({ children }: SupportWebSocketProviderProps) {
  const { user, isAuthenticated } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState('disconnected');
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  // Update connection state
  const updateConnectionState = useCallback(() => {
    const state = supportWebSocket.getConnectionState();
    setConnectionState(state);
    setIsConnected(state === 'connected');
  }, []);

  // Connect to WebSocket
  const connect = useCallback(async (ticketId?: string) => {
    if (!isAuthenticated) {
      console.warn('Cannot connect WebSocket: User not authenticated');
      return;
    }

    try {
      await supportWebSocket.connect(ticketId);
      setReconnectAttempts(0);
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      
      // Show user-friendly error after multiple failed attempts
      if (reconnectAttempts > 2) {
        toast.error('Connection issues detected. Some features may be limited.');
      }
      
      setReconnectAttempts(prev => prev + 1);
    }
  }, [isAuthenticated, reconnectAttempts]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    supportWebSocket.disconnect();
    updateConnectionState();
  }, [updateConnectionState]);

  // Send message through WebSocket
  const sendMessage = useCallback((type: string, data: any): boolean => {
    return supportWebSocket.send(type, data);
  }, []);

  // Join ticket room
  const joinTicketRoom = useCallback((ticketId: string): boolean => {
    return supportWebSocket.joinTicketRoom(ticketId);
  }, []);

  // Leave ticket room
  const leaveTicketRoom = useCallback((ticketId: string): boolean => {
    return supportWebSocket.leaveTicketRoom(ticketId);
  }, []);

  // Set up WebSocket event listeners
  useEffect(() => {
    const handleConnected = () => {
      console.log('WebSocket connected');
      updateConnectionState();
      setReconnectAttempts(0);
      
      // Send user identification
      if (user) {
        supportWebSocket.send('user_identify', {
          userId: user.id,
          userType: user.roles?.includes('SUPPORT_AGENT') ? 'agent' : 'user',
          agentId: user.agentId
        });
      }
    };

    const handleDisconnected = (data: any) => {
      console.log('WebSocket disconnected:', data);
      updateConnectionState();
      
      if (data.code !== 1000 && isAuthenticated) {
        // Auto-reconnect after a delay (handled by the WebSocket client)
        setTimeout(() => {
          if (supportWebSocket.getConnectionState() === 'closed') {
            connect();
          }
        }, 3000);
      }
    };

    const handleError = (data: any) => {
      console.error('WebSocket error:', data);
      updateConnectionState();
    };

    const handleMessage = (data: any) => {
      console.log('WebSocket message received:', data);
      // Messages are handled by individual components that subscribe to specific events
    };

    const handleNotification = (data: any) => {
      // Handle system notifications
      if (data.type === 'info') {
        toast.success(data.message);
      } else if (data.type === 'warning') {
        toast.error(data.message);
      } else if (data.type === 'error') {
        toast.error(data.message);
      }
    };

    // Subscribe to WebSocket events
    supportWebSocket.on('connected', handleConnected);
    supportWebSocket.on('disconnected', handleDisconnected);
    supportWebSocket.on('error', handleError);
    supportWebSocket.on('message', handleMessage);
    supportWebSocket.on('notification', handleNotification);

    // Cleanup on unmount
    return () => {
      supportWebSocket.off('connected', handleConnected);
      supportWebSocket.off('disconnected', handleDisconnected);
      supportWebSocket.off('error', handleError);
      supportWebSocket.off('message', handleMessage);
      supportWebSocket.off('notification', handleNotification);
    };
  }, [user, isAuthenticated, connect, updateConnectionState]);

  // Auto-connect when user is authenticated
  useEffect(() => {
    if (isAuthenticated && user && !isConnected) {
      connect();
    }
  }, [isAuthenticated, user, isConnected, connect]);

  // Disconnect when user logs out
  useEffect(() => {
    if (!isAuthenticated && isConnected) {
      disconnect();
    }
  }, [isAuthenticated, isConnected, disconnect]);

  // Handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Page is hidden, don't disconnect but pause heartbeat
        console.log('Page hidden, WebSocket will continue in background');
      } else {
        // Page is visible, ensure connection is active
        if (isAuthenticated && !isConnected) {
          connect();
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isAuthenticated, isConnected, connect]);

  // Handle browser/tab close
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (isConnected) {
        // Send a quick disconnect message
        supportWebSocket.send('user_disconnect', { userId: user?.id });
        disconnect();
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [isConnected, user, disconnect]);

  const contextValue: WebSocketContextType = {
    ws: supportWebSocket,
    isConnected,
    connectionState,
    connect,
    disconnect,
    sendMessage,
    joinTicketRoom,
    leaveTicketRoom
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
}