package com.alphabot.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.reactive.CorsWebFilter;
import org.springframework.web.cors.reactive.UrlBasedCorsConfigurationSource;
import org.springframework.cloud.gateway.filter.ratelimit.KeyResolver;
import reactor.core.publisher.Mono;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.cloud.gateway.filter.GatewayFilter;
import org.springframework.cloud.gateway.filter.factory.AbstractGatewayFilterFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;
import java.util.Arrays;
import java.util.Collections;

@SpringBootApplication
public class GatewayApplication {

    public static void main(String[] args) {
        SpringApplication.run(GatewayApplication.class, args);
    }

    @Bean
    public RouteLocator customRouteLocator(RouteLocatorBuilder builder) {
        return builder.routes()
                // Auth Service Routes
                .route("auth-service", r -> r.path("/api/auth/**")
                        .filters(f -> f
                                .stripPrefix(2)
                                .addRequestHeader("X-Gateway", "alphintra-Gateway")
                                .circuitBreaker(config -> config
                                        .setName("auth-service")
                                        .setFallbackUri("forward:/fallback/auth"))
                                .retry(config -> config.setRetries(3))
                                .requestRateLimiter(config -> config
                                        .setRateLimiter(redisRateLimiter())
                                        .setKeyResolver(userKeyResolver())))
                        .uri("http://auth-service:8001"))
                
                // Trading API Routes
                .route("trading-api", r -> r.path("/api/trading/**")
                        .filters(f -> f
                                .stripPrefix(2)
                                .addRequestHeader("X-Gateway", "alphintra-Gateway")
                                .circuitBreaker(config -> config
                                        .setName("trading-api")
                                        .setFallbackUri("forward:/fallback/trading"))
                                .retry(config -> config.setRetries(3))
                                .requestRateLimiter(config -> config
                                        .setRateLimiter(redisRateLimiter())
                                        .setKeyResolver(userKeyResolver())))
                        .uri("http://trading-api:8002"))
                
                // Strategy Engine Routes
                .route("strategy-engine", r -> r.path("/api/strategies/**")
                        .filters(f -> f
                                .stripPrefix(2)
                                .addRequestHeader("X-Gateway", "alphintra-Gateway")
                                .circuitBreaker(config -> config
                                        .setName("strategy-engine")
                                        .setFallbackUri("forward:/fallback/strategies"))
                                .retry(config -> config.setRetries(3))
                                .requestRateLimiter(config -> config
                                        .setRateLimiter(redisRateLimiter())
                                        .setKeyResolver(userKeyResolver())))
                        .uri("http://strategy-engine:8003"))
                
                // Broker Connector Routes
                .route("broker-connector", r -> r.path("/api/broker/**")
                        .filters(f -> f
                                .stripPrefix(2)
                                .addRequestHeader("X-Gateway", "alphintra-Gateway")
                                .circuitBreaker(config -> config
                                        .setName("broker-connector")
                                        .setFallbackUri("forward:/fallback/broker"))
                                .retry(config -> config.setRetries(3))
                                .requestRateLimiter(config -> config
                                        .setRateLimiter(redisRateLimiter())
                                        .setKeyResolver(userKeyResolver())))
                        .uri("http://broker-connector:8005"))
                
                // Broker Simulator Routes
                .route("broker-simulator", r -> r.path("/api/simulator/**")
                        .filters(f -> f
                                .stripPrefix(2)
                                .addRequestHeader("X-Gateway", "alphintra-Gateway")
                                .circuitBreaker(config -> config
                                        .setName("broker-simulator")
                                        .setFallbackUri("forward:/fallback/simulator"))
                                .retry(config -> config.setRetries(3))
                                .requestRateLimiter(config -> config
                                        .setRateLimiter(redisRateLimiter())
                                        .setKeyResolver(userKeyResolver())))
                        .uri("http://broker-simulator:8006"))
                
                // MLflow Routes
                .route("mlflow", r -> r.path("/api/mlflow/**")
                        .filters(f -> f
                                .stripPrefix(2)
                                .addRequestHeader("X-Gateway", "alphintra-Gateway")
                                .circuitBreaker(config -> config
                                        .setName("mlflow")
                                        .setFallbackUri("forward:/fallback/mlflow"))
                                .retry(config -> config.setRetries(3)))
                        .uri("http://mlflow:5000"))
                
                // Prometheus Routes (for monitoring)
                .route("prometheus", r -> r.path("/api/metrics/**")
                        .filters(f -> f
                                .stripPrefix(2)
                                .addRequestHeader("X-Gateway", "alphintra-Gateway"))
                        .uri("http://prometheus:9090"))
                
                // Grafana Routes (for dashboards)
                .route("grafana", r -> r.path("/api/dashboards/**")
                        .filters(f -> f
                                .stripPrefix(2)
                                .addRequestHeader("X-Gateway", "alphintra-Gateway"))
                        .uri("http://grafana:3000"))
                
                // WebSocket Routes for real-time data
                .route("websocket", r -> r.path("/ws/**")
                        .filters(f -> f
                                .addRequestHeader("X-Gateway", "alphintra-Gateway"))
                        .uri("ws://trading-api:8002"))
                
                // Health Check Routes
                .route("health", r -> r.path("/health")
                        .filters(f -> f
                                .addRequestHeader("X-Gateway", "alphintra-Gateway"))
                        .uri("http://localhost:8080"))
                
                .build();
    }

    @Bean
    public CorsWebFilter corsWebFilter() {
        CorsConfiguration corsConfig = new CorsConfiguration();
        corsConfig.setAllowedOriginPatterns(Arrays.asList("*"));
        corsConfig.setMaxAge(3600L);
        corsConfig.setAllowedMethods(Arrays.asList(
                HttpMethod.GET.name(),
                HttpMethod.POST.name(),
                HttpMethod.PUT.name(),
                HttpMethod.DELETE.name(),
                HttpMethod.OPTIONS.name(),
                HttpMethod.PATCH.name()
        ));
        corsConfig.setAllowedHeaders(Arrays.asList("*"));
        corsConfig.setAllowCredentials(true);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", corsConfig);

        return new CorsWebFilter(source);
    }

    @Bean
    public KeyResolver userKeyResolver() {
        return exchange -> {
            // Extract user ID from JWT token or use IP address as fallback
            String authHeader = exchange.getRequest().getHeaders().getFirst(HttpHeaders.AUTHORIZATION);
            if (authHeader != null && authHeader.startsWith("Bearer ")) {
                // In a real implementation, you would decode the JWT and extract user ID
                // For now, we'll use the token itself as the key
                return Mono.just(authHeader.substring(7));
            }
            // Fallback to IP address
            String clientIp = exchange.getRequest().getRemoteAddress() != null ?
                    exchange.getRequest().getRemoteAddress().getAddress().getHostAddress() : "unknown";
            return Mono.just(clientIp);
        };
    }

    @Bean
    public org.springframework.cloud.gateway.filter.ratelimit.RedisRateLimiter redisRateLimiter() {
        // Allow 100 requests per minute per user
        return new org.springframework.cloud.gateway.filter.ratelimit.RedisRateLimiter(100, 100, 1);
    }

    @Component
    public static class AuthenticationFilter extends AbstractGatewayFilterFactory<AuthenticationFilter.Config> {

        public AuthenticationFilter() {
            super(Config.class);
        }

        @Override
        public GatewayFilter apply(Config config) {
            return (exchange, chain) -> {
                String path = exchange.getRequest().getPath().value();
                
                // Skip authentication for public endpoints
                if (isPublicEndpoint(path)) {
                    return chain.filter(exchange);
                }

                String authHeader = exchange.getRequest().getHeaders().getFirst(HttpHeaders.AUTHORIZATION);
                
                if (authHeader == null || !authHeader.startsWith("Bearer ")) {
                    return handleUnauthorized(exchange);
                }

                String token = authHeader.substring(7);
                
                // In a real implementation, you would validate the JWT token here
                // For now, we'll just check if it's not empty
                if (token.isEmpty()) {
                    return handleUnauthorized(exchange);
                }

                // Add user information to request headers
                ServerWebExchange modifiedExchange = exchange.mutate()
                        .request(r -> r.header("X-User-Token", token))
                        .build();

                return chain.filter(modifiedExchange);
            };
        }

        private boolean isPublicEndpoint(String path) {
            return path.startsWith("/api/auth/login") ||
                   path.startsWith("/api/auth/register") ||
                   path.startsWith("/api/auth/verify") ||
                   path.startsWith("/health") ||
                   path.startsWith("/actuator");
        }

        private Mono<Void> handleUnauthorized(ServerWebExchange exchange) {
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }

        public static class Config {
            // Configuration properties if needed
        }
    }

    @Component
    public static class LoggingFilter extends AbstractGatewayFilterFactory<LoggingFilter.Config> {

        public LoggingFilter() {
            super(Config.class);
        }

        @Override
        public GatewayFilter apply(Config config) {
            return (exchange, chain) -> {
                long startTime = System.currentTimeMillis();
                String requestId = java.util.UUID.randomUUID().toString();
                
                // Add request ID to headers
                ServerWebExchange modifiedExchange = exchange.mutate()
                        .request(r -> r.header("X-Request-ID", requestId))
                        .build();

                System.out.println(String.format(
                        "[%s] %s %s - Request ID: %s",
                        java.time.LocalDateTime.now(),
                        exchange.getRequest().getMethod(),
                        exchange.getRequest().getPath(),
                        requestId
                ));

                return chain.filter(modifiedExchange).then(
                        Mono.fromRunnable(() -> {
                            long endTime = System.currentTimeMillis();
                            System.out.println(String.format(
                                    "[%s] %s %s - Request ID: %s - Duration: %dms - Status: %s",
                                    java.time.LocalDateTime.now(),
                                    exchange.getRequest().getMethod(),
                                    exchange.getRequest().getPath(),
                                    requestId,
                                    endTime - startTime,
                                    exchange.getResponse().getStatusCode()
                            ));
                        })
                );
            };
        }

        public static class Config {
            // Configuration properties if needed
        }
    }
}