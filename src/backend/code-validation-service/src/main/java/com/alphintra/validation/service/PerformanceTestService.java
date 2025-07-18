package com.alphintra.validation.service;

import com.alphintra.validation.dto.*;
import org.springframework.stereotype.Service;
import org.springframework.scheduling.annotation.Async;

import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

@Service
public class PerformanceTestService {

    private final Map<String, PerformanceTestResponse> testResults = new ConcurrentHashMap<>();
    private final Map<String, Pattern> PERFORMANCE_PATTERNS = new HashMap<>();
    
    public PerformanceTestService() {
        initializePerformancePatterns();
    }

    private void initializePerformancePatterns() {
        // Inefficient patterns that impact performance
        PERFORMANCE_PATTERNS.put("nested_loops", Pattern.compile("for\\s+.*:\\s*\\n\\s*for\\s+.*:"));
        PERFORMANCE_PATTERNS.put("iterrows", Pattern.compile("\\.iterrows\\s*\\("));
        PERFORMANCE_PATTERNS.put("apply_lambda", Pattern.compile("\\.apply\\s*\\(\\s*lambda"));
        PERFORMANCE_PATTERNS.put("string_concatenation", Pattern.compile("\\+\\s*['\"].*['\"]"));
        PERFORMANCE_PATTERNS.put("list_comprehension_nested", Pattern.compile("\\[.*\\[.*for.*in.*\\].*for.*in.*\\]"));
        PERFORMANCE_PATTERNS.put("inefficient_search", Pattern.compile(".*in\\s+list\\s*\\("));
        PERFORMANCE_PATTERNS.put("repeated_computation", Pattern.compile("len\\s*\\(.*\\).*for.*in"));
        PERFORMANCE_PATTERNS.put("inefficient_sorting", Pattern.compile("sorted\\s*\\(.*\\).*for.*in"));
        PERFORMANCE_PATTERNS.put("unnecessary_copying", Pattern.compile("\\.copy\\s*\\(\\)"));
        PERFORMANCE_PATTERNS.put("inefficient_io", Pattern.compile("open\\s*\\(.*\\).*for.*in"));
    }

    @Async
    public CompletableFuture<PerformanceTestResponse> performPerformanceTest(PerformanceTestRequest request) {
        String testId = "test-" + UUID.randomUUID().toString();
        
        // Create initial response
        PerformanceTestResponse initialResponse = PerformanceTestResponse.builder()
            .testId(testId)
            .workflowId(request.getWorkflowId())
            .status("RUNNING")
            .success(false)
            .message("Performance test started")
            .timestamp(new Date())
            .build();
        
        testResults.put(testId, initialResponse);
        
        return CompletableFuture.supplyAsync(() -> {
            try {
                // Simulate performance testing
                Thread.sleep(3000); // Simulate test execution time
                
                // Perform static analysis
                List<PerformanceIssue> issues = analyzePerformanceIssues(request.getCode());
                
                // Simulate dynamic performance metrics
                PerformanceMetrics metrics = simulatePerformanceMetrics(request);
                
                // Generate overall assessment
                String complexityRating = analyzeComplexity(request.getCode());
                metrics = PerformanceMetrics.builder()
                    .executionTime(metrics.getExecutionTime())
                    .memoryUsage(metrics.getMemoryUsage())
                    .cpuUsage(metrics.getCpuUsage())
                    .operationsPerSecond(metrics.getOperationsPerSecond())
                    .throughput(metrics.getThroughput())
                    .complexityRating(complexityRating)
                    .build();
                
                boolean success = issues.stream().noneMatch(issue -> "HIGH".equals(issue.getSeverity()));
                
                PerformanceTestResponse response = PerformanceTestResponse.builder()
                    .testId(testId)
                    .workflowId(request.getWorkflowId())
                    .status("COMPLETED")
                    .success(success)
                    .message(success ? "Performance test completed successfully" : "Performance issues detected")
                    .metrics(metrics)
                    .issues(issues)
                    .timestamp(new Date())
                    .executionTimeMs(3000)
                    .build();
                
                testResults.put(testId, response);
                return response;
                
            } catch (InterruptedException e) {
                PerformanceTestResponse errorResponse = PerformanceTestResponse.builder()
                    .testId(testId)
                    .workflowId(request.getWorkflowId())
                    .status("FAILED")
                    .success(false)
                    .message("Performance test interrupted: " + e.getMessage())
                    .timestamp(new Date())
                    .build();
                
                testResults.put(testId, errorResponse);
                return errorResponse;
            }
        });
    }

