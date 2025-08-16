package com.alphintra.customersupport;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
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
public class CustomerSupportApplication {

    public static void main(String[] args) {
        SpringApplication.run(CustomerSupportApplication.class, args);
    }
}