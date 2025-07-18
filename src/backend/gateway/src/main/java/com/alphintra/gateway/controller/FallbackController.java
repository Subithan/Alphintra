package com.alphintra.gateway.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * Fallback Controller for Circuit Breaker
 * Provides fallback responses when microservices are unavailable
 */
@RestController
public class FallbackController {

    @GetMapping("/fallback")
    public ResponseEntity<Map<String, Object>> fallback() {
        Map<String, Object> response = new HashMap<>();
        response.put("error", "Service temporarily unavailable");
        response.put("message", "The requested service is currently experiencing issues. Please try again later.");
        response.put("status", HttpStatus.SERVICE_UNAVAILABLE.value());
        response.put("timestamp", LocalDateTime.now());
        response.put("fallback", true);
        
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(response);
    }

    @RequestMapping("/fallback/trading")
    public ResponseEntity<Map<String, Object>> tradingFallback() {
        Map<String, Object> response = new HashMap<>();
        response.put("error", "Trading service unavailable");
        response.put("message", "Trading operations are temporarily suspended for maintenance. Your positions are safe.");
        response.put("status", HttpStatus.SERVICE_UNAVAILABLE.value());
        response.put("timestamp", LocalDateTime.now());
        response.put("service", "trading");
        response.put("fallback", true);
        
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(response);
    }

    @RequestMapping("/fallback/risk")
    public ResponseEntity<Map<String, Object>> riskFallback() {
        Map<String, Object> response = new HashMap<>();
        response.put("error", "Risk service unavailable");
        response.put("message", "Risk assessment service is temporarily unavailable. Trading may be limited.");
        response.put("status", HttpStatus.SERVICE_UNAVAILABLE.value());
        response.put("timestamp", LocalDateTime.now());
        response.put("service", "risk");
        response.put("fallback", true);
        
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(response);
    }

    @RequestMapping("/fallback/graphql")
    public ResponseEntity<Map<String, Object>> graphqlFallback() {
        Map<String, Object> response = new HashMap<>();
        response.put("error", "GraphQL service unavailable");
        response.put("message", "GraphQL API is temporarily unavailable. Please use REST endpoints.");
        response.put("status", HttpStatus.SERVICE_UNAVAILABLE.value());
        response.put("timestamp", LocalDateTime.now());
        response.put("service", "graphql");
        response.put("fallback", true);
        
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(response);
    }
}