package com.alphintra.validation.service;

import com.alphintra.validation.dto.*;
import org.springframework.stereotype.Service;
import org.springframework.scheduling.annotation.Async;

import java.util.*;
import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.concurrent.CompletableFuture;

@Service
public class SecurityScanService {

    private static final Map<String, SecurityRisk> SECURITY_PATTERNS = new HashMap<>();
    private static final Map<String, String> CWE_MAPPING = new HashMap<>();
    
    static {
        // Initialize security patterns and their risk levels
        SECURITY_PATTERNS.put("exec\\s*\\(", new SecurityRisk("CRITICAL", "CODE_INJECTION", "CWE-94"));
        SECURITY_PATTERNS.put("eval\\s*\\(", new SecurityRisk("CRITICAL", "CODE_INJECTION", "CWE-94"));
        SECURITY_PATTERNS.put("subprocess\\.", new SecurityRisk("HIGH", "COMMAND_INJECTION", "CWE-78"));
        SECURITY_PATTERNS.put("os\\.system\\s*\\(", new SecurityRisk("HIGH", "COMMAND_INJECTION", "CWE-78"));
        SECURITY_PATTERNS.put("__import__\\s*\\(", new SecurityRisk("HIGH", "DYNAMIC_IMPORT", "CWE-94"));
        SECURITY_PATTERNS.put("open\\s*\\(", new SecurityRisk("MEDIUM", "FILE_ACCESS", "CWE-22"));
        SECURITY_PATTERNS.put("file\\s*\\(", new SecurityRisk("MEDIUM", "FILE_ACCESS", "CWE-22"));
        SECURITY_PATTERNS.put("input\\s*\\(", new SecurityRisk("MEDIUM", "USER_INPUT", "CWE-20"));
        SECURITY_PATTERNS.put("raw_input\\s*\\(", new SecurityRisk("MEDIUM", "USER_INPUT", "CWE-20"));
        SECURITY_PATTERNS.put("pickle\\.load", new SecurityRisk("HIGH", "INSECURE_DESERIALIZATION", "CWE-502"));
        SECURITY_PATTERNS.put("pickle\\.loads", new SecurityRisk("HIGH", "INSECURE_DESERIALIZATION", "CWE-502"));
        SECURITY_PATTERNS.put("yaml\\.load(?!_safe)", new SecurityRisk("HIGH", "INSECURE_DESERIALIZATION", "CWE-502"));
        SECURITY_PATTERNS.put("requests\\.(get|post|put|delete)\\s*\\(", new SecurityRisk("MEDIUM", "EXTERNAL_REQUEST", "CWE-918"));
        SECURITY_PATTERNS.put("urllib\\.(request|parse)", new SecurityRisk("MEDIUM", "EXTERNAL_REQUEST", "CWE-918"));
        SECURITY_PATTERNS.put("sqlite3\\.execute\\s*\\(", new SecurityRisk("MEDIUM", "SQL_INJECTION", "CWE-89"));
        SECURITY_PATTERNS.put("cursor\\.execute\\s*\\(", new SecurityRisk("MEDIUM", "SQL_INJECTION", "CWE-89"));
        SECURITY_PATTERNS.put("password\\s*=\\s*['\"]", new SecurityRisk("HIGH", "HARDCODED_CREDENTIALS", "CWE-798"));
        SECURITY_PATTERNS.put("api_key\\s*=\\s*['\"]", new SecurityRisk("HIGH", "HARDCODED_CREDENTIALS", "CWE-798"));
        SECURITY_PATTERNS.put("secret\\s*=\\s*['\"]", new SecurityRisk("HIGH", "HARDCODED_CREDENTIALS", "CWE-798"));
        SECURITY_PATTERNS.put("token\\s*=\\s*['\"]", new SecurityRisk("HIGH", "HARDCODED_CREDENTIALS", "CWE-798"));
        SECURITY_PATTERNS.put("random\\.seed\\s*\\(", new SecurityRisk("LOW", "WEAK_RANDOMNESS", "CWE-338"));
        SECURITY_PATTERNS.put("hashlib\\.md5", new SecurityRisk("LOW", "WEAK_CRYPTO", "CWE-327"));
        SECURITY_PATTERNS.put("hashlib\\.sha1", new SecurityRisk("LOW", "WEAK_CRYPTO", "CWE-327"));
        
        // Initialize CWE descriptions
        CWE_MAPPING.put("CWE-94", "Improper Control of Generation of Code ('Code Injection')");
        CWE_MAPPING.put("CWE-78", "Improper Neutralization of Special Elements used in an OS Command ('OS Command Injection')");
        CWE_MAPPING.put("CWE-22", "Improper Limitation of a Pathname to a Restricted Directory ('Path Traversal')");
        CWE_MAPPING.put("CWE-20", "Improper Input Validation");
        CWE_MAPPING.put("CWE-502", "Deserialization of Untrusted Data");
        CWE_MAPPING.put("CWE-918", "Server-Side Request Forgery (SSRF)");
        CWE_MAPPING.put("CWE-89", "Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection')");
        CWE_MAPPING.put("CWE-798", "Use of Hard-coded Credentials");
        CWE_MAPPING.put("CWE-338", "Use of Cryptographically Weak Pseudo-Random Number Generator (PRNG)");
        CWE_MAPPING.put("CWE-327", "Use of a Broken or Risky Cryptographic Algorithm");
    }

