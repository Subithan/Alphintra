package com.alphintra.auth_service.dto;

public class CheckoutSessionResponse {

  private boolean success;
  private String sessionId;
  private String sessionUrl;
  private String message;

  public CheckoutSessionResponse() {}

  public CheckoutSessionResponse(String sessionId, String sessionUrl) {
    this.success = true;
    this.sessionId = sessionId;
    this.sessionUrl = sessionUrl;
  }

  public static CheckoutSessionResponse error(String message) {
    CheckoutSessionResponse response = new CheckoutSessionResponse();
    response.success = false;
    response.message = message;
    return response;
  }

  public boolean isSuccess() {
    return success;
  }

  public void setSuccess(boolean success) {
    this.success = success;
  }

  public String getSessionId() {
    return sessionId;
  }

  public void setSessionId(String sessionId) {
    this.sessionId = sessionId;
  }

  public String getSessionUrl() {
    return sessionUrl;
  }

  public void setSessionUrl(String sessionUrl) {
    this.sessionUrl = sessionUrl;
  }

  public String getMessage() {
    return message;
  }

  public void setMessage(String message) {
    this.message = message;
  }
}
