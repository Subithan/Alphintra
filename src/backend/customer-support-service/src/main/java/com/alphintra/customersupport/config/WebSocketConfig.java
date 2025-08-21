package com.alphintra.customersupport.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.scheduling.TaskScheduler;
import org.springframework.scheduling.concurrent.ThreadPoolTaskScheduler;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;

/**
 * WebSocket configuration for real-time communication in customer support
 */
@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    @Value("${support.communication.websocket.heartbeat-interval:30000}")
    private long heartbeatInterval;

    @Bean
    public TaskScheduler supportWebSocketTaskScheduler() {
        ThreadPoolTaskScheduler scheduler = new ThreadPoolTaskScheduler();
        scheduler.setPoolSize(1);
        scheduler.setThreadNamePrefix("support-websocket-");
        scheduler.initialize();
        return scheduler;
    }

    @Override
    public void configureMessageBroker(MessageBrokerRegistry config) {
        // Enable simple broker for destinations prefixed with "/topic" and "/queue"
        config.enableSimpleBroker("/topic", "/queue")
                .setHeartbeatValue(new long[]{heartbeatInterval, heartbeatInterval})
                .setTaskScheduler(supportWebSocketTaskScheduler());
        
        // Set application destination prefix for messages bound for @MessageMapping methods
        config.setApplicationDestinationPrefixes("/app");
        
        // Set user destination prefix for user-specific messages
        config.setUserDestinationPrefix("/user");
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        // Register STOMP endpoint for WebSocket connection
        registry.addEndpoint("/ws")
                .setAllowedOriginPatterns("*")
                .withSockJS();
        
        // Register endpoint for support-specific connections
        registry.addEndpoint("/ws/support")
                .setAllowedOriginPatterns("*")
                .withSockJS();
        
        // Register endpoint for ticket-specific connections
        registry.addEndpoint("/ws/tickets/{ticketId}")
                .setAllowedOriginPatterns("*")
                .withSockJS();
    }
}