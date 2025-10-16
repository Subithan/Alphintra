// Path: Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/dto/AuthRequest.java
// Purpose: DTO for login requests.

package com.alphintra.auth_service.dto;

public class AuthRequest {
    private String email;
    private String password;

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }
}