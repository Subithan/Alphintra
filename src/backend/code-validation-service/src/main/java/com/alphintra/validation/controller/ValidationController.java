package com.alphintra.validation.controller;

import com.alphintra.validation.dto.*;
import com.alphintra.validation.service.CodeValidationService;
import com.alphintra.validation.service.SecurityScanService;
import com.alphintra.validation.service.PerformanceTestService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/api/validation")
@CrossOrigin(origins = {"http://localhost:3000", "https://alphintra.com"})
public class ValidationController {

    @Autowired
    private CodeValidationService codeValidationService;

    @Autowired
    private SecurityScanService securityScanService;

    @Autowired
    private PerformanceTestService performanceTestService;

    @PostMapping("/code/validate")
    public ResponseEntity<ValidationResponse> validateCode(@Valid @RequestBody CodeValidationRequest request) {
        try {
            ValidationResponse response = codeValidationService.validatePythonCode(
                request.getCode(), 
                request.getWorkflowId()
            );
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            ValidationResponse errorResponse = ValidationResponse.builder()
                .success(false)
                .message("Validation failed: " + e.getMessage())
                .build();
            return ResponseEntity.badRequest().body(errorResponse);
        }
    }

    @PostMapping("/security/scan")
    public ResponseEntity<SecurityScanResponse> performSecurityScan(@Valid @RequestBody SecurityScanRequest request) {
        try {
            SecurityScanResponse response = securityScanService.performSecurityScan(
                request.getCode(),
                request.getWorkflowId()
            );
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            SecurityScanResponse errorResponse = SecurityScanResponse.builder()
                .success(false)
                .message("Security scan failed: " + e.getMessage())
                .overallRisk("UNKNOWN")
                .build();
            return ResponseEntity.badRequest().body(errorResponse);
        }
    }

    @PostMapping("/performance/test")
    public ResponseEntity<CompletableFuture<PerformanceTestResponse>> performPerformanceTest(
            @Valid @RequestBody PerformanceTestRequest request) {
        try {
            CompletableFuture<PerformanceTestResponse> futureResponse = 
                performanceTestService.performPerformanceTest(request);
            return ResponseEntity.ok(futureResponse);
        } catch (Exception e) {
            CompletableFuture<PerformanceTestResponse> errorResponse = 
                CompletableFuture.completedFuture(
                    PerformanceTestResponse.builder()
                        .success(false)
                        .message("Performance test failed: " + e.getMessage())
                        .build()
                );
            return ResponseEntity.badRequest().body(errorResponse);
        }
    }

    @GetMapping("/test-results/{testId}")
    public ResponseEntity<PerformanceTestResponse> getTestResults(@PathVariable String testId) {
        try {
            PerformanceTestResponse response = performanceTestService.getTestResults(testId);
            if (response != null) {
                return ResponseEntity.ok(response);
            } else {
                return ResponseEntity.notFound().build();
            }
        } catch (Exception e) {
            return ResponseEntity.badRequest().build();
        }
    }

    @PostMapping("/model/validate")
    public ResponseEntity<ModelValidationResponse> validateModel(@Valid @RequestBody ModelValidationRequest request) {
        try {
            ModelValidationResponse response = codeValidationService.validateTrainedModel(
                request.getModelPath(),
                request.getDatasetPath(),
                request.getWorkflowId()
            );
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            ModelValidationResponse errorResponse = ModelValidationResponse.builder()
                .success(false)
                .message("Model validation failed: " + e.getMessage())
                .build();
            return ResponseEntity.badRequest().body(errorResponse);
        }
    }

    @GetMapping("/health")
    public ResponseEntity<String> healthCheck() {
        return ResponseEntity.ok("Code Validation Service is running");
    }
}