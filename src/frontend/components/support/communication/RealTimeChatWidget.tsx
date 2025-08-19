'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  MessageSquare, 
  Send, 
  Phone, 
  Video, 
  Paperclip, 
  Smile, 
  MoreVertical,
  CheckCircle,
  Clock,
  AlertCircle,
  Minimize2,
  Maximize2,
  X
} from 'lucide-react';
import { 
  customerSupportApi, 
  Communication, 
  CommunicationType,
  SenderType,
  CreateCommunicationRequest
} from '@/lib/api/customer-support-api';
import { formatDistanceToNow, format } from 'date-fns';
import { toast } from 'react-hot-toast';

interface RealTimeChatWidgetProps {
  ticketId: string;
  currentUserId: string;
  currentUserName: string;
  isAgent?: boolean;
  onClose?: () => void;
  className?: string;
}

interface ChatMessage extends Communication {
  isOwn: boolean;
  status?: 'sending' | 'sent' | 'failed';
}

export default function RealTimeChatWidget({
  ticketId,
  currentUserId,
  currentUserName,
  isAgent = false,
  onClose,
  className = ''
}: RealTimeChatWidgetProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [typingUsers, setTypingUsers] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadInitialMessages();
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, [ticketId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadInitialMessages = async () => {
    setIsLoading(true);
    try {
      const communications = await customerSupportApi.getTicketCommunications(ticketId);
      const chatMessages: ChatMessage[] = communications
        .filter(comm => 
          comm.communicationType === CommunicationType.MESSAGE && 
          !comm.isInternal
        )
        .map(comm => ({
          ...comm,
          isOwn: comm.senderId === currentUserId,
          status: 'sent' as const
        }));
      
      setMessages(chatMessages);
    } catch (error) {
      console.error('Failed to load messages:', error);
      toast.error('Failed to load chat messages');
    } finally {
      setIsLoading(false);
    }
  };

  const connectWebSocket = () => {
    try {
      // WebSocket connection would be implemented here
      // For now, we'll simulate the connection
      const ws = new WebSocket(`ws://localhost:8085/ws/tickets/${ticketId}/chat`);
      
      ws.onopen = () => {
        setIsConnected(true);
        console.log('Chat WebSocket connected');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log('Chat WebSocket disconnected');
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          if (wsRef.current?.readyState === WebSocket.CLOSED) {
            connectWebSocket();
          }
        }, 3000);
      };

      ws.onerror = (error) => {
        console.error('Chat WebSocket error:', error);
        setIsConnected(false);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      // Fallback to polling for real-time updates
      setUpPolling();
    }
  };

  const setUpPolling = () => {
    // Fallback polling mechanism
    const interval = setInterval(async () => {
      try {
        const communications = await customerSupportApi.getTicketCommunications(ticketId);
        const latestMessages = communications
          .filter(comm => 
            comm.communicationType === CommunicationType.MESSAGE && 
            !comm.isInternal
          )
          .map(comm => ({
            ...comm,
            isOwn: comm.senderId === currentUserId,
            status: 'sent' as const
          }));
        
        if (latestMessages.length > messages.length) {
          setMessages(latestMessages);
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 2000);

    return () => clearInterval(interval);
  };

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'new_message':
        const newMsg: ChatMessage = {
          ...data.message,
          isOwn: data.message.senderId === currentUserId,
          status: 'sent'
        };
        setMessages(prev => [...prev, newMsg]);
        break;
        
      case 'typing_start':
        if (data.userId !== currentUserId) {
          setTypingUsers(prev => [...prev.filter(id => id !== data.userId), data.userName]);
        }
        break;
        
      case 'typing_stop':
        setTypingUsers(prev => prev.filter(name => name !== data.userName));
        break;
        
      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || isSending) return;

    const messageContent = newMessage.trim();
    setNewMessage('');
    setIsSending(true);

    // Add optimistic message
    const optimisticMessage: ChatMessage = {
      communicationId: Date.now(), // Temporary ID
      ticketId,
      senderId: currentUserId,
      senderName: currentUserName,
      senderType: isAgent ? SenderType.AGENT : SenderType.USER,
      content: messageContent,
      communicationType: CommunicationType.MESSAGE,
      isInternal: false,
      createdAt: new Date().toISOString(),
      isOwn: true,
      status: 'sending'
    };

    setMessages(prev => [...prev, optimisticMessage]);

    try {
      const request: CreateCommunicationRequest = {
        content: messageContent,
        communicationType: CommunicationType.MESSAGE,
        isInternal: false
      };

      const sentMessage = await customerSupportApi.addCommunication(ticketId, request);
      
      // Update the optimistic message with real data
      setMessages(prev => prev.map(msg => 
        msg.communicationId === optimisticMessage.communicationId 
          ? { ...sentMessage, isOwn: true, status: 'sent' as const }
          : msg
      ));

      // Send via WebSocket for real-time updates
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'send_message',
          ticketId,
          message: sentMessage
        }));
      }

    } catch (error) {
      console.error('Failed to send message:', error);
      
      // Mark message as failed
      setMessages(prev => prev.map(msg => 
        msg.communicationId === optimisticMessage.communicationId 
          ? { ...msg, status: 'failed' as const }
          : msg
      ));
      
      toast.error('Failed to send message');
    } finally {
      setIsSending(false);
    }
  };

  const handleTyping = () => {
    if (!isTyping && wsRef.current?.readyState === WebSocket.OPEN) {
      setIsTyping(true);
      wsRef.current.send(JSON.stringify({
        type: 'typing_start',
        ticketId,
        userId: currentUserId,
        userName: currentUserName
      }));
    }

    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Set new timeout to stop typing indicator
    typingTimeoutRef.current = setTimeout(() => {
      setIsTyping(false);
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'typing_stop',
          ticketId,
          userId: currentUserId,
          userName: currentUserName
        }));
      }
    }, 1000);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatMessageTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      return format(date, 'HH:mm');
    } else {
      return format(date, 'MMM d, HH:mm');
    }
  };

  const getMessageStatusIcon = (status?: string) => {
    switch (status) {
      case 'sending':
        return <Clock className="w-3 h-3 text-gray-400" />;
      case 'sent':
        return <CheckCircle className="w-3 h-3 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-3 h-3 text-red-500" />;
      default:
        return null;
    }
  };

  if (isMinimized) {
    return (
      <div className={`fixed bottom-4 right-4 z-50 ${className}`}>
        <Button
          onClick={() => setIsMinimized(false)}
          className="rounded-full w-12 h-12 shadow-lg"
          size="sm"
        >
          <MessageSquare className="w-5 h-5" />
          {messages.some(msg => !msg.isOwn && !msg.readAt) && (
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></div>
          )}
        </Button>
      </div>
    );
  }

  return (
    <Card className={`fixed bottom-4 right-4 w-80 h-96 z-50 shadow-xl ${className}`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4" />
            Live Chat
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          </div>
        </CardTitle>
        
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" onClick={() => setIsMinimized(true)}>
            <Minimize2 className="w-4 h-4" />
          </Button>
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="p-0 flex flex-col h-80">
        {/* Messages Area */}
        <ScrollArea className="flex-1 px-4">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"></div>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-500 text-sm">
              <div className="text-center">
                <MessageSquare className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                <p>Start the conversation</p>
              </div>
            </div>
          ) : (
            <div className="space-y-3 py-4">
              {messages.map((message) => (
                <div
                  key={message.communicationId}
                  className={`flex ${message.isOwn ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[75%] rounded-lg px-3 py-2 ${
                      message.isOwn
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    {!message.isOwn && (
                      <div className="text-xs font-medium mb-1 opacity-75">
                        {message.senderDisplayName || message.senderName}
                      </div>
                    )}
                    
                    <div className="text-sm">{message.content}</div>
                    
                    <div className={`flex items-center justify-between mt-1 text-xs ${
                      message.isOwn ? 'text-blue-100' : 'text-gray-500'
                    }`}>
                      <span>{formatMessageTime(message.createdAt)}</span>
                      {message.isOwn && getMessageStatusIcon(message.status)}
                    </div>
                  </div>
                </div>
              ))}
              
              {/* Typing Indicator */}
              {typingUsers.length > 0 && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-lg px-3 py-2 max-w-[75%]">
                    <div className="text-xs text-gray-500 mb-1">
                      {typingUsers.join(', ')} {typingUsers.length === 1 ? 'is' : 'are'} typing...
                    </div>
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          )}
        </ScrollArea>

        {/* Input Area */}
        <div className="border-t p-3">
          <div className="flex items-center gap-2">
            <div className="flex-1 relative">
              <Input
                value={newMessage}
                onChange={(e) => {
                  setNewMessage(e.target.value);
                  handleTyping();
                }}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
                placeholder="Type a message..."
                disabled={!isConnected || isSending}
                className="pr-10"
              />
              
              <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                  <Paperclip className="w-3 h-3" />
                </Button>
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                  <Smile className="w-3 h-3" />
                </Button>
              </div>
            </div>
            
            <Button
              onClick={sendMessage}
              disabled={!newMessage.trim() || !isConnected || isSending}
              size="sm"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
          
          {!isConnected && (
            <div className="text-xs text-red-500 mt-1 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              Connection lost. Trying to reconnect...
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}