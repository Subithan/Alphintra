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

// package com.alphintra.trading_engine;

// import java.util.concurrent.CountDownLatch;

// public class MainApplication {
//     public static void main(String[] args) {
//         System.out.println("Trading Engine application starting...");
        
//         try {
//             // Initialize database first using Docker network aware initializer
//             System.out.println("Initializing database...");
//             DockerNetworkDatabaseInitializer.initializeDatabase();
//             System.out.println("Database initialization completed.");
            
//             // Start the trading engine services
//             System.out.println("Starting trading engine services...");
//             startTradingEngine();
            
//         } catch (Exception e) {
//             System.err.println("Failed to start Trading Engine: " + e.getMessage());
//             e.printStackTrace();
//             System.exit(1);
//         }
//     }
    
//     private static void startTradingEngine() {
//         try {
//             // Create a CountDownLatch to keep the application running
//             CountDownLatch latch = new CountDownLatch(1);
            
//             // Add shutdown hook to gracefully shutdown
//             Runtime.getRuntime().addShutdownHook(new Thread(() -> {
//                 System.out.println("Shutting down Trading Engine...");
//                 latch.countDown();
//             }));
            
//             System.out.println("Trading Engine is now running. Press Ctrl+C to stop.");
            
//             // Keep the application running
//             latch.await();
            
//         } catch (InterruptedException e) {
//             System.err.println("Trading Engine interrupted: " + e.getMessage());
//             Thread.currentThread().interrupt();
//         }
//     }
// }