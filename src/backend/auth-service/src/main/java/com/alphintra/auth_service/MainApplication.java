package com.alphintra.auth_service;

import java.util.concurrent.CountDownLatch;

public class MainApplication {
    public static void main(String[] args) {
        System.out.println("Auth Service application starting...");
        
        try {
            // Initialize database first using Docker network aware initializer
            System.out.println("Initializing database...");
            DockerNetworkDatabaseInitializer.initializeDatabase();
            System.out.println("Database initialization completed.");
            
            // Start the auth service
            System.out.println("Starting auth service...");
            startAuthService();
            
        } catch (Exception e) {
            System.err.println("Failed to start Auth Service: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
    
    private static void startAuthService() {
        try {
            // Create a CountDownLatch to keep the application running
            CountDownLatch latch = new CountDownLatch(1);
            
            // Add shutdown hook to gracefully shutdown
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                System.out.println("Shutting down Auth Service...");
                latch.countDown();
            }));
            
            System.out.println("Auth Service is now running. Press Ctrl+C to stop.");
            
            // Keep the application running
            latch.await();
            
        } catch (InterruptedException e) {
            System.err.println("Auth Service interrupted: " + e.getMessage());
            Thread.currentThread().interrupt();
        }
    }
}