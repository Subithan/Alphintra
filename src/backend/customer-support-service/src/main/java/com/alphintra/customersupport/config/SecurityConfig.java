package com.alphintra.customersupport.config;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;

/**
 * Security configuration for the customer support service.
 */
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    /**
     * Development security configuration with disabled authentication.
     */
    @Bean
    @Profile({"local", "docker", "development"})
    public SecurityFilterChain developmentSecurityFilterChain(HttpSecurity http) throws Exception {
        return http
                .authorizeHttpRequests(auth -> auth
                    .anyRequest().permitAll() // Allow all requests without authentication
                )
                .csrf(csrf -> csrf.disable()) // Disable CSRF for development
                .cors(cors -> {}) // Enable CORS with default configuration
                .headers(headers -> headers.frameOptions().disable()) // Allow frames for development
                .build();
    }

    /**
     * Production security configuration (to be implemented).
     */
    @Bean
    @Profile("production")
    public SecurityFilterChain productionSecurityFilterChain(HttpSecurity http) throws Exception {
        return http
                .authorizeHttpRequests(auth -> auth
                    .requestMatchers("/actuator/health", "/actuator/info").permitAll()
                    .requestMatchers("/ws/**", "/api/customer-support/ws/**").permitAll() // Allow WebSocket connections
                    .requestMatchers("/tickets/categories", "/tickets/priorities", "/tickets/statuses").permitAll()
                    .anyRequest().authenticated()
                )
                .oauth2ResourceServer(oauth2 -> oauth2.jwt(jwt -> {}))
                .csrf(csrf -> csrf.disable()) // Disable CSRF for REST APIs
                .build();
    }
}