package com.alphintra.gateway.config;

import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Route Security Configuration for API Gateway
 * Ensures all microservice requests are properly routed and secured
 */
@Configuration
public class RouteSecurityConfig {

    @Bean
    public RouteLocator gatewayRoutes(RouteLocatorBuilder builder) {
        return builder.routes()
                // Trading API Routes
                .route("trading-service", r -> r.path("/api/trading/**")
                        .filters(f -> f
                                .addRequestHeader("X-Gateway-Routed", "true")
                                .addRequestHeader("X-Service-Type", "trading")
                                .addRequestHeader("X-Request-ID", "#{T(java.util.UUID).randomUUID().toString()}")
                                .circuitBreaker(c -> c
                                        .setName("trading-circuit-breaker")
                                        .setFallbackUri("forward:/fallback"))
                                .retry(retryConfig -> retryConfig.setRetries(3))
                        )
                        .uri("lb://trading-service"))
                
                // Risk Management Routes
                .route("risk-service", r -> r.path("/api/risk/**")
                        .filters(f -> f
                                .addRequestHeader("X-Gateway-Routed", "true")
                                .addRequestHeader("X-Service-Type", "risk")
                                .addRequestHeader("X-Request-ID", "#{T(java.util.UUID).randomUUID().toString()}")
                                .circuitBreaker(c -> c
                                        .setName("risk-circuit-breaker")
                                        .setFallbackUri("forward:/fallback"))
                                .retry(retryConfig -> retryConfig.setRetries(3))
                        )
                        .uri("lb://risk-service"))
                
                // Strategy Management Routes
                .route("strategy-service", r -> r.path("/api/strategy/**")
                        .filters(f -> f
                                .addRequestHeader("X-Gateway-Routed", "true")
                                .addRequestHeader("X-Service-Type", "strategy")
                                .addRequestHeader("X-Request-ID", "#{T(java.util.UUID).randomUUID().toString()}")
                                .circuitBreaker(c -> c
                                        .setName("strategy-circuit-breaker")
                                        .setFallbackUri("forward:/fallback"))
                                .retry(retryConfig -> retryConfig.setRetries(3))
                        )
                        .uri("lb://strategy-service"))
                
                // Broker Integration Routes
                .route("broker-service", r -> r.path("/api/broker/**")
                        .filters(f -> f
                                .addRequestHeader("X-Gateway-Routed", "true")
                                .addRequestHeader("X-Service-Type", "broker")
                                .addRequestHeader("X-Request-ID", "#{T(java.util.UUID).randomUUID().toString()}")
                                .circuitBreaker(c -> c
                                        .setName("broker-circuit-breaker")
                                        .setFallbackUri("forward:/fallback"))
                                .retry(retryConfig -> retryConfig.setRetries(3))
                        )
                        .uri("lb://broker-service"))
                
                // User Management Routes
                .route("user-service", r -> r.path("/api/user/**")
                        .filters(f -> f
                                .addRequestHeader("X-Gateway-Routed", "true")
                                .addRequestHeader("X-Service-Type", "user")
                                .addRequestHeader("X-Request-ID", "#{T(java.util.UUID).randomUUID().toString()}")
                                .circuitBreaker(c -> c
                                        .setName("user-circuit-breaker")
                                        .setFallbackUri("forward:/fallback"))
                                .retry(retryConfig -> retryConfig.setRetries(3))
                        )
                        .uri("lb://user-service"))
                
                // No-Code Platform Routes
                .route("no-code-service", r -> r.path("/api/no-code/**")
                        .filters(f -> f
                                .addRequestHeader("X-Gateway-Routed", "true")
                                .addRequestHeader("X-Service-Type", "no-code")
                                .addRequestHeader("X-Request-ID", "#{T(java.util.UUID).randomUUID().toString()}")
                                .circuitBreaker(c -> c
                                        .setName("no-code-circuit-breaker")
                                        .setFallbackUri("forward:/fallback"))
                                .retry(retryConfig -> retryConfig.setRetries(3))
                        )
                        .uri("lb://no-code-service"))
                
                // Authentication Routes (no circuit breaker for auth)
                .route("auth-service", r -> r.path("/api/auth/**")
                        .filters(f -> f
                                .addRequestHeader("X-Gateway-Routed", "true")
                                .addRequestHeader("X-Service-Type", "auth")
                                .addRequestHeader("X-Request-ID", "#{T(java.util.UUID).randomUUID().toString()}")
                        )
                        .uri("lb://auth-service"))
                
                // GraphQL Gateway Routes (secured)
                .route("graphql-gateway", r -> r.path("/graphql/**")
                        .filters(f -> f
                                .addRequestHeader("X-Gateway-Routed", "true")
                                .addRequestHeader("X-Service-Type", "graphql")
                                .addRequestHeader("X-Request-ID", "#{T(java.util.UUID).randomUUID().toString()}")
                                .circuitBreaker(c -> c
                                        .setName("graphql-circuit-breaker")
                                        .setFallbackUri("forward:/fallback"))
                                .retry(retryConfig -> retryConfig.setRetries(2))
                        )
                        .uri("lb://graphql-gateway"))
                
                // Notification Routes
                .route("notification-service", r -> r.path("/api/notification/**")
                        .filters(f -> f
                                .addRequestHeader("X-Gateway-Routed", "true")
                                .addRequestHeader("X-Service-Type", "notification")
                                .addRequestHeader("X-Request-ID", "#{T(java.util.UUID).randomUUID().toString()}")
                                .circuitBreaker(c -> c
                                        .setName("notification-circuit-breaker")
                                        .setFallbackUri("forward:/fallback"))
                                .retry(retryConfig -> retryConfig.setRetries(3))
                        )
                        .uri("lb://notification-service"))
                
                .build();
    }
}