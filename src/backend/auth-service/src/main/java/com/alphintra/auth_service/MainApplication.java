// Path: Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/MainApplication.java
// Purpose: Spring Boot application entry point, with logging and graceful shutdown.

package com.alphintra.auth_service;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext; // For graceful shutdown

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@SpringBootApplication
public class MainApplication {

    private static final Logger logger = LoggerFactory.getLogger(MainApplication.class);

    public static void main(String[] args) {
        ConfigurableApplicationContext context = null; // Declare context outside try-catch
        try {
            logger.info("Starting Auth Service Spring Boot application...");
            context = SpringApplication.run(MainApplication.class, args);
            // After successful startup, context will not be null
            logger.info("Auth Service Spring Boot application started successfully!");

            // Add a shutdown hook to perform actions on graceful shutdown (e.g., via docker stop)
            final ConfigurableApplicationContext finalContext = context; // Effectively final for lambda
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                logger.info("Auth Service Spring Boot application is shutting down...");
                if (finalContext != null && finalContext.isRunning()) {
                    finalContext.close(); // Perform graceful shutdown of Spring context
                }
                logger.info("Auth Service Spring Boot application shutdown complete.");
            }));

        } catch (Exception e) {
            // Catch a general exception during application startup
            logger.error("Auth Service Spring Boot application failed to start!", e);
            // Exit with a non-zero status code to indicate failure to Docker/Kubernetes
            System.exit(1);
        }
    }
}


// // Path: Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/MainApplication.java
// // Purpose: Spring Boot application entry point, unchanged but included for completeness to support Flyway migrations via pom.xml.

// package com.alphintra.auth_service;

// import org.springframework.boot.SpringApplication;
// import org.springframework.boot.autoconfigure.SpringBootApplication;

// import java.util.concurrent.CountDownLatch;

// @SpringBootApplication
// public class MainApplication {
//     public static void main(String[] args) throws InterruptedException {
//         SpringApplication.run(MainApplication.class, args);
//         new CountDownLatch(1).await();
//     }
// }