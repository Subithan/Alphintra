package com.alphintra.gateway.config;

import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class GatewayConfig {

    @Bean
    public RouteLocator customRouteLocator(RouteLocatorBuilder builder) {
        return builder.routes()
                .route("auth-service", r -> r.path("/api/v1/auth/**")
                        .uri("lb://auth-service"))
                .route("trading-service", r -> r.path("/api/v1/trading/**")
                        .uri("lb://trading-service"))
                .route("strategy-service", r -> r.path("/api/v1/strategy/**")
                        .uri("lb://strategy-service"))
                .route("risk-service", r -> r.path("/api/v1/risk/**")
                        .uri("lb://risk-service"))
                .route("no-code-service", r -> r.path("/api/v1/no-code/**")
                        .uri("lb://no-code-service"))
                .route("broker-service", r -> r.path("/api/v1/broker/**")
                        .uri("lb://broker-service"))
                .route("notification-service", r -> r.path("/api/v1/notifications/**")
                        .uri("lb://notification-service"))
                .route("graphql-service", r -> r.path("/graphql/**")
                        .uri("lb://graphql-service"))
                .build();
    }
}