    public PerformanceTestResponse getTestResults(String testId) {
        return testResults.get(testId);
    }

    private List<PerformanceIssue> analyzePerformanceIssues(String code) {
        List<PerformanceIssue> issues = new ArrayList<>();
        String[] lines = code.split("\n");
        
        // Check for performance anti-patterns
        for (Map.Entry<String, Pattern> entry : PERFORMANCE_PATTERNS.entrySet()) {
            String patternName = entry.getKey();
            Pattern pattern = entry.getValue();
            
            for (int i = 0; i < lines.length; i++) {
                String line = lines[i].trim();
                if (line.startsWith("#") || line.isEmpty()) continue;
                
                Matcher matcher = pattern.matcher(line);
                if (matcher.find()) {
                    issues.add(createPerformanceIssue(patternName, line, i + 1));
                }
            }
        }
        
        // Multi-line pattern analysis
        issues.addAll(analyzeMultiLinePatterns(code));
        
        // Algorithm complexity analysis
        issues.addAll(analyzeAlgorithmComplexity(code));
        
        return issues;
    }

    private List<PerformanceIssue> analyzeMultiLinePatterns(String code) {
        List<PerformanceIssue> issues = new ArrayList<>();
        
        // Check for nested loops
        if (code.contains("for") && countOccurrences(code, "for") > 1) {
            String[] lines = code.split("\n");
            int indent = 0;
            boolean inLoop = false;
            
            for (int i = 0; i < lines.length; i++) {
                String line = lines[i];
                if (line.trim().startsWith("for")) {
                    if (inLoop) {
                        issues.add(PerformanceIssue.builder()
                            .severity("HIGH")
                            .category("ALGORITHM")
                            .message("Nested loops detected - consider optimization")
                            .suggestion("Use vectorized operations or more efficient algorithms")
                            .line(i + 1)
                            .impact(8.0)
                            .build());
                    }
                    inLoop = true;
                    indent = getIndentLevel(line);
                } else if (line.trim().isEmpty() || getIndentLevel(line) <= indent) {
                    inLoop = false;
                }
            }
        }
        
        return issues;
    }

    private List<PerformanceIssue> analyzeAlgorithmComplexity(String code) {
        List<PerformanceIssue> issues = new ArrayList<>();
        
        // Check for potentially expensive operations
        if (code.contains("sort") && code.contains("for")) {
            issues.add(PerformanceIssue.builder()
                .severity("MEDIUM")
                .category("ALGORITHM")
                .message("Sorting inside loop detected")
                .suggestion("Move sorting outside the loop or use more efficient data structures")
                .line(0)
                .impact(6.0)
                .build());
        }
        
        // Check for database operations in loops
        if (code.contains("execute") && code.contains("for")) {
            issues.add(PerformanceIssue.builder()
                .severity("HIGH")
                .category("IO")
                .message("Database operations in loop detected")
                .suggestion("Use batch operations or prepare statements outside the loop")
                .line(0)
                .impact(9.0)
                .build());
        }
        
        return issues;
    }

    private PerformanceIssue createPerformanceIssue(String patternName, String line, int lineNumber) {
        switch (patternName) {
            case "iterrows":
                return PerformanceIssue.builder()
                    .severity("HIGH")
                    .category("MEMORY")
                    .message("Use of iterrows() detected - very slow for large datasets")
                    .suggestion("Use vectorized operations or .apply() instead")
                    .line(lineNumber)
                    .impact(8.0)
                    .build();
                    
            case "apply_lambda":
                return PerformanceIssue.builder()
                    .severity("MEDIUM")
                    .category("CPU")
                    .message("Lambda in apply() - consider vectorization")
                    .suggestion("Use numpy operations or built-in pandas methods")
                    .line(lineNumber)
                    .impact(6.0)
                    .build();
                    
            case "string_concatenation":
                return PerformanceIssue.builder()
                    .severity("MEDIUM")
                    .category("MEMORY")
                    .message("String concatenation in loop may be inefficient")
                    .suggestion("Use list and join() or f-strings")
                    .line(lineNumber)
                    .impact(5.0)
                    .build();
                    
            case "inefficient_search":
                return PerformanceIssue.builder()
                    .severity("MEDIUM")
                    .category("ALGORITHM")
                    .message("Linear search in converted list")
                    .suggestion("Use sets for membership testing")
                    .line(lineNumber)
                    .impact(7.0)
                    .build();
                    
            case "repeated_computation":
                return PerformanceIssue.builder()
                    .severity("MEDIUM")
                    .category("CPU")
                    .message("Repeated computation detected")
                    .suggestion("Store computed values outside the loop")
                    .line(lineNumber)
                    .impact(6.0)
                    .build();
                    
            default:
                return PerformanceIssue.builder()
                    .severity("LOW")
                    .category("GENERAL")
                    .message("Performance issue detected: " + patternName)
                    .suggestion("Review code for optimization opportunities")
                    .line(lineNumber)
                    .impact(3.0)
                    .build();
        }
    }

