// Path: Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/DockerNetworkDatabaseInitializer.java
// Purpose: Initializes the PostgreSQL database and executes init_database.sql. Added environment variables for KYC provider settings.

package com.alphintra.auth_service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.datasource.DriverManagerDataSource;

import javax.sql.DataSource;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.sql.Connection;
import java.sql.SQLException;
import java.sql.Statement;

public class DockerNetworkDatabaseInitializer {
    private static final Logger log = LoggerFactory.getLogger(DockerNetworkDatabaseInitializer.class);
    private static final String DB_URL = "jdbc:postgresql://postgres:5432/postgres";
    private static final String DB_USER = System.getenv("POSTGRES_USER") != null ? System.getenv("POSTGRES_USER") : "postgres";
    private static final String DB_PASSWORD = System.getenv("POSTGRES_PASSWORD") != null ? System.getenv("POSTGRES_PASSWORD") : "password";
    private static final String DB_NAME = "alphintra_auth_service";
    private static final String KYC_API_KEY = System.getenv("KYC_API_KEY") != null ? System.getenv("KYC_API_KEY") : "";
    private static final String KYC_ENDPOINT = System.getenv("KYC_ENDPOINT") != null ? System.getenv("KYC_ENDPOINT") : "";

    public static void main(String[] args) {
        try {
            DataSource dataSource = createDataSource();
            createDatabaseIfNotExists(dataSource);
            executeSqlScript(dataSource);
            log.info("Database initialization completed successfully.");
            log.info("KYC_API_KEY: {}, KYC_ENDPOINT: {}", KYC_API_KEY, KYC_ENDPOINT);
        } catch (SQLException e) {
            log.error("Error during database initialization", e);
            throw new RuntimeException("Database initialization failed", e);
        }
    }

    private static DataSource createDataSource() {
        DriverManagerDataSource dataSource = new DriverManagerDataSource();
        dataSource.setDriverClassName("org.postgresql.Driver");
        dataSource.setUrl(DB_URL);
        dataSource.setUsername(DB_USER);
        dataSource.setPassword(DB_PASSWORD);
        return dataSource;
    }

    private static void createDatabaseIfNotExists(DataSource dataSource) throws SQLException {
        try (Connection conn = dataSource.getConnection();
             Statement stmt = conn.createStatement()) {
            stmt.executeUpdate("CREATE DATABASE " + DB_NAME);
            log.info("Database {} created or already exists.", DB_NAME);
        } catch (SQLException e) {
            if (!e.getSQLState().equals("42P04")) { // 42P04 = database already exists
                throw e;
            }
        }
    }

    private static void executeSqlScript(DataSource dataSource) throws SQLException {
        try (Connection conn = dataSource.getConnection();
             Statement stmt = conn.createStatement()) {
            String sqlScript = readSqlScript();
            stmt.execute(sqlScript);
            log.info("SQL script executed successfully.");
        }
    }

    private static String readSqlScript() {
        StringBuilder sql = new StringBuilder();
        try (InputStream is = DockerNetworkDatabaseInitializer.class.getClassLoader().getResourceAsStream("init_database.sql");
             BufferedReader reader = new BufferedReader(new InputStreamReader(is))) {
            String line;
            while ((line = reader.readLine()) != null) {
                sql.append(line).append("\n");
            }
        } catch (Exception e) {
            log.error("Error reading SQL script", e);
            throw new RuntimeException("Failed to read SQL script", e);
        }
        return sql.toString();
    }
}