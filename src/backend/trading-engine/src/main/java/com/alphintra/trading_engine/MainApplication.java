package com.alphintra.trading_engine;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import jakarta.annotation.PostConstruct;

@SpringBootApplication
public class MainApplication {

    public static void main(String[] args) {
        SpringApplication.run(MainApplication.class, args);
        System.out.println("Trading Engine application started on port 8008.");
    }

    @PostConstruct
    public void init() {
        try {
            System.out.println("Initializing database...");
            DockerNetworkDatabaseInitializer.initializeDatabase();
            System.out.println("Database initialization completed.");
        } catch (Exception e) {
            System.err.println("Failed to initialize database: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
}