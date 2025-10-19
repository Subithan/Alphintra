package com.alphintra.auth_service.dto;

import jakarta.validation.constraints.NotBlank;

public class DeleteAccountRequest {

  @NotBlank(message = "Password is required for account deletion")
  private String password;

  private String confirmationText;

  public DeleteAccountRequest() {}

  public DeleteAccountRequest(String password, String confirmationText) {
    this.password = password;
    this.confirmationText = confirmationText;
  }

  public String getPassword() {
    return password;
  }

  public void setPassword(String password) {
    this.password = password;
  }

  public String getConfirmationText() {
    return confirmationText;
  }

  public void setConfirmationText(String confirmationText) {
    this.confirmationText = confirmationText;
  }
}
