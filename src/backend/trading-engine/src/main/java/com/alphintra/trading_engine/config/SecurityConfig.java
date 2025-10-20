package com.alphintra.trading_engine.config;
// import com.alphintra.trading_engine.service.JwtValidationFilter; // Disabled for testing

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.HttpStatusEntryPoint;
// import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;

import java.util.Arrays;
import java.util.List;

@Configuration
public class SecurityConfig {

    // private final JwtValidationFilter jwtValidationFilter; // Disabled for testing

    @Value("${jwt.secret:OTc0MjZhMWMtM2NmOS00OGZlLTk1MjEtNzYwNWRlZTg=}") // Shared with auth-service
    private String jwtSecret;

    // public SecurityConfig(JwtValidationFilter jwtValidationFilter) { // Disabled for testing
    //     this.jwtValidationFilter = jwtValidationFilter;
    // }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())
            .cors(cors -> cors.configurationSource(request -> {
                CorsConfiguration config = new CorsConfiguration();
                config.setAllowedOrigins(List.of("*")); // Adjust for specific origins
                config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
                config.setAllowedHeaders(Arrays.asList("authorization", "content-type", "x-auth-token", "Authorization"));
                return config;
            }))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/health", "/api/public/**", "/api/trading/**").permitAll() // Public endpoints
                .requestMatchers("/api/**").authenticated() // Protect API paths
                .anyRequest().permitAll() // Or .denyAll() for stricter
            )
            .sessionManagement(sess -> sess.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            // .addFilterBefore(jwtValidationFilter, UsernamePasswordAuthenticationFilter.class) // Disabled for testing
            .exceptionHandling(ex -> ex.authenticationEntryPoint(new HttpStatusEntryPoint(HttpStatus.UNAUTHORIZED)));

        return http.build();
    }
}