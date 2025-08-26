package com.alphintra.customersupport.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * Root level controller for general endpoints without prefix.
 */
@RestController
@RequestMapping("")
public class RootController {

    /**
     * Health check endpoint.
     */
    @GetMapping("/health")
    @CrossOrigin(originPatterns = "*", allowCredentials = "false")
    public ResponseEntity<Map<String, Object>> healthCheck() {
        Map<String, Object> response = new HashMap<>();
        response.put("status", "UP");
        response.put("service", "customer-support-service");
        return ResponseEntity.ok(response);
    }
}