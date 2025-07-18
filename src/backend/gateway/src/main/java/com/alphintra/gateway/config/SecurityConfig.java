package com.alphintra.gateway.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.reactive.EnableWebFluxSecurity;
import org.springframework.security.config.web.server.ServerHttpSecurity;
import org.springframework.security.core.userdetails.MapReactiveUserDetailsService;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.server.SecurityWebFilterChain;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.reactive.CorsConfigurationSource;
import org.springframework.web.cors.reactive.UrlBasedCorsConfigurationSource;

import java.util.Arrays;

/**
 * Spring Security Configuration for API Gateway
 * Implements comprehensive security policies for microservices routing
 */
@Configuration
@EnableWebFluxSecurity
public class SecurityConfig {

    @Value("${gateway.security.jwt.secret:alphintra-jwt-secret-key-for-secure-trading-platform}")
    private String jwtSecret;

    @Value("${gateway.security.admin.username:admin}")
    private String adminUsername;

    @Value("${gateway.security.admin.password:admin123}")
    private String adminPassword;

    @Bean
    public SecurityWebFilterChain securityWebFilterChain(ServerHttpSecurity http) {
        return http
                // Disable CSRF for API Gateway (stateless)
                .csrf(csrf -> csrf.disable())
                
                // Configure CORS
                .cors(cors -> cors.configurationSource(corsConfigurationSource()))
                
                // Configure authorization rules
                .authorizeExchange(exchanges -> exchanges
                        // Public endpoints (no authentication required)
                        .pathMatchers("/actuator/health", "/actuator/info").permitAll()
                        .pathMatchers("/api/auth/login", "/api/auth/register").permitAll()
                        .pathMatchers("/api/auth/refresh", "/api/auth/validate").permitAll()
                        
                        // Admin endpoints (require admin role)
                        .pathMatchers("/actuator/**").hasRole("ADMIN")
                        .pathMatchers("/admin/**").hasRole("ADMIN")
                        
                        // GraphQL endpoints (require authentication)
                        .pathMatchers("/graphql/**").authenticated()
                        
                        // Microservice endpoints (require authentication)
                        .pathMatchers("/api/trading/**").authenticated()
                        .pathMatchers("/api/risk/**").authenticated()
                        .pathMatchers("/api/strategy/**").authenticated()
                        .pathMatchers("/api/broker/**").authenticated()
                        .pathMatchers("/api/user/**").authenticated()
                        .pathMatchers("/api/notification/**").authenticated()
                        .pathMatchers("/api/no-code/**").authenticated()
                        
                        // All other requests require authentication
                        .anyExchange().authenticated()
                )
                
                // Configure HTTP Basic Authentication for admin endpoints
                .httpBasic(httpBasic -> {})
                
                // Configure exception handling
                .exceptionHandling(exceptions -> exceptions
                        .authenticationEntryPoint((exchange, ex) -> {
                            exchange.getResponse().setStatusCode(org.springframework.http.HttpStatus.UNAUTHORIZED);
                            return exchange.getResponse().setComplete();
                        })
                        .accessDeniedHandler((exchange, denied) -> {
                            exchange.getResponse().setStatusCode(org.springframework.http.HttpStatus.FORBIDDEN);
                            return exchange.getResponse().setComplete();
                        })
                )
                
                .build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        
        // Allow specific origins in production, * for development
        configuration.setAllowedOriginPatterns(Arrays.asList("*"));
        
        // Allow common HTTP methods
        configuration.setAllowedMethods(Arrays.asList(
                "GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"
        ));
        
        // Allow common headers
        configuration.setAllowedHeaders(Arrays.asList(
                "Authorization", "Cache-Control", "Content-Type", 
                "X-Requested-With", "X-Forwarded-For", "X-Forwarded-Proto",
                "X-Forwarded-Host", "X-Request-ID", "X-Correlation-ID"
        ));
        
        // Allow credentials
        configuration.setAllowCredentials(true);
        
        // Expose headers that frontend might need
        configuration.setExposedHeaders(Arrays.asList(
                "X-Request-ID", "X-Correlation-ID", "X-Rate-Limit-Remaining"
        ));
        
        // Cache preflight requests for 1 hour
        configuration.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }

    @Bean
    public MapReactiveUserDetailsService userDetailsService() {
        UserDetails admin = User.builder()
                .username(adminUsername)
                .password(passwordEncoder().encode(adminPassword))
                .roles("ADMIN", "USER")
                .build();

        return new MapReactiveUserDetailsService(admin);
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder(12);
    }
}