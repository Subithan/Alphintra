package com.alphintra.auth_service.dto;

import jakarta.validation.constraints.NotBlank;

public class AuthResponse {

  @NotBlank private String token;
  private UserProfile user;

  public AuthResponse(String token, UserProfile user) {
    this.token = token;
    this.user = user;
  }

  public String getToken() {
    return token;
  }

  public void setToken(String token) {
    this.token = token;
  }

  public UserProfile getUser() {
    return user;
  }

  public void setUser(UserProfile user) {
    this.user = user;
  }
}
