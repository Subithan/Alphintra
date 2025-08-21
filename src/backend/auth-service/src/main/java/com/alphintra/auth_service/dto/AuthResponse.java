// Path: Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/dto/AuthResponse.java
// Purpose: DTO for login response with JWT.

package com.alphintra.auth_service.dto;

public class AuthResponse {
    private String token;

    public AuthResponse(String token) {
        this.token = token;
    }

    public String getToken() { return token; }
    public void setToken(String token) { this.token = token; }
}