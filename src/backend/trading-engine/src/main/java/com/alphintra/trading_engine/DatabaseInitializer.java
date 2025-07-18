package com.alphintra.trading_engine;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.sql.Statement;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.io.IOException;

public class DatabaseInitializer {
    private static final String DB_URL = System.getenv("DATABASE_URL") != null 
        ? System.getenv("DATABASE_URL").replace("postgresql://", "jdbc:postgresql://").replace("alphintra_trading_engine", "postgres") 
        : "jdbc:postgresql://postgres:5432/postgres";
    private static final String USER = "alphintra";
    private static final String PASSWORD = "alphintra123";
    private static final String SQL_FILE_PATH = "/app/init_database.sql";

    public static void main(String[] args) {
        try {
            // Ensure PostgreSQL driver is loaded
            Class.forName("org.postgresql.Driver");

            // Create database if not exists
            createDatabase();

            // Execute SQL script for schema initialization
            executeSqlScript();
            System.out.println("Database 'alphintra_trading_engine' initialized successfully.");
        } catch (SQLException | IOException | ClassNotFoundException e) {
            System.err.println("Error initializing database: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }

    private static void createDatabase() throws SQLException {
        try (Connection conn = DriverManager.getConnection(DB_URL, USER, PASSWORD);
             Statement stmt = conn.createStatement()) {
            stmt.execute("CREATE DATABASE alphintra_trading_engine");
            System.out.println("Database 'alphintra_trading_engine' created or already exists.");
        } catch (SQLException e) {
            if (!e.getSQLState().equals("42P04")) { // Ignore if database already exists
                throw e;
            }
        }
    }

    private static void executeSqlScript() throws SQLException, IOException {
        String sql = new String(Files.readAllBytes(Paths.get(SQL_FILE_PATH)));
        String dbUrl = DB_URL.replace("postgres", "alphintra_trading_engine");
        try (Connection conn = DriverManager.getConnection(dbUrl, USER, PASSWORD);
             Statement stmt = conn.createStatement()) {
            stmt.execute(sql);
        }
    }
}