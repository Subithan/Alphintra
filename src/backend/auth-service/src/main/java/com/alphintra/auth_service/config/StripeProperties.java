package com.alphintra.auth_service.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties(prefix = "stripe")
public class StripeProperties {

  private String apiKey;
  private String webhookSecret;
  private String successUrl;
  private String cancelUrl;
  private PriceIds priceIds = new PriceIds();

  public static class PriceIds {
    private String basic;
    private String pro;
    private String enterprise;

    public String getBasic() {
      return basic;
    }

    public void setBasic(String basic) {
      this.basic = basic;
    }

    public String getPro() {
      return pro;
    }

    public void setPro(String pro) {
      this.pro = pro;
    }

    public String getEnterprise() {
      return enterprise;
    }

    public void setEnterprise(String enterprise) {
      this.enterprise = enterprise;
    }
  }

  public String getApiKey() {
    return apiKey;
  }

  public void setApiKey(String apiKey) {
    this.apiKey = apiKey;
  }

  public String getWebhookSecret() {
    return webhookSecret;
  }

  public void setWebhookSecret(String webhookSecret) {
    this.webhookSecret = webhookSecret;
  }

  public String getSuccessUrl() {
    return successUrl;
  }

  public void setSuccessUrl(String successUrl) {
    this.successUrl = successUrl;
  }

  public String getCancelUrl() {
    return cancelUrl;
  }

  public void setCancelUrl(String cancelUrl) {
    this.cancelUrl = cancelUrl;
  }

  public PriceIds getPriceIds() {
    return priceIds;
  }

  public void setPriceIds(PriceIds priceIds) {
    this.priceIds = priceIds;
  }
}
