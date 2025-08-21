// Path: Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/dto/AuthRequest.java
// Purpose: DTO for login requests.

package com.alphintra.auth_service.dto;

public class AuthRequest {
    private String username;
    private String password;

    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }
    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }
}