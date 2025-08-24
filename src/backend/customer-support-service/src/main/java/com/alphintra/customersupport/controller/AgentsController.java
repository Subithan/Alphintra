package com.alphintra.customersupport.controller;

import com.alphintra.customersupport.entity.SupportAgent;
import com.alphintra.customersupport.repository.SupportAgentRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * REST Controller for managing support agents.
 */
@RestController
@RequestMapping("/agents")
public class AgentsController {

    @Autowired
    private SupportAgentRepository supportAgentRepository;

    /**
     * Get all agents - endpoint for frontend dashboard.
     */
    @GetMapping
    @CrossOrigin(originPatterns = "*", allowCredentials = "false")
    public ResponseEntity<Map<String, Object>> getAllAgents() {
        try {
            List<SupportAgent> agents = supportAgentRepository.findAll();
            Map<String, Object> response = new HashMap<>();
            response.put("message", "Agents retrieved successfully from database");
            response.put("data", agents);
            response.put("total", agents.size());
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("message", "Failed to retrieve agents: " + e.getMessage());
            errorResponse.put("data", new Object[0]);
            errorResponse.put("error", true);
            return ResponseEntity.status(500).body(errorResponse);
        }
    }
}