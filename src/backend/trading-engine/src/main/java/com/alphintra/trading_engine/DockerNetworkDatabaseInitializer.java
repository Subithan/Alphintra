package com.alphintra.trading_engine;

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
import java.net.URI;
import java.util.ArrayList;
import java.util.List;

public class DockerNetworkDatabaseInitializer {
    private static final String DB_NAME = "alphintra_trading_engine";
    private static final String SQL_FILE_PATH = "/app/init_database.sql";
    private static final int MAX_RETRY_ATTEMPTS = 30;
    private static final int RETRY_DELAY_MS = 2000;

    public static void initializeDatabase() {
        try {
            // Ensure PostgreSQL driver is loaded
            Class.forName("org.postgresql.Driver");
            System.out.println("PostgreSQL driver loaded successfully.");

            // Find working database connection
            ConnectionDetails connDetails = findWorkingConnection();

            // Create database if not exists
            createDatabase(connDetails);

            // Execute SQL script for schema initialization
            executeSqlScript(connDetails);

            System.out.println("Database 'alphintra_trading_engine' initialized successfully.");

        } catch (SQLException | IOException | ClassNotFoundException e) {
            System.err.println("Error initializing database: " + e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Failed to initialize database", e);
        }
    }

    private static class ConnectionDetails {
        String host;
        String port;
        String user;
        String password;

        ConnectionDetails(String host, String port, String user, String password) {
            this.host = host;
            this.port = port;
            this.user = user;
            this.password = password;
        }
    }

    private static ConnectionDetails findWorkingConnection() throws SQLException {
        System.out.println("Finding working database connection...");

        // Try DATABASE_URL environment variable first
        String databaseUrl = System.getenv("DATABASE_URL");
        if (databaseUrl != null && !databaseUrl.isEmpty()) {
            try {
                URI dbUri = new URI(databaseUrl.replace("jdbc:postgresql://", "http://"));
                String userInfo = dbUri.getUserInfo();
                String user = userInfo != null ? userInfo.split(":")[0] : "postgres";
                String password = userInfo != null && userInfo.contains(":") ? userInfo.split(":")[1] : "";
                String host = dbUri.getHost();
                String port = String.valueOf(dbUri.getPort() != -1 ? dbUri.getPort() : 5432);

                String postgresUrl = String.format("jdbc:postgresql://%s:%s/postgres", host, port);
                try (Connection conn = DriverManager.getConnection(postgresUrl, user, password)) {
                    System.out.println("✓ Connected using DATABASE_URL: " + user + "@" + host + ":" + port);
                    return new ConnectionDetails(host, port, user, password);
                }
            } catch (Exception e) {
                System.out.println("✗ DATABASE_URL connection failed: " + databaseUrl + " - " + e.getMessage());
            }
        }

        // Fallback to common configurations
        String[][] fallbackConfigs = {
            {"postgres", "5432", "trading_engine", "alphintra@123"},
            {"postgres", "5432", "postgres", "postgres"},
            {"postgres", "5432", "postgres", ""},
            {"postgresql", "5432", "trading_engine", "alphintra@123"},
            {"db", "5432", "trading_engine", "alphintra@123"},
            {"localhost", "5432", "trading_engine", "alphintra@123"}
        };

        for (int attempt = 1; attempt <= MAX_RETRY_ATTEMPTS; attempt++) {
            System.out.println("Attempt " + attempt + "/" + MAX_RETRY_ATTEMPTS + " - trying fallback configurations...");
            for (String[] config : fallbackConfigs) {
                String host = config[0];
                String port = config[1];
                String user = config[2];
                String password = config[3];
                String postgresUrl = String.format("jdbc:postgresql://%s:%s/postgres", host, port);

                try (Connection conn = DriverManager.getConnection(postgresUrl, user, password)) {
                    System.out.println("✓ Successfully connected with: " + user + "@" + host + ":" + port);
                    return new ConnectionDetails(host, port, user, password);
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

    private static void createDatabase(ConnectionDetails connDetails) throws SQLException {
        System.out.println("Checking if database '" + DB_NAME + "' exists...");
        String postgresUrl = String.format("jdbc:postgresql://%s:%s/postgres", connDetails.host, connDetails.port);

        try (Connection conn = DriverManager.getConnection(postgresUrl, connDetails.user, connDetails.password);
             Statement stmt = conn.createStatement()) {
            String checkDbQuery = "SELECT 1 FROM pg_database WHERE datname = '" + DB_NAME + "'";
            try (ResultSet rs = stmt.executeQuery(checkDbQuery)) {
                if (rs.next()) {
                    System.out.println("Database '" + DB_NAME + "' already exists.");
                    return;
                }
            }

            stmt.execute("CREATE DATABASE " + DB_NAME);
            System.out.println("Database '" + DB_NAME + "' created successfully.");
        } catch (SQLException e) {
            if (e.getSQLState().equals("42P04")) {
                System.out.println("Database '" + DB_NAME + "' already exists.");
            } else {
                System.err.println("Error creating database: " + e.getMessage());
                throw e;
            }
        }
    }

    private static void executeSqlScript(ConnectionDetails connDetails) throws SQLException, IOException {
        System.out.println("Executing database schema initialization...");

        String sql;
        try {
            sql = new String(Files.readAllBytes(Paths.get(SQL_FILE_PATH)), StandardCharsets.UTF_8);
            System.out.println("SQL file loaded from filesystem: " + SQL_FILE_PATH);
        } catch (IOException e) {
            System.out.println("SQL file not found at " + SQL_FILE_PATH + ", trying classpath...");
            try (InputStream is = DockerNetworkDatabaseInitializer.class.getResourceAsStream("/init_database.sql")) {
                if (is == null) {
                    throw new IOException("Could not find init_database.sql in classpath or filesystem");
                }
                sql = new String(is.readAllBytes(), StandardCharsets.UTF_8);
                System.out.println("SQL file loaded from classpath: /init_database.sql");
            }
        }

        if (sql == null || sql.trim().isEmpty()) {
            throw new IOException("SQL script is empty or could not be read");
        }

        System.out.println("SQL script loaded successfully. Length: " + sql.length() + " characters");

        String dbUrl = String.format("jdbc:postgresql://%s:%s/%s", connDetails.host, connDetails.port, DB_NAME);
        System.out.println("Connecting to database: " + dbUrl);
        try (Connection conn = DriverManager.getConnection(dbUrl, connDetails.user, connDetails.password);
             Statement stmt = conn.createStatement()) {
            List<String> statements = parseSqlStatements(sql);
            int executedCount = 0;

            for (String statement : statements) {
                String trimmedStatement = statement.trim();
                if (!trimmedStatement.isEmpty()) {
                    try {
                        stmt.execute(trimmedStatement);
                        executedCount++;
                        System.out.println("✓ Statement " + executedCount + ": " + trimmedStatement.substring(0, Math.min(50, trimmedStatement.length())) + "...");
                    } catch (SQLException statementError) {
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

    private static List<String> parseSqlStatements(String sql) {
        List<String> statements = new ArrayList<>();
        StringBuilder currentStatement = new StringBuilder();
        String[] lines = sql.split("\n");

        for (String line : lines) {
            String trimmedLine = line.trim();
            if (trimmedLine.isEmpty() || trimmedLine.startsWith("--")) {
                continue;
            }

            if (currentStatement.length() > 0) {
                currentStatement.append("\n");
            }
            currentStatement.append(line);

            if (trimmedLine.endsWith(";")) {
                String completeStatement = currentStatement.toString().trim();
                if (!completeStatement.isEmpty()) {
                    statements.add(completeStatement);
                }
                currentStatement = new StringBuilder();
            }
        }

        if (currentStatement.length() > 0) {
            String remainingStatement = currentStatement.toString().trim();
            if (!remainingStatement.isEmpty()) {
                statements.add(remainingStatement);
            }
        }

        return statements;
    }
}
