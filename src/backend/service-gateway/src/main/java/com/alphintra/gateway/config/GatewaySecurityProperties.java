package com.alphintra.gateway.config;

import java.util.List;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "gateway.security")
public class GatewaySecurityProperties {

  private Jwt jwt = new Jwt();
  // When false, JWT validation is disabled and all routes are treated as public.
  private boolean enabled = false;
  private List<String> publicPaths =
      List.of(
          "/api/auth/login",
          "/api/auth/register",
          "/api/auth/validate",
          "/api/auth/introspect",
          "/actuator/**");
  private AuthService authService = new AuthService();

  public Jwt getJwt() {
    return jwt;
  }

  public void setJwt(Jwt jwt) {
    this.jwt = jwt;
  }

  public boolean isEnabled() {
    return enabled;
  }

  public void setEnabled(boolean enabled) {
    this.enabled = enabled;
  }

  public List<String> getPublicPaths() {
    return publicPaths;
  }

  public void setPublicPaths(List<String> publicPaths) {
    this.publicPaths = publicPaths;
  }

  public static class Jwt {
    private String secret;
    private long clockSkewSeconds = 60;

    public String getSecret() {
      return secret;
    }

    public void setSecret(String secret) {
      this.secret = secret;
    }

    public long getClockSkewSeconds() {
      return clockSkewSeconds;
    }

    public void setClockSkewSeconds(long clockSkewSeconds) {
      this.clockSkewSeconds = clockSkewSeconds;
    }
  }

  public AuthService getAuthService() {
    return authService;
  }

  public void setAuthService(AuthService authService) {
    this.authService = authService;
  }

  public static class AuthService {
    private boolean delegationEnabled = true;
    private boolean fallbackLocal = false;
    private String baseUrl = "http://auth-service:8080";
    private long timeoutMs = 1000;

    public boolean isDelegationEnabled() {
      return delegationEnabled;
    }

    public void setDelegationEnabled(boolean delegationEnabled) {
      this.delegationEnabled = delegationEnabled;
    }

    public boolean isFallbackLocal() {
      return fallbackLocal;
    }

    public void setFallbackLocal(boolean fallbackLocal) {
      this.fallbackLocal = fallbackLocal;
    }

    public String getBaseUrl() {
      return baseUrl;
    }

    public void setBaseUrl(String baseUrl) {
      this.baseUrl = baseUrl;
    }

    public long getTimeoutMs() {
      return timeoutMs;
    }

    public void setTimeoutMs(long timeoutMs) {
      this.timeoutMs = timeoutMs;
    }
  }
}
