package com.alphintra.auth_service;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.jdbc.core.JdbcTemplate;
import javax.sql.DataSource;
import java.sql.Timestamp;

@SpringBootApplication
public class MainApplication {

    public static void main(String[] args) {
        try {
            System.out.println("Initializing database...");
            DockerNetworkDatabaseInitializer.main(args);
            System.out.println("Database initialization completed.");
        } catch (Exception e) {
            System.err.println("Failed to initialize database: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
        SpringApplication.run(MainApplication.class, args);
        System.out.println("Trading Engine application started on port 8009.");
    }

    @Bean
    public CommandLineRunner databaseInitializer() {
        return args -> {
            // Avoid redundant initialization if already done in main
            System.out.println("Database initializer bean invoked.");
        };
    }

    @Bean
    public BCryptPasswordEncoder customPasswordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public JdbcTemplate jdbcTemplate(DataSource dataSource) {
        return new JdbcTemplate(dataSource);
    }

    // Remove CORS configuration (handled in SecurityConfig.java)
    // public WebMvcConfigurer corsConfigurer() { ... }

    
}