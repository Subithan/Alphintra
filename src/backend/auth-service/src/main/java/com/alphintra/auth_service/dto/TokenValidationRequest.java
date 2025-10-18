package com.alphintra.auth_service.dto;

import jakarta.validation.constraints.NotBlank;

public class TokenValidationRequest {

  @NotBlank(message = "Token is required")
  private String token;

  public String getToken() {
    return token;
  }

  public void setToken(String token) {
    this.token = token;
  }
}
