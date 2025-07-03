package com.alphintra.validation.dto;

import lombok.Builder;
import lombok.Data;
import java.util.Date;
import java.util.List;

@Data
@Builder
public class ValidationResponse {
    private boolean success;
    private String message;
    private String workflowId;
    private List<ValidationIssue> issues;
    private Date timestamp;
    private String validationId;
    private long executionTimeMs;
}

@Data
@Builder
public class ValidationIssue {
    private String severity; // ERROR, WARNING, INFO
    private String message;
    private String rule;
    private int line;
    private int column;
    private String suggestion;
    private String codeSnippet;
}

@Data
@Builder
public class CodeValidationRequest {
    private String code;
    private String workflowId;
    private String language; // python, r, etc.
    private ValidationOptions options;
}

@Data
@Builder
public class ValidationOptions {
    private boolean enableSecurityScan;
    private boolean enablePerformanceCheck;
    private boolean enableStyleCheck;
    private String securityLevel; // STRICT, MODERATE, LENIENT
}

@Data
@Builder
public class SecurityScanResponse {
    private boolean success;
    private String message;
    private String workflowId;
    private String overallRisk; // LOW, MEDIUM, HIGH, CRITICAL
    private List<SecurityIssue> securityIssues;
    private Date timestamp;
    private String scanId;
}

@Data
@Builder
public class SecurityIssue {
    private String severity; // LOW, MEDIUM, HIGH, CRITICAL
    private String category; // INJECTION, XSS, INSECURE_DESERIALIZATION, etc.
    private String message;
    private String rule;
    private int line;
    private String codeSnippet;
    private String remediation;
    private String cweId;
}

@Data
@Builder
public class SecurityScanRequest {
    private String code;
    private String workflowId;
    private String scanLevel; // BASIC, COMPREHENSIVE, DEEP
}

@Data
@Builder
public class PerformanceTestResponse {
    private boolean success;
    private String message;
    private String testId;
    private String workflowId;
    private String status; // PENDING, RUNNING, COMPLETED, FAILED
    private PerformanceMetrics metrics;
    private List<PerformanceIssue> issues;
    private Date timestamp;
    private long executionTimeMs;
}

@Data
@Builder
public class PerformanceMetrics {
    private double executionTime; // seconds
    private double memoryUsage; // MB
    private double cpuUsage; // percentage
    private int operationsPerSecond;
    private double throughput; // records/second
    private String complexityRating; // O(1), O(n), O(n²), etc.
}

@Data
@Builder
public class PerformanceIssue {
    private String severity; // LOW, MEDIUM, HIGH
    private String category; // MEMORY, CPU, IO, ALGORITHM
    private String message;
    private String suggestion;
    private int line;
    private double impact; // performance impact score
}

@Data
@Builder
public class PerformanceTestRequest {
    private String code;
    private String workflowId;
    private String datasetPath;
    private int testDurationSeconds;
    private PerformanceTestConfig config;
}

@Data
@Builder
public class PerformanceTestConfig {
    private int maxMemoryMB;
    private int maxExecutionTimeSeconds;
    private int datasetSizeLimit;
    private boolean enableMemoryProfiling;
    private boolean enableCpuProfiling;
}

@Data
@Builder
public class ModelValidationResponse {
    private boolean success;
    private String message;
    private String workflowId;
    private String modelPath;
    private double accuracy;
    private java.util.Map<String, Object> performanceMetrics;
    private List<ValidationIssue> issues;
    private Date timestamp;
    private String validationId;
}

@Data
@Builder
public class ModelValidationRequest {
    private String modelPath;
    private String datasetPath;
    private String workflowId;
    private ModelValidationConfig config;
}

@Data
@Builder
public class ModelValidationConfig {
    private double minAccuracy;
    private double minSharpeRatio;
    private double maxDrawdown;
    private boolean enableBenchmarkComparison;
    private String benchmarkStrategy;
}