    public SecurityScanResponse performSecurityScan(String code, String workflowId) {
        List<SecurityIssue> issues = new ArrayList<>();
        
        // Perform pattern-based security scanning
        issues.addAll(scanSecurityPatterns(code));
        
        // Perform context-aware security analysis
        issues.addAll(analyzeSecurityContext(code));
        
        // Perform dependency security analysis
        issues.addAll(analyzeDependencySecurity(code));
        
        // Calculate overall risk
        String overallRisk = calculateOverallRisk(issues);
        
        boolean success = !issues.stream().anyMatch(issue -> "CRITICAL".equals(issue.getSeverity()));
        
        return SecurityScanResponse.builder()
            .success(success)
            .workflowId(workflowId)
            .overallRisk(overallRisk)
            .securityIssues(issues)
            .message(success ? "Security scan completed successfully" : "Security issues detected")
            .timestamp(new Date())
            .scanId("scan-" + UUID.randomUUID().toString())
            .build();
    }

    @Async
    public CompletableFuture<SecurityScanResponse> performAsyncSecurityScan(String code, String workflowId) {
        try {
            // Simulate processing time for comprehensive scan
            Thread.sleep(2000);
            SecurityScanResponse response = performSecurityScan(code, workflowId);
            return CompletableFuture.completedFuture(response);
        } catch (InterruptedException e) {
            SecurityScanResponse errorResponse = SecurityScanResponse.builder()
                .success(false)
                .workflowId(workflowId)
                .overallRisk("UNKNOWN")
                .message("Security scan interrupted")
                .timestamp(new Date())
                .scanId("scan-" + UUID.randomUUID().toString())
                .build();
            return CompletableFuture.completedFuture(errorResponse);
        }
    }

    private List<SecurityIssue> scanSecurityPatterns(String code) {
        List<SecurityIssue> issues = new ArrayList<>();
        String[] lines = code.split("\n");
        
        for (Map.Entry<String, SecurityRisk> entry : SECURITY_PATTERNS.entrySet()) {
            String pattern = entry.getKey();
            SecurityRisk risk = entry.getValue();
            
            Pattern compiledPattern = Pattern.compile(pattern, Pattern.CASE_INSENSITIVE);
            
            for (int i = 0; i < lines.length; i++) {
                String line = lines[i].trim();
                if (line.startsWith("#") || line.isEmpty()) continue; // Skip comments and empty lines
                
                Matcher matcher = compiledPattern.matcher(line);
                if (matcher.find()) {
                    issues.add(SecurityIssue.builder()
                        .severity(risk.severity)
                        .category(risk.category)
                        .message(generateSecurityMessage(risk.category, matcher.group()))
                        .rule("pattern_" + risk.category.toLowerCase())
                        .line(i + 1)
                        .codeSnippet(line)
                        .remediation(generateRemediation(risk.category))
                        .cweId(risk.cweId)
                        .build());
                }
            }
        }
        
        return issues;
    }

    private List<SecurityIssue> analyzeSecurityContext(String code) {
        List<SecurityIssue> issues = new ArrayList<>();
        String[] lines = code.split("\n");
        
        // Check for network operations without proper validation
        for (int i = 0; i < lines.length; i++) {
            String line = lines[i].trim();
            if (line.startsWith("#") || line.isEmpty()) continue;
            
            // Check for URL construction without validation
            if (line.contains("http://") || line.contains("https://")) {
                if (!line.contains("requests.get") && !line.contains("urllib")) {
                    issues.add(SecurityIssue.builder()
                        .severity("LOW")
                        .category("INFORMATION_EXPOSURE")
                        .message("Hardcoded URL found - consider using configuration")
                        .rule("hardcoded_url")
                        .line(i + 1)
                        .codeSnippet(line)
                        .remediation("Use environment variables or configuration files for URLs")
                        .cweId("CWE-200")
                        .build());
                }
            }
            
            // Check for exception handling that might leak information
            if (line.contains("except") && line.contains("print")) {
                issues.add(SecurityIssue.builder()
                    .severity("LOW")
                    .category("INFORMATION_EXPOSURE")
                    .message("Exception details printed to console - potential information leakage")
                    .rule("exception_exposure")
                    .line(i + 1)
                    .codeSnippet(line)
                    .remediation("Log exceptions securely without exposing sensitive details")
                    .cweId("CWE-209")
                    .build());
            }
        }
        
        return issues;
    }

