package com.alphintra.auth_service.dto;

import jakarta.validation.constraints.NotBlank;

public class CheckoutSessionRequest {

  @NotBlank(message = "Price ID is required")
  private String priceId;

  private String planName; // basic, pro, enterprise

  public CheckoutSessionRequest() {}

  public CheckoutSessionRequest(String priceId, String planName) {
    this.priceId = priceId;
    this.planName = planName;
  }

  public String getPriceId() {
    return priceId;
  }

  public void setPriceId(String priceId) {
    this.priceId = priceId;
  }

  public String getPlanName() {
    return planName;
  }

  public void setPlanName(String planName) {
    this.planName = planName;
  }
}
