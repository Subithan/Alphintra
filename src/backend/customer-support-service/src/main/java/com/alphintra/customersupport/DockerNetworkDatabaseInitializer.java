package com.alphintra.customersupport;

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
    private static final String DB_NAME = "alphintra_customer_support";
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

            System.out.println("Database 'alphintra_customer_support' initialized successfully.");

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
                String defaultUser = firstNonEmpty(
                    System.getenv("DB_USER"),
                    System.getenv("SPRING_DATASOURCE_USERNAME"),
                    "customer_support"
                );
                String defaultPassword = firstNonEmpty(
                    System.getenv("DB_PASSWORD"),
                    System.getenv("SPRING_DATASOURCE_PASSWORD"),
                    "alphintra@123"
                );
                String user = userInfo != null ? userInfo.split(":")[0] : defaultUser;
                String password = (userInfo != null && userInfo.contains(":")) ? userInfo.split(":")[1] : defaultPassword;
                if (user == null || user.isEmpty()) {
                    user = defaultUser;
                }
                if (password == null) {
                    password = defaultPassword;
                }
                String host = dbUri.getHost() != null ? dbUri.getHost() : "127.0.0.1";
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
            {"127.0.0.1", "5432", "customer_support", "alphintra@123"},
            {"localhost", "5432", "customer_support", "alphintra@123"},
            {"postgres", "5432", "customer_support", "alphintra@123"},
            {"postgres", "5432", "postgres", "postgres"},
            {"postgres", "5432", "postgres", ""},
            {"postgresql", "5432", "customer_support", "alphintra@123"},
            {"db", "5432", "customer_support", "alphintra@123"}
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
                    // Check if we can verify schema exists by connecting to the database
                    try {
                        String dbUrl = String.format("jdbc:postgresql://%s:%s/%s", connDetails.host, connDetails.port, DB_NAME);
                        try (Connection dbConn = DriverManager.getConnection(dbUrl, connDetails.user, connDetails.password);
                             Statement dbStmt = dbConn.createStatement()) {
                            // Check if support_tickets table exists and has the estimated_resolution_time column
                            try (ResultSet tableCheck = dbStmt.executeQuery(
                                "SELECT column_name FROM information_schema.columns WHERE table_name = 'support_tickets' AND column_name = 'estimated_resolution_time'")) {
                                if (tableCheck.next()) {
                                    System.out.println("Database schema appears to be up to date. Skipping recreation.");
                                    return;
                                } else {
                                    System.out.println("Database schema is outdated. Need to recreate...");
                                }
                            }
                        }
                    } catch (SQLException schemaCheckError) {
                        System.out.println("Could not verify schema: " + schemaCheckError.getMessage() + ". Will recreate database.");
                    }
                    
                    // Try to terminate active connections before dropping
                    try {
                        System.out.println("Terminating active connections to database '" + DB_NAME + "'...");
                        stmt.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '" + DB_NAME + "' AND pid != pg_backend_pid()");
                        Thread.sleep(1000); // Give connections time to close
                        stmt.execute("DROP DATABASE " + DB_NAME);
                        System.out.println("Database '" + DB_NAME + "' dropped successfully.");
                    } catch (SQLException dropError) {
                        System.out.println("Could not drop database (active connections): " + dropError.getMessage());
                        System.out.println("Will try to update schema in existing database...");
                        return; // Don't create new database, just update schema
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new SQLException("Interrupted while waiting", ie);
                    }
                } else {
                    System.out.println("Database '" + DB_NAME + "' does not exist. Creating...");
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

        String dbUrl = String.format("jdbc:postgresql://%s:%s/%s", connDetails.host, connDetails.port, DB_NAME);
        try (Connection conn = DriverManager.getConnection(dbUrl, connDetails.user, connDetails.password);
             Statement stmt = conn.createStatement()) {
            
            // First check if support_tickets table exists before trying to add columns
            boolean tableExists = false;
            try (ResultSet tableCheck = stmt.executeQuery(
                "SELECT table_name FROM information_schema.tables WHERE table_name = 'support_tickets'")) {
                tableExists = tableCheck.next();
            }
            
            if (tableExists) {
                System.out.println("support_tickets table exists, checking for missing columns...");
                // Ensure user_id column type is VARCHAR (was UUID in earlier schema)
                try (ResultSet colType = stmt.executeQuery(
                    "SELECT data_type FROM information_schema.columns WHERE table_name = 'support_tickets' AND column_name = 'user_id'")) {
                    if (colType.next()) {
                        String dataType = colType.getString(1);
                        if ("uuid".equalsIgnoreCase(dataType)) {
                            System.out.println("Altering support_tickets.user_id from UUID to VARCHAR(255)...");
                            stmt.execute("ALTER TABLE support_tickets ALTER COLUMN user_id TYPE VARCHAR(255) USING user_id::text");
                            System.out.println("✓ support_tickets.user_id column type updated to VARCHAR(255)");
                        }
                    }
                }
                
                // Check if estimated_resolution_time column exists in support_tickets
                try (ResultSet columnCheck = stmt.executeQuery(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = 'support_tickets' AND column_name = 'estimated_resolution_time'")) {
                    if (!columnCheck.next()) {
                        System.out.println("Adding missing estimated_resolution_time column to support_tickets table...");
                        stmt.execute("ALTER TABLE support_tickets ADD COLUMN IF NOT EXISTS estimated_resolution_time TIMESTAMP");
                        System.out.println("✓ Added estimated_resolution_time column.");
                    }
                }
                
                // Check if last_updated_by column exists
                try (ResultSet columnCheck = stmt.executeQuery(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = 'support_tickets' AND column_name = 'last_updated_by'")) {
                    if (!columnCheck.next()) {
                        System.out.println("Adding missing last_updated_by column to support_tickets table...");
                        stmt.execute("ALTER TABLE support_tickets ADD COLUMN IF NOT EXISTS last_updated_by VARCHAR(255)");
                        System.out.println("✓ Added last_updated_by column.");
                    }
                }
            } else {
                System.out.println("support_tickets table does not exist, will create it with full schema...");
            }
            
            // Check communications table schema and recreate if needed
            boolean communicationsTableExists = false;
            try (ResultSet tableCheck = stmt.executeQuery(
                "SELECT table_name FROM information_schema.tables WHERE table_name = 'communications'")) {
                communicationsTableExists = tableCheck.next();
            }
            
            if (communicationsTableExists) {
                // Check if communications table has old schema (message column instead of content)
                boolean hasOldSchema = false;
                try (ResultSet columnCheck = stmt.executeQuery(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = 'communications' AND column_name = 'message'")) {
                    hasOldSchema = columnCheck.next();
                }
                
                if (hasOldSchema) {
                    System.out.println("Communications table has old schema, dropping and recreating...");
                    stmt.execute("DROP TABLE IF EXISTS communications CASCADE");
                    System.out.println("✓ Dropped old communications table.");
                }
            }
            
            // Now proceed with full schema initialization
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
            System.out.println("Executing SQL statements...");
            
            List<String> statements = parseSqlStatements(sql);
            int executedCount = 0;
            int skippedCount = 0;

            for (String statement : statements) {
                String trimmedStatement = statement.trim();
                if (!trimmedStatement.isEmpty()) {
                    try {
                        stmt.execute(trimmedStatement);
                        executedCount++;
                        System.out.println("✓ Statement " + executedCount + ": " + trimmedStatement.substring(0, Math.min(50, trimmedStatement.length())) + "...");
                    } catch (SQLException statementError) {
                        if (statementError.getSQLState().equals("42P07") || 
                            statementError.getSQLState().equals("42P16") || 
                            statementError.getSQLState().equals("42710") ||
                            statementError.getSQLState().equals("42P01") ||
                            statementError.getSQLState().equals("23505")) { // Unique violation
                            skippedCount++;
                            System.out.println("⚠ Skipping (already exists): " + trimmedStatement.substring(0, Math.min(50, trimmedStatement.length())) + "...");
                        } else {
                            System.err.println("✗ Error executing statement: " + trimmedStatement.substring(0, Math.min(100, trimmedStatement.length())));
                            System.err.println("  Error: " + statementError.getMessage());
                            System.err.println("  SQL State: " + statementError.getSQLState());
                            // Don't throw error for schema updates, just continue
                            System.out.println("⚠ Continuing with next statement...");
                        }
                    }
                }
            }

            System.out.println("✓ Database schema initialization completed. Executed: " + executedCount + ", Skipped: " + skippedCount + " statements.");
        }
    }

    private static List<String> parseSqlStatements(String sql) {
        List<String> statements = new ArrayList<>();
        StringBuilder currentStatement = new StringBuilder();
        String[] lines = sql.split("\n");
        boolean inFunction = false;

        for (String line : lines) {
            String trimmedLine = line.trim();
            if (trimmedLine.isEmpty() || trimmedLine.startsWith("--")) {
                continue;
            }

            // Track if we're inside a function/procedure definition
            if (trimmedLine.toUpperCase().contains("CREATE OR REPLACE FUNCTION") || 
                trimmedLine.toUpperCase().contains("CREATE FUNCTION")) {
                inFunction = true;
            }
            
            if (currentStatement.length() > 0) {
                currentStatement.append("\n");
            }
            currentStatement.append(line);

            // End of function/procedure
            if (inFunction && trimmedLine.toUpperCase().contains("$$ LANGUAGE")) {
                inFunction = false;
                String completeStatement = currentStatement.toString().trim();
                if (!completeStatement.isEmpty()) {
                    statements.add(completeStatement);
                }
                currentStatement = new StringBuilder();
            }
            // Regular statement end
            else if (!inFunction && trimmedLine.endsWith(";")) {
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

    private static String firstNonEmpty(String... values) {
        for (String value : values) {
            if (value != null && !value.isEmpty()) {
                return value;
            }
        }
        return null;
    }
}
