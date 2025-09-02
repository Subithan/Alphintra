package com.alphintra.customersupport;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.servlet.ServletComponentScan;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * Main application class for the Customer Support Service.
 * This service provides comprehensive support functionality for the Alphintra trading platform,
 * including ticketing, user assistance, knowledge base management, and AI-powered support tools.
 */
@SpringBootApplication
@EnableFeignClients
@EnableJpaRepositories
@EnableAsync
@EnableScheduling
@ServletComponentScan
public class CustomerSupportApplication {

    public static void main(String[] args) {
        // Initialize database before starting the application
        System.out.println("Initializing Customer Support Service database...");
        try {
            DockerNetworkDatabaseInitializer.initializeDatabase();
            System.out.println("Database initialization completed successfully.");
        } catch (Exception e) {
            System.err.println("Failed to initialize database: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }

        SpringApplication.run(CustomerSupportApplication.class, args);
    }
}