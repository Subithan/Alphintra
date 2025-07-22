// Path: Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/MainApplication.java
// Purpose: Spring Boot application entry point, unchanged but included for completeness to support Flyway migrations via pom.xml.

package com.alphintra.auth_service;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import java.util.concurrent.CountDownLatch;

@SpringBootApplication
public class MainApplication {
    public static void main(String[] args) throws InterruptedException {
        SpringApplication.run(MainApplication.class, args);
        new CountDownLatch(1).await();
    }
}