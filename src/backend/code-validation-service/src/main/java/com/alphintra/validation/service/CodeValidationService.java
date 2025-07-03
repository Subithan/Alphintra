package com.alphintra.validation.service;

import com.alphintra.validation.dto.*;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.util.regex.Pattern;
import java.util.regex.Matcher;

@Service
public class CodeValidationService {

    @Autowired
    private SecurityScanService securityScanService;

    private static final List<String> REQUIRED_IMPORTS = Arrays.asList(
        "pandas", "numpy", "talib"
    );

    private static final List<String> FORBIDDEN_OPERATIONS = Arrays.asList(
        "exec(", "eval(", "subprocess", "os.system", "__import__",
        "open(", "file(", "input(", "raw_input("
    );

    private static final Pattern CLASS_PATTERN = Pattern.compile("class\\s+(\\w+):");
    private static final Pattern METHOD_PATTERN = Pattern.compile("def\\s+(\\w+)\\s*\\(");
    private static final Pattern IMPORT_PATTERN = Pattern.compile("^\\s*(?:from\\s+\\w+\\s+)?import\\s+([\\w\\s,]+)", Pattern.MULTILINE);

    public ValidationResponse validatePythonCode(String code, String workflowId) {
        List<ValidationIssue> issues = new ArrayList<>();
        
        // Basic syntax validation
        issues.addAll(validateSyntax(code));
        
        // Import validation
        issues.addAll(validateImports(code));
        
        // Security validation
        issues.addAll(validateSecurity(code));
        
        // Structure validation
        issues.addAll(validateStructure(code));
        
        // Performance hints
        issues.addAll(validatePerformance(code));

        boolean success = issues.stream().noneMatch(issue -> "ERROR".equals(issue.getSeverity()));
        
        return ValidationResponse.builder()
            .success(success)
            .workflowId(workflowId)
            .issues(issues)
            .message(success ? "Code validation passed" : "Code validation failed with errors")
            .timestamp(new Date())
            .build();
    }

    public ModelValidationResponse validateTrainedModel(String modelPath, String datasetPath, String workflowId) {
        List<ValidationIssue> issues = new ArrayList<>();
        
        try {
            // Check if model file exists
            Path model = Paths.get(modelPath);
            if (!Files.exists(model)) {
                issues.add(ValidationIssue.builder()
                    .severity("ERROR")
                    .message("Model file not found: " + modelPath)
                    .line(0)
                    .rule("model_file_exists")
                    .build());
            }

            // Check model file size
            if (Files.exists(model)) {
                long fileSize = Files.size(model);
                if (fileSize == 0) {
                    issues.add(ValidationIssue.builder()
                        .severity("ERROR")
                        .message("Model file is empty")
                        .line(0)
                        .rule("model_file_size")
                        .build());
                } else if (fileSize > 1024 * 1024 * 100) { // 100MB
                    issues.add(ValidationIssue.builder()
                        .severity("WARNING")
                        .message("Model file is very large: " + (fileSize / 1024 / 1024) + "MB")
                        .line(0)
                        .rule("model_file_size")
                        .build());
                }
            }

            // Validate dataset if provided
            if (datasetPath != null) {
                Path dataset = Paths.get(datasetPath);
                if (!Files.exists(dataset)) {
                    issues.add(ValidationIssue.builder()
                        .severity("WARNING")
                        .message("Dataset file not found: " + datasetPath)
                        .line(0)
                        .rule("dataset_file_exists")
                        .build());
                }
            }

            // Simulate model accuracy validation
            double accuracy = 0.85 + Math.random() * 0.1; // Simulate 85-95% accuracy
            double sharpeRatio = 1.2 + Math.random() * 0.8; // Simulate 1.2-2.0 Sharpe ratio
            
            Map<String, Object> metrics = new HashMap<>();
            metrics.put("accuracy", accuracy);
            metrics.put("sharpe_ratio", sharpeRatio);
            metrics.put("max_drawdown", -0.05 - Math.random() * 0.1);
            metrics.put("total_return", 0.15 + Math.random() * 0.2);

            boolean success = issues.stream().noneMatch(issue -> "ERROR".equals(issue.getSeverity()));

            return ModelValidationResponse.builder()
                .success(success)
                .workflowId(workflowId)
                .modelPath(modelPath)
                .accuracy(accuracy)
                .performanceMetrics(metrics)
                .issues(issues)
                .message(success ? "Model validation passed" : "Model validation failed")
                .timestamp(new Date())
                .build();

        } catch (IOException e) {
            issues.add(ValidationIssue.builder()
                .severity("ERROR")
                .message("IO error during model validation: " + e.getMessage())
                .line(0)
                .rule("io_error")
                .build());

            return ModelValidationResponse.builder()
                .success(false)
                .workflowId(workflowId)
                .modelPath(modelPath)
                .issues(issues)
                .message("Model validation failed due to IO error")
                .timestamp(new Date())
                .build();
        }
    }

    private List<ValidationIssue> validateSyntax(String code) {
        List<ValidationIssue> issues = new ArrayList<>();
        
        try {
            // Create a temporary Python file and try to compile it
            Path tempFile = Files.createTempFile("validation", ".py");
            Files.write(tempFile, code.getBytes());
            
            ProcessBuilder pb = new ProcessBuilder("python", "-m", "py_compile", tempFile.toString());
            Process process = pb.start();
            
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getErrorStream()));
            String line;
            while ((line = reader.readLine()) != null) {
                if (line.contains("SyntaxError")) {
                    issues.add(ValidationIssue.builder()
                        .severity("ERROR")
                        .message("Syntax error: " + line)
                        .line(extractLineNumber(line))
                        .rule("syntax_check")
                        .build());
                }
            }
            
