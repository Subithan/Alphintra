package com.alphintra.auth_service.config;

import java.util.List;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.security")
public record SecurityProperties(List<String> allowedOrigins) {
  public List<String> resolvedAllowedOrigins() {
    return (allowedOrigins == null || allowedOrigins.isEmpty()) ? List.of("*") : allowedOrigins;
  }
}