    private List<SecurityIssue> analyzeDependencySecurity(String code) {
        List<SecurityIssue> issues = new ArrayList<>();
        
        // Known vulnerable packages and versions
        Map<String, String> vulnerablePackages = new HashMap<>();
        vulnerablePackages.put("requests", "Consider using requests with proper SSL verification");
        vulnerablePackages.put("urllib3", "Ensure urllib3 is updated to latest version");
        vulnerablePackages.put("pycrypto", "pycrypto is deprecated, use pycryptodome instead");
        
        String[] lines = code.split("\n");
        for (int i = 0; i < lines.length; i++) {
            String line = lines[i].trim();
            if (line.startsWith("import ") || line.startsWith("from ")) {
                for (Map.Entry<String, String> entry : vulnerablePackages.entrySet()) {
                    if (line.contains(entry.getKey())) {
                        issues.add(SecurityIssue.builder()
                            .severity("MEDIUM")
                            .category("VULNERABLE_DEPENDENCY")
                            .message("Using potentially vulnerable dependency: " + entry.getKey())
                            .rule("vulnerable_dependency")
                            .line(i + 1)
                            .codeSnippet(line)
                            .remediation(entry.getValue())
                            .cweId("CWE-1104")
                            .build());
                    }
                }
            }
        }
        
        return issues;
    }

    private String calculateOverallRisk(List<SecurityIssue> issues) {
        if (issues.isEmpty()) return "LOW";
        
        boolean hasCritical = issues.stream().anyMatch(issue -> "CRITICAL".equals(issue.getSeverity()));
        boolean hasHigh = issues.stream().anyMatch(issue -> "HIGH".equals(issue.getSeverity()));
        boolean hasMedium = issues.stream().anyMatch(issue -> "MEDIUM".equals(issue.getSeverity()));
        
        if (hasCritical) return "CRITICAL";
        if (hasHigh) return "HIGH";
        if (hasMedium) return "MEDIUM";
        return "LOW";
    }

    private String generateSecurityMessage(String category, String matchedText) {
        switch (category) {
            case "CODE_INJECTION":
                return "Potential code injection vulnerability detected with: " + matchedText;
            case "COMMAND_INJECTION":
                return "Potential command injection vulnerability detected with: " + matchedText;
            case "FILE_ACCESS":
                return "Unsafe file access operation detected: " + matchedText;
            case "USER_INPUT":
                return "Unvalidated user input detected: " + matchedText;
            case "INSECURE_DESERIALIZATION":
                return "Insecure deserialization detected: " + matchedText;
            case "EXTERNAL_REQUEST":
                return "External request without validation: " + matchedText;
            case "SQL_INJECTION":
                return "Potential SQL injection vulnerability: " + matchedText;
            case "HARDCODED_CREDENTIALS":
                return "Hardcoded credentials detected: " + matchedText;
            case "WEAK_RANDOMNESS":
                return "Weak random number generation: " + matchedText;
            case "WEAK_CRYPTO":
                return "Weak cryptographic algorithm: " + matchedText;
            default:
                return "Security issue detected: " + matchedText;
        }
    }

    private String generateRemediation(String category) {
        switch (category) {
            case "CODE_INJECTION":
                return "Avoid dynamic code execution. Use safe alternatives like pre-defined functions.";
            case "COMMAND_INJECTION":
                return "Use subprocess with shell=False and validate all inputs.";
            case "FILE_ACCESS":
                return "Validate file paths and use secure file operations.";
            case "USER_INPUT":
                return "Validate and sanitize all user inputs.";
            case "INSECURE_DESERIALIZATION":
                return "Use safe deserialization methods or JSON instead of pickle.";
            case "EXTERNAL_REQUEST":
                return "Validate URLs and use proper SSL verification.";
            case "SQL_INJECTION":
                return "Use parameterized queries or prepared statements.";
            case "HARDCODED_CREDENTIALS":
                return "Use environment variables or secure configuration files.";
            case "WEAK_RANDOMNESS":
                return "Use cryptographically secure random number generators.";
            case "WEAK_CRYPTO":
                return "Use strong cryptographic algorithms like SHA-256 or better.";
            default:
                return "Review and fix the security issue.";
        }
    }

    private static class SecurityRisk {
        final String severity;
        final String category;
        final String cweId;
        
        SecurityRisk(String severity, String category, String cweId) {
            this.severity = severity;
            this.category = category;
            this.cweId = cweId;
        }
    }
}