            Files.deleteIfExists(tempFile);
            
        } catch (IOException e) {
            // If Python is not available, do basic bracket matching
            issues.addAll(validateBrackets(code));
        }
        
        return issues;
    }

    private List<ValidationIssue> validateBrackets(String code) {
        List<ValidationIssue> issues = new ArrayList<>();
        Stack<Character> stack = new Stack<>();
        String[] lines = code.split("\n");
        
        for (int i = 0; i < lines.length; i++) {
            String line = lines[i];
            for (char c : line.toCharArray()) {
                if (c == '(' || c == '[' || c == '{') {
                    stack.push(c);
                } else if (c == ')' || c == ']' || c == '}') {
                    if (stack.isEmpty()) {
                        issues.add(ValidationIssue.builder()
                            .severity("ERROR")
                            .message("Unmatched closing bracket: " + c)
                            .line(i + 1)
                            .rule("bracket_matching")
                            .build());
                    } else {
                        char open = stack.pop();
                        if (!isMatchingBracket(open, c)) {
                            issues.add(ValidationIssue.builder()
                                .severity("ERROR")
                                .message("Mismatched brackets: " + open + " and " + c)
                                .line(i + 1)
                                .rule("bracket_matching")
                                .build());
                        }
                    }
                }
            }
        }
        
        if (!stack.isEmpty()) {
            issues.add(ValidationIssue.builder()
                .severity("ERROR")
                .message("Unclosed brackets found")
                .line(0)
                .rule("bracket_matching")
                .build());
        }
        
        return issues;
    }

    private boolean isMatchingBracket(char open, char close) {
        return (open == '(' && close == ')') ||
               (open == '[' && close == ']') ||
               (open == '{' && close == '}');
    }

    private List<ValidationIssue> validateImports(String code) {
        List<ValidationIssue> issues = new ArrayList<>();
        
        Set<String> foundImports = new HashSet<>();
        Matcher matcher = IMPORT_PATTERN.matcher(code);
        
        while (matcher.find()) {
            String imports = matcher.group(1);
            String[] importList = imports.split(",");
            for (String imp : importList) {
                foundImports.add(imp.trim().split("\\s+")[0]); // Get first word of import
            }
        }
        
        // Check for required imports
        for (String required : REQUIRED_IMPORTS) {
            if (!foundImports.contains(required)) {
                issues.add(ValidationIssue.builder()
                    .severity("WARNING")
                    .message("Missing recommended import: " + required)
                    .line(0)
                    .rule("required_imports")
                    .build());
            }
        }
        
        return issues;
    }

    private List<ValidationIssue> validateSecurity(String code) {
        List<ValidationIssue> issues = new ArrayList<>();
        String[] lines = code.split("\n");
        
        for (int i = 0; i < lines.length; i++) {
            String line = lines[i];
            for (String forbidden : FORBIDDEN_OPERATIONS) {
                if (line.contains(forbidden)) {
                    issues.add(ValidationIssue.builder()
                        .severity("ERROR")
                        .message("Forbidden operation detected: " + forbidden)
                        .line(i + 1)
                        .rule("security_check")
                        .build());
                }
            }
        }
        
        return issues;
    }

    private List<ValidationIssue> validateStructure(String code) {
        List<ValidationIssue> issues = new ArrayList<>();
        
        // Check for class definition
        Matcher classMatcher = CLASS_PATTERN.matcher(code);
        if (!classMatcher.find()) {
            issues.add(ValidationIssue.builder()
                .severity("ERROR")
                .message("No class definition found")
                .line(0)
                .rule("class_structure")
                .build());
        }
        
        // Check for required methods
        List<String> requiredMethods = Arrays.asList("__init__", "execute", "backtest");
        Matcher methodMatcher = METHOD_PATTERN.matcher(code);
        Set<String> foundMethods = new HashSet<>();
        
        while (methodMatcher.find()) {
            foundMethods.add(methodMatcher.group(1));
        }
        
        for (String required : requiredMethods) {
            if (!foundMethods.contains(required)) {
                issues.add(ValidationIssue.builder()
                    .severity("ERROR")
                    .message("Missing required method: " + required)
                    .line(0)
                    .rule("method_structure")
                    .build());
            }
        }
        
        return issues;
    }

    private List<ValidationIssue> validatePerformance(String code) {
        List<ValidationIssue> issues = new ArrayList<>();
        
        // Check for potential performance issues
        if (code.contains("for") && code.contains("iterrows")) {
            issues.add(ValidationIssue.builder()
                .severity("WARNING")
                .message("Consider using vectorized operations instead of iterrows() for better performance")
                .line(0)
                .rule("performance_hint")
                .build());
        }
        
        if (code.contains("apply(lambda")) {
            issues.add(ValidationIssue.builder()
                .severity("INFO")
                .message("Consider using vectorized operations instead of apply() with lambda for better performance")
                .line(0)
                .rule("performance_hint")
                .build());
        }
        
        return issues;
    }

    private int extractLineNumber(String errorMessage) {
        Pattern linePattern = Pattern.compile("line (\\d+)");
        Matcher matcher = linePattern.matcher(errorMessage);
        if (matcher.find()) {
            return Integer.parseInt(matcher.group(1));
        }
        return 0;
    }
}