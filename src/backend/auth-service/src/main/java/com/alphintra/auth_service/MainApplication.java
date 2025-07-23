package com.alphintra.auth_service;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.jdbc.core.JdbcTemplate;
import javax.sql.DataSource;
import java.sql.Timestamp;

@SpringBootApplication
public class MainApplication {

    public static void main(String[] args) {
        try {
            System.out.println("Initializing database...");
            DockerNetworkDatabaseInitializer.main(args);
            System.out.println("Database initialization completed.");
        } catch (Exception e) {
            System.err.println("Failed to initialize database: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
        SpringApplication.run(MainApplication.class, args);
        System.out.println("Trading Engine application started on port 8009.");
    }

    @Bean
    public CommandLineRunner databaseInitializer() {
        return args -> {
            // Avoid redundant initialization if already done in main
            System.out.println("Database initializer bean invoked.");
        };
    }

    @Bean
    public BCryptPasswordEncoder customPasswordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public JdbcTemplate jdbcTemplate(DataSource dataSource) {
        return new JdbcTemplate(dataSource);
    }

    // Remove CORS configuration (handled in SecurityConfig.java)
    // public WebMvcConfigurer corsConfigurer() { ... }

    public void signup(String username, String email, String password, String firstName, String lastName,
                       JdbcTemplate jdbcTemplate, BCryptPasswordEncoder passwordEncoder) {
        try {
            String hashedPassword = passwordEncoder.encode(password);
            String sql = "INSERT INTO users (username, email, password, first_name, last_name, kyc_status, created_at, updated_at) " +
                         "VALUES (?, ?, ?, ?, ?, 'NOT_STARTED', ?, ?) " +
                         "ON CONFLICT (username, email) DO NOTHING"; // Prevent duplicate errors
            int rows = jdbcTemplate.update(sql, username, email, hashedPassword, firstName, lastName,
                                          new Timestamp(System.currentTimeMillis()), new Timestamp(System.currentTimeMillis()));
            if (rows == 0) {
                throw new RuntimeException("User already exists with username or email");
            }

            String roleSql = "INSERT INTO user_roles (user_id, role_id) " +
                            "SELECT u.id, r.id FROM users u, roles r WHERE u.username = ? AND r.name = 'USER' " +
                            "ON CONFLICT DO NOTHING";
            jdbcTemplate.update(roleSql, username);
        } catch (Exception e) {
            System.err.println("Signup error: " + e.getMessage());
            throw new RuntimeException("Signup failed: " + e.getMessage());
        }
    }

    public boolean login(String email, String password, JdbcTemplate jdbcTemplate, BCryptPasswordEncoder passwordEncoder) {
        String sql = "SELECT password FROM users WHERE email = ?";
        try {
            String hashedPassword = jdbcTemplate.queryForObject(sql, String.class, email);
            return hashedPassword != null && passwordEncoder.matches(password, hashedPassword);
        } catch (Exception e) {
            System.err.println("Login error: " + e.getMessage());
            return false;
        }
    }

    public boolean verifyUser(String username, JdbcTemplate jdbcTemplate) {
        String sql = "SELECT COUNT(*) FROM users WHERE username = ? AND kyc_status != 'NOT_STARTED'";
        try {
            Integer count = jdbcTemplate.queryForObject(sql, Integer.class, username);
            return count != null && count > 0;
        } catch (Exception e) {
            System.err.println("Verify user error: " + e.getMessage());
            return false;
        }
    }
}