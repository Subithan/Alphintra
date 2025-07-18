package com.alphintra.auth_service;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.ResultSet;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class DockerNetworkDatabaseInitializer {
    private static final String DB_NAME = "alphintra_auth_service";
    private static final String SQL_FILE_PATH = "/app/init_database.sql";
    
    private static final int MAX_RETRY_ATTEMPTS = 30;
    private static final int RETRY_DELAY_MS = 2000;
    
    // Common Docker network configurations
    private static final String[][] CONNECTION_CONFIGS = {
        // {host, port, user, password}
        {"postgres", "5432", "postgres", "postgres"},
        {"postgres", "5432", "postgres", ""},
        {"postgres", "5432", "alphintra", "alphintra123"},
        {"postgres", "5432", "alphintra", "alphintra"},
        {"postgresql", "5432", "postgres", "postgres"},
        {"postgresql", "5432", "postgres", ""},
        {"postgresql", "5432", "alphintra", "alphintra123"},
        {"db", "5432", "postgres", "postgres"},
        {"db", "5432", "postgres", ""},
        {"localhost", "5432", "postgres", "postgres"},
        {"localhost", "5432", "postgres", ""},
        {"localhost", "5432", "alphintra", "alphintra123"}
    };
    
    private static String workingHost;
    private static String workingPort;
    private static String workingUser;
    private static String workingPassword;

    public static void main(String[] args) {
        initializeDatabase();
    }

    public static void initializeDatabase() {
        try {
            // Ensure PostgreSQL driver is loaded
            Class.forName("org.postgresql.Driver");
            
            // Find working database connection
            findWorkingConnection();
            
            // Create database if not exists
            createDatabase();

            // Execute SQL script for schema initialization
            executeSqlScript();
            
            System.out.println("Database 'alphintra_auth_service' initialized successfully.");
            
        } catch (SQLException | IOException | ClassNotFoundException e) {
            System.err.println("Error initializing database: " + e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Failed to initialize database", e);
        }
    }

    private static void findWorkingConnection() throws SQLException {
        System.out.println("Finding working database connection...");
        
        // Try environment variables first
        String envHost = System.getenv("DB_HOST");
        String envPort = System.getenv("DB_PORT");
        String envUser = System.getenv("DB_USER");
        String envPassword = System.getenv("DB_PASSWORD");
        
        if (envHost != null && envPort != null && envUser != null && envPassword != null) {
            String postgresUrl = String.format("jdbc:postgresql://%s:%s/postgres", envHost, envPort);
            try (Connection conn = DriverManager.getConnection(postgresUrl, envUser, envPassword)) {
                System.out.println("✓ Connected using environment variables: " + envUser + "@" + envHost + ":" + envPort);
                workingHost = envHost;
                workingPort = envPort;
                workingUser = envUser;
                workingPassword = envPassword;
                return;
            } catch (SQLException e) {
                System.out.println("✗ Environment variables connection failed: " + e.getMessage());
            }
        }
        
        // Try common configurations
        for (int attempt = 1; attempt <= MAX_RETRY_ATTEMPTS; attempt++) {
            System.out.println("Attempt " + attempt + "/" + MAX_RETRY_ATTEMPTS + " - trying common configurations...");
            
            for (String[] config : CONNECTION_CONFIGS) {
                String host = config[0];
                String port = config[1];
                String user = config[2];
                String password = config[3];
                
                String postgresUrl = String.format("jdbc:postgresql://%s:%s/postgres", host, port);
                
                try (Connection conn = DriverManager.getConnection(postgresUrl, user, password)) {
                    System.out.println("✓ Successfully connected with: " + user + "@" + host + ":" + port);
                    workingHost = host;
                    workingPort = port;
                    workingUser = user;
                    workingPassword = password;
                    return;
                } catch (SQLException e) {
                    System.out.println("✗ Failed " + user + "@" + host + ":" + port + " - " + e.getMessage());
                }
            }
            
            if (attempt < MAX_RETRY_ATTEMPTS) {
                try {
                    Thread.sleep(RETRY_DELAY_MS);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    throw new SQLException("Interrupted while waiting for database", ie);
                }
            }
        }
        
        throw new SQLException("Could not find working database connection after " + MAX_RETRY_ATTEMPTS + " attempts");
    }

    private static void createDatabase() throws SQLException {
        System.out.println("Checking if database exists...");
        
        String postgresUrl = String.format("jdbc:postgresql://%s:%s/postgres", workingHost, workingPort);
        
        try (Connection conn = DriverManager.getConnection(postgresUrl, workingUser, workingPassword);
             Statement stmt = conn.createStatement()) {
            
            // Check if database exists
            String checkDbQuery = "SELECT 1 FROM pg_database WHERE datname = '" + DB_NAME + "'";
            try (ResultSet rs = stmt.executeQuery(checkDbQuery)) {
                if (rs.next()) {
                    System.out.println("Database 'alphintra_auth_service' already exists.");
                    return;
                }
            }
            
            // Create database
            stmt.execute("CREATE DATABASE " + DB_NAME);
            System.out.println("Database 'alphintra_auth_service' created successfully.");
            
        } catch (SQLException e) {
            if (e.getSQLState().equals("42P04")) { // Database already exists
                System.out.println("Database 'alphintra_auth_service' already exists.");
            } else {
                System.err.println("Error creating database: " + e.getMessage());
                throw e;
            }
        }
    }

    private static void executeSqlScript() throws SQLException, IOException {
        System.out.println("Executing database schema initialization...");
        
        // First try to read from file system
        String sql = null;
        try {
            sql = new String(Files.readAllBytes(Paths.get(SQL_FILE_PATH)), StandardCharsets.UTF_8);
        } catch (IOException e) {
            // If file doesn't exist, try to read from classpath
            System.out.println("SQL file not found at " + SQL_FILE_PATH + ", trying classpath...");
            try (InputStream is = DockerNetworkDatabaseInitializer.class.getResourceAsStream("/init_database.sql")) {
                if (is != null) {
                    sql = new String(is.readAllBytes(), StandardCharsets.UTF_8);
                } else {
                    throw new IOException("Could not find init_database.sql in classpath");
                }
            }
        }
        
        if (sql == null || sql.trim().isEmpty()) {
            throw new IOException("SQL script is empty or could not be read");
        }
        
        System.out.println("SQL script loaded successfully. Length: " + sql.length() + " characters");
        System.out.println("First 100 characters: " + sql.substring(0, Math.min(100, sql.length())));
        
        String dbUrl = String.format("jdbc:postgresql://%s:%s/%s", workingHost, workingPort, DB_NAME);
        System.out.println("Connecting to database: " + dbUrl + " with user: " + workingUser);
        
        try (Connection conn = DriverManager.getConnection(dbUrl, workingUser, workingPassword);
             Statement stmt = conn.createStatement()) {
            
            // Test the connection first
            try (ResultSet rs = stmt.executeQuery("SELECT 1")) {
                if (rs.next()) {
                    System.out.println("✓ Database connection verified successfully.");
                }
            }
            
            // Parse SQL statements properly handling multi-line statements
            java.util.List<String> statements = parseSqlStatements(sql);
            int executedCount = 0;
            
            for (String statement : statements) {
                String trimmedStatement = statement.trim();
                if (!trimmedStatement.isEmpty()) {
                    try {
                        stmt.execute(trimmedStatement);
                        executedCount++;
                        System.out.println("✓ Statement " + executedCount + ": " + trimmedStatement.substring(0, Math.min(50, trimmedStatement.length())) + "...");
                    } catch (SQLException statementError) {
                        // Continue if table/index already exists
                        if (statementError.getSQLState().equals("42P07") || statementError.getSQLState().equals("42P16")) {
                            System.out.println("⚠ Skipping (already exists): " + trimmedStatement.substring(0, Math.min(50, trimmedStatement.length())) + "...");
                        } else {
                            System.err.println("✗ Error executing statement: " + trimmedStatement.substring(0, Math.min(100, trimmedStatement.length())));
                            System.err.println("  Error: " + statementError.getMessage());
                            System.err.println("  SQL State: " + statementError.getSQLState());
                            throw statementError;
                        }
                    }
                }
            }
            
            System.out.println("✓ Database schema initialization completed successfully. Executed " + executedCount + " statements.");
        }
    }
    
    private static java.util.List<String> parseSqlStatements(String sql) {
        java.util.List<String> statements = new java.util.ArrayList<>();
        StringBuilder currentStatement = new StringBuilder();
        String[] lines = sql.split("\n");
        
        for (String line : lines) {
            String trimmedLine = line.trim();
            
            // Skip empty lines and comments
            if (trimmedLine.isEmpty() || trimmedLine.startsWith("--")) {
                continue;
            }
            
            // Add line to current statement
            if (currentStatement.length() > 0) {
                currentStatement.append("\n");
            }
            currentStatement.append(line);
            
            // Check if statement is complete (ends with semicolon)
            if (trimmedLine.endsWith(";")) {
                String completeStatement = currentStatement.toString().trim();
                if (!completeStatement.isEmpty()) {
                    statements.add(completeStatement);
                }
                currentStatement = new StringBuilder();
            }
        }
        
        // Add any remaining statement
        if (currentStatement.length() > 0) {
            String remainingStatement = currentStatement.toString().trim();
            if (!remainingStatement.isEmpty()) {
                statements.add(remainingStatement);
            }
        }
        
        return statements;
    }
}