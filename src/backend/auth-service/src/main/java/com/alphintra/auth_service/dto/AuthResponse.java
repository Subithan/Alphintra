// Path: Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/dto/AuthResponse.java
// Purpose: DTO for login response with JWT.

package com.alphintra.auth_service.dto;

import com.alphintra.auth_service.entity.User;

public class AuthResponse {
    private String token;
    private User user;

    public AuthResponse(String token, User user) {
        this.token = token;
        this.user = user;
    }

    public String getToken() { return token; }
    public void setToken(String token) { this.token = token; }
    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }
}