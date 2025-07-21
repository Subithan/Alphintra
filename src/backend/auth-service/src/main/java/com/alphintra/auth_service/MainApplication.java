// Path: Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/MainApplication.java
// Purpose: Spring Boot application entry point, unchanged but included for completeness to support Flyway migrations via pom.xml.

package com.alphintra.auth_service;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

// Removed: import java.util.concurrent.CountDownLatch; // No longer needed

@SpringBootApplication
public class MainApplication {
    public static void main(String[] args) { // Removed 'throws InterruptedException' as it's no longer needed
        SpringApplication.run(MainApplication.class, args);
        // Removed: new CountDownLatch(1).await(); // This line caused the application to hang
    }
}