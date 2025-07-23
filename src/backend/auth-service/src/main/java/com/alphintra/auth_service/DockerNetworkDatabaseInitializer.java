package com.alphintra.auth_service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class DockerNetworkDatabaseInitializer {
    private static final Logger log = LoggerFactory.getLogger(DockerNetworkDatabaseInitializer.class);

    private static final String DB_NAME = "alphintra_auth_service";
    private static final String SQL_FILE_PATH = "/app/init_database.sql"; // adjust if needed

    private static final int MAX_RETRY_ATTEMPTS = 30;
    private static final int RETRY_DELAY_MS = 2000;

    public static void main(String[] args) {
        try {
            Class.forName("org.postgresql.Driver");
            log.info("PostgreSQL JDBC Driver loaded.");

            ConnectionDetails connDetails = findWorkingConnection();

            createDatabaseIfNotExists(connDetails);

            executeSqlScript(connDetails);

            log.info("Database initialization for '{}' completed successfully.", DB_NAME);

        } catch (Exception e) {
            log.error("Database initialization failed.", e);
            throw new RuntimeException(e);
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
        log.info("Trying to find working database connection...");

        String databaseUrl = System.getenv("DATABASE_URL");
        if (databaseUrl != null && !databaseUrl.isEmpty()) {
            try {
                // Parse DATABASE_URL, fix if not jdbc URL
                // We expect format like: postgresql://user:pass@host:port/db
                String tempUrl = databaseUrl.startsWith("jdbc:") ? databaseUrl : "http://" + databaseUrl.replace("postgresql://", "");
                java.net.URI dbUri = new java.net.URI(tempUrl);

                String userInfo = dbUri.getUserInfo();
                String user = (userInfo != null && userInfo.contains(":")) ? userInfo.split(":")[0] : "postgres";
                String password = (userInfo != null && userInfo.contains(":")) ? userInfo.split(":")[1] : "";
                String host = dbUri.getHost();
                int portInt = dbUri.getPort() != -1 ? dbUri.getPort() : 5432;
                String port = String.valueOf(portInt);

                String jdbcUrl = String.format("jdbc:postgresql://%s:%s/postgres", host, port);

                try (Connection conn = DriverManager.getConnection(jdbcUrl, user, password)) {
                    log.info("Connected successfully using DATABASE_URL: {}@{}:{}", user, host, port);
                    return new ConnectionDetails(host, port, user, password);
                }
            } catch (Exception e) {
                log.warn("Failed to connect using DATABASE_URL '{}': {}", databaseUrl, e.getMessage());
            }
        }

        // Fallback default configs
        String[][] fallbackConfigs = {
                {"postgres", "5432", "alphintra", "alphintra123"},
                {"postgres", "5432", "postgres", "postgres"},
                {"localhost", "5432", "alphintra", "alphintra123"},
                {"localhost", "5432", "postgres", "postgres"},
        };

        for (int attempt = 1; attempt <= MAX_RETRY_ATTEMPTS; attempt++) {
            log.info("Attempt {}/{} to connect using fallback configurations...", attempt, MAX_RETRY_ATTEMPTS);
            for (String[] cfg : fallbackConfigs) {
                String host = cfg[0], port = cfg[1], user = cfg[2], pass = cfg[3];
                String jdbcUrl = String.format("jdbc:postgresql://%s:%s/postgres", host, port);
                try (Connection conn = DriverManager.getConnection(jdbcUrl, user, pass)) {
                    log.info("Connected successfully: {}@{}:{}", user, host, port);
                    return new ConnectionDetails(host, port, user, pass);
                } catch (SQLException ex) {
                    log.debug("Connection failed: {}@{}:{} - {}", user, host, port, ex.getMessage());
                }
            }
            try {
                Thread.sleep(RETRY_DELAY_MS);
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                throw new SQLException("Interrupted during retry delay", ie);
            }
        }
        throw new SQLException("Could not establish database connection after retries");
    }

    private static void createDatabaseIfNotExists(ConnectionDetails connDetails) throws SQLException {
        log.info("Checking if database '{}' exists...", DB_NAME);
        String jdbcUrl = String.format("jdbc:postgresql://%s:%s/postgres", connDetails.host, connDetails.port);
        try (Connection conn = DriverManager.getConnection(jdbcUrl, connDetails.user, connDetails.password);
             Statement stmt = conn.createStatement()) {

            String checkDbQuery = "SELECT 1 FROM pg_database WHERE datname = '" + DB_NAME + "'";
            try (ResultSet rs = stmt.executeQuery(checkDbQuery)) {
                if (rs.next()) {
                    log.info("Database '{}' already exists.", DB_NAME);
                    return;
                }
            }

            stmt.execute("CREATE DATABASE " + DB_NAME);
            log.info("Database '{}' created.", DB_NAME);

        } catch (SQLException e) {
            if ("42P04".equals(e.getSQLState())) {
                log.info("Database '{}' already exists (caught exception).", DB_NAME);
            } else {
                throw e;
            }
        }
    }

    private static void executeSqlScript(ConnectionDetails connDetails) throws SQLException, IOException {
        log.info("Loading SQL script for schema initialization...");

        String sql;

        try {
            sql = new String(Files.readAllBytes(Paths.get(SQL_FILE_PATH)), StandardCharsets.UTF_8);
            log.info("Loaded SQL script from file system: {}", SQL_FILE_PATH);
        } catch (IOException e) {
            log.warn("SQL file not found on file system: {}. Trying classpath...", SQL_FILE_PATH);
            try (InputStream is = DockerNetworkDatabaseInitializer.class.getResourceAsStream("/init_database.sql")) {
                if (is == null) {
                    throw new IOException("Could not find init_database.sql on classpath or filesystem");
                }
                sql = new String(is.readAllBytes(), StandardCharsets.UTF_8);
                log.info("Loaded SQL script from classpath resource: /init_database.sql");
            }
        }

        if (sql == null || sql.trim().isEmpty()) {
            throw new IOException("SQL script is empty");
        }

        log.info("SQL script length: {} characters", sql.length());

        String jdbcUrl = String.format("jdbc:postgresql://%s:%s/%s", connDetails.host, connDetails.port, DB_NAME);
        try (Connection conn = DriverManager.getConnection(jdbcUrl, connDetails.user, connDetails.password);
             Statement stmt = conn.createStatement()) {

            List<String> statements = parseSqlStatements(sql);
            int executedCount = 0;

            for (String statement : statements) {
                String trimmedStmt = statement.trim();
                if (!trimmedStmt.isEmpty()) {
                    try {
                        stmt.execute(trimmedStmt);
                        executedCount++;
                        log.info("Executed statement {}: {}", executedCount,
                                trimmedStmt.length() > 60 ? trimmedStmt.substring(0, 60) + "..." : trimmedStmt);
                    } catch (SQLException ex) {
                        // Handle common "already exists" errors gracefully
                        if ("42P07".equals(ex.getSQLState()) || "42P16".equals(ex.getSQLState())) {
                            log.warn("Skipping existing object: {}", trimmedStmt);
                        } else {
                            log.error("Failed to execute statement: {}", trimmedStmt, ex);
                            throw ex;
                        }
                    }
                }
            }

            log.info("SQL script executed successfully. {} statements executed.", executedCount);
        }
    }

    private static List<String> parseSqlStatements(String sql) {
        List<String> statements = new ArrayList<>();
        StringBuilder sb = new StringBuilder();
        String[] lines = sql.split("\n");

        for (String line : lines) {
            String trimmed = line.trim();
            if (trimmed.isEmpty() || trimmed.startsWith("--")) {
                continue; // skip comments and empty lines
            }

            if (sb.length() > 0) {
                sb.append("\n");
            }
            sb.append(line);

            if (trimmed.endsWith(";")) {
                statements.add(sb.toString().trim());
                sb.setLength(0);
            }
        }
        if (sb.length() > 0) {
            statements.add(sb.toString().trim());
        }

        return statements;
    }
}