    private PerformanceMetrics simulatePerformanceMetrics(PerformanceTestRequest request) {
        // Simulate realistic performance metrics based on code complexity
        String code = request.getCode();
        int codeComplexity = calculateCodeComplexity(code);
        
        // Base metrics with variation based on complexity
        double executionTime = 0.5 + (codeComplexity * 0.1) + (Math.random() * 0.3);
        double memoryUsage = 50 + (codeComplexity * 10) + (Math.random() * 30);
        double cpuUsage = 20 + (codeComplexity * 5) + (Math.random() * 15);
        int operationsPerSecond = Math.max(100, 10000 - (codeComplexity * 500));
        double throughput = Math.max(10, 1000 - (codeComplexity * 50));
        
        return PerformanceMetrics.builder()
            .executionTime(executionTime)
            .memoryUsage(memoryUsage)
            .cpuUsage(cpuUsage)
            .operationsPerSecond(operationsPerSecond)
            .throughput(throughput)
            .complexityRating("O(n)")
            .build();
    }

    private String analyzeComplexity(String code) {
        int nestedLoops = countNestedLoops(code);
        boolean hasSorting = code.contains("sort");
        boolean hasSearch = code.contains("search") || code.contains("find");
        
        if (nestedLoops >= 3) {
            return "O(n³)";
        } else if (nestedLoops == 2) {
            return "O(n²)";
        } else if (nestedLoops == 1) {
            if (hasSorting) {
                return "O(n log n)";
            } else {
                return "O(n)";
            }
        } else if (hasSorting) {
            return "O(n log n)";
        } else {
            return "O(1)";
        }
    }

    private int calculateCodeComplexity(String code) {
        int complexity = 0;
        complexity += countOccurrences(code, "for") * 2;
        complexity += countOccurrences(code, "while") * 2;
        complexity += countOccurrences(code, "if") * 1;
        complexity += countOccurrences(code, "try") * 1;
        complexity += countNestedLoops(code) * 3;
        return complexity;
    }

    private int countNestedLoops(String code) {
        String[] lines = code.split("\n");
        int maxNesting = 0;
        int currentNesting = 0;
        
        for (String line : lines) {
            String trimmed = line.trim();
            if (trimmed.startsWith("for ") || trimmed.startsWith("while ")) {
                currentNesting++;
                maxNesting = Math.max(maxNesting, currentNesting);
            } else if (trimmed.isEmpty() || getIndentLevel(line) == 0) {
                currentNesting = 0;
            }
        }
        
        return maxNesting;
    }

    private int countOccurrences(String str, String substr) {
        return str.split(substr, -1).length - 1;
    }

    private int getIndentLevel(String line) {
        int indent = 0;
        for (char c : line.toCharArray()) {
            if (c == ' ') indent++;
            else if (c == '\t') indent += 4;
            else break;
        }
        return indent;
    }

    public void cleanup() {
        // Clean up old test results (keep last 100)
        if (testResults.size() > 100) {
            List<String> sortedKeys = new ArrayList<>(testResults.keySet());
            sortedKeys.sort((a, b) -> {
                Date dateA = testResults.get(a).getTimestamp();
                Date dateB = testResults.get(b).getTimestamp();
                return dateB.compareTo(dateA);
            });
            
            // Remove oldest entries
            for (int i = 100; i < sortedKeys.size(); i++) {
                testResults.remove(sortedKeys.get(i));
            }
        }
    }
}