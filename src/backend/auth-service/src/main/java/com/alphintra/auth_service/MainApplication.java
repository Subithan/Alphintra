package com.alphintra.auth_service;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

import java.util.concurrent.CountDownLatch;

@SpringBootApplication
public class MainApplication {
    public static void main(String[] args) throws InterruptedException {
        SpringApplication.run(MainApplication.class, args);
        new CountDownLatch(1).await();
    }

    @Bean
    public CommandLineRunner databaseInitializer() {
        return args -> DockerNetworkDatabaseInitializer.main(args);
    }
}