package com.alphintra.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.reactive.CorsWebFilter;
import org.springframework.web.cors.reactive.UrlBasedCorsConfigurationSource;
import org.springframework.http.HttpMethod;
import java.util.Arrays;

@Configuration
@Profile("standalone")
public class StandaloneGatewayApplication {

    public static void main(String[] args) {
        SpringApplication.run(StandaloneGatewayApplication.class, args);
    }

    @Bean
    @Profile("standalone")
    public RouteLocator standaloneRouteLocator(RouteLocatorBuilder builder) {
        return builder.routes()
                // Health check route
                .route("health", r -> r.path("/health")
                        .filters(f -> f
                                .addRequestHeader("X-Request-Source", "gateway")
                                .addResponseHeader("X-Gateway-Status", "healthy"))
                        .uri("http://httpbin.org/status/200"))
                
                // Echo test route
                .route("echo", r -> r.path("/echo/**")
                        .filters(f -> f
                                .stripPrefix(1)
                                .addRequestHeader("X-Request-Source", "gateway"))
                        .uri("http://httpbin.org/anything"))
                
                // Test API route
                .route("test-api", r -> r.path("/api/test/**")
                        .filters(f -> f
                                .stripPrefix(2)
                                .addRequestHeader("X-Request-Source", "gateway")
                                .addRequestHeader("X-Service-Type", "test"))
                        .uri("http://httpbin.org/anything"))
                
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
}