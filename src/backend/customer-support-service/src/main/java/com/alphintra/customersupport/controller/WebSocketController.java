package com.alphintra.customersupport.controller;

import com.alphintra.customersupport.dto.ChatMessageDto;
import com.alphintra.customersupport.dto.TypingEventDto;
import com.alphintra.customersupport.dto.NotificationDto;
import com.alphintra.customersupport.service.TicketService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.messaging.handler.annotation.DestinationVariable;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.messaging.handler.annotation.SendTo;
import org.springframework.messaging.simp.SimpMessageHeaderAccessor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.messaging.simp.annotation.SubscribeMapping;
import org.springframework.stereotype.Controller;

import java.security.Principal;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * WebSocket controller for handling real-time communication
 */
@Controller
public class WebSocketController {

    private static final Logger logger = LoggerFactory.getLogger(WebSocketController.class);

    @Autowired
    private SimpMessagingTemplate messagingTemplate;

    @Autowired
    private TicketService ticketService;

    // Track active users in ticket rooms
    private final Map<String, Map<String, String>> ticketRooms = new ConcurrentHashMap<>();
    
    // Track typing users
    private final Map<String, Map<String, LocalDateTime>> typingUsers = new ConcurrentHashMap<>();

    /**
     * Handle user joining a ticket room
     */
    @MessageMapping("/tickets/{ticketId}/join")
    public void joinTicketRoom(@DestinationVariable String ticketId, 
                              @Payload Map<String, Object> payload,
                              SimpMessageHeaderAccessor headerAccessor,
                              Principal principal) {
        String userId = (String) payload.get("userId");
        String userName = (String) payload.get("userName");
        String userType = (String) payload.get("userType");
        
        logger.info("User {} joining ticket room: {}", userId, ticketId);
        
        // Add user to ticket room
        ticketRooms.computeIfAbsent(ticketId, k -> new ConcurrentHashMap<>())
                   .put(userId, userName);
        
        // Store session attributes
        if (headerAccessor.getSessionAttributes() != null) {
            headerAccessor.getSessionAttributes().put("userId", userId);
            headerAccessor.getSessionAttributes().put("ticketId", ticketId);
            headerAccessor.getSessionAttributes().put("userType", userType);
        }
        
        // Notify other users in the room
        NotificationDto notification = new NotificationDto();
        notification.setType("user_joined");
        notification.setMessage(userName + " joined the conversation");
        notification.setTicketId(ticketId);
        notification.setTimestamp(LocalDateTime.now());
        
        messagingTemplate.convertAndSend("/topic/tickets/" + ticketId + "/notifications", notification);
    }

    /**
     * Handle user leaving a ticket room
     */
    @MessageMapping("/tickets/{ticketId}/leave")
    public void leaveTicketRoom(@DestinationVariable String ticketId,
                               @Payload Map<String, Object> payload) {
        String userId = (String) payload.get("userId");
        String userName = (String) payload.get("userName");
        
        logger.info("User {} leaving ticket room: {}", userId, ticketId);
        
        // Remove user from ticket room
        Map<String, String> room = ticketRooms.get(ticketId);
        if (room != null) {
            room.remove(userId);
            if (room.isEmpty()) {
                ticketRooms.remove(ticketId);
            }
        }
        
        // Remove from typing users
        Map<String, LocalDateTime> typing = typingUsers.get(ticketId);
        if (typing != null) {
            typing.remove(userId);
            if (typing.isEmpty()) {
                typingUsers.remove(ticketId);
            }
        }
        
        // Notify other users in the room
        NotificationDto notification = new NotificationDto();
        notification.setType("user_left");
        notification.setMessage(userName + " left the conversation");
        notification.setTicketId(ticketId);
        notification.setTimestamp(LocalDateTime.now());
        
        messagingTemplate.convertAndSend("/topic/tickets/" + ticketId + "/notifications", notification);
    }

    /**
     * Handle chat messages in ticket rooms
     */
    @MessageMapping("/tickets/{ticketId}/chat")
    @SendTo("/topic/tickets/{ticketId}/messages")
    public ChatMessageDto sendChatMessage(@DestinationVariable String ticketId,
                                         @Payload ChatMessageDto message,
                                         Principal principal) {
        logger.info("Received chat message for ticket {}: {}", ticketId, message.getMessage());
        
        // Set server-side timestamp
        message.setTimestamp(LocalDateTime.now());
        message.setTicketId(ticketId);
        
        // TODO: Save message to database
        // ticketService.saveChatMessage(ticketId, message);
        
        return message;
    }

    /**
     * Handle typing start events
     */
    @MessageMapping("/tickets/{ticketId}/typing/start")
    public void handleTypingStart(@DestinationVariable String ticketId,
                                 @Payload TypingEventDto typingEvent) {
        logger.debug("Typing start for ticket {}: {}", ticketId, typingEvent.getUserName());
        
        // Track typing user
        typingUsers.computeIfAbsent(ticketId, k -> new ConcurrentHashMap<>())
                   .put(typingEvent.getUserId(), LocalDateTime.now());
        
        // Broadcast typing event to other users
        messagingTemplate.convertAndSend("/topic/tickets/" + ticketId + "/typing", typingEvent);
    }

    /**
     * Handle typing stop events
     */
    @MessageMapping("/tickets/{ticketId}/typing/stop")
    public void handleTypingStop(@DestinationVariable String ticketId,
                                @Payload TypingEventDto typingEvent) {
        logger.debug("Typing stop for ticket {}: {}", ticketId, typingEvent.getUserName());
        
        // Remove from typing users
        Map<String, LocalDateTime> typing = typingUsers.get(ticketId);
        if (typing != null) {
            typing.remove(typingEvent.getUserId());
        }
        
        // Broadcast typing stop event
        messagingTemplate.convertAndSend("/topic/tickets/" + ticketId + "/typing", typingEvent);
    }

    /**
     * Handle agent status updates
     */
    @MessageMapping("/support/agent/status")
    public void updateAgentStatus(@Payload Map<String, Object> payload,
                                 Principal principal) {
        String agentId = (String) payload.get("agentId");
        String status = (String) payload.get("status");
        
        logger.info("Agent {} status updated to: {}", agentId, status);
        
        // Broadcast agent status change to support team
        NotificationDto notification = new NotificationDto();
        notification.setType("agent_status_change");
        notification.setMessage("Agent status updated");
        notification.setTimestamp(LocalDateTime.now());
        notification.setData(payload);
        
        messagingTemplate.convertAndSend("/topic/support/agent-status", notification);
    }

    /**
     * Handle subscription to ticket updates
     */
    @SubscribeMapping("/tickets/{ticketId}/updates")
    public NotificationDto subscribeToTicketUpdates(@DestinationVariable String ticketId,
                                                   Principal principal) {
        logger.info("User subscribed to ticket updates: {}", ticketId);
        
        NotificationDto notification = new NotificationDto();
        notification.setType("subscription_confirmed");
        notification.setMessage("Subscribed to ticket updates");
        notification.setTicketId(ticketId);
        notification.setTimestamp(LocalDateTime.now());
        
        return notification;
    }

    /**
     * Handle subscription to support team notifications
     */
    @SubscribeMapping("/support/notifications")
    public NotificationDto subscribeToSupportNotifications(Principal principal) {
        logger.info("User subscribed to support notifications");
        
        NotificationDto notification = new NotificationDto();
        notification.setType("subscription_confirmed");
        notification.setMessage("Subscribed to support notifications");
        notification.setTimestamp(LocalDateTime.now());
        
        return notification;
    }

    /**
     * Send notification to specific ticket room
     */
    public void sendTicketNotification(String ticketId, NotificationDto notification) {
        notification.setTicketId(ticketId);
        notification.setTimestamp(LocalDateTime.now());
        messagingTemplate.convertAndSend("/topic/tickets/" + ticketId + "/notifications", notification);
    }

    /**
     * Send notification to support team
     */
    public void sendSupportNotification(NotificationDto notification) {
        notification.setTimestamp(LocalDateTime.now());
        messagingTemplate.convertAndSend("/topic/support/notifications", notification);
    }

    /**
     * Send notification to specific user
     */
    public void sendUserNotification(String userId, NotificationDto notification) {
        notification.setTimestamp(LocalDateTime.now());
        messagingTemplate.convertAndSendToUser(userId, "/queue/notifications", notification);
    }
}