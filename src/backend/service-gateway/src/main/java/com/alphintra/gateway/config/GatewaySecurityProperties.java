package com.alphintra.gateway.config;

import java.util.List;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "gateway.security")
public class GatewaySecurityProperties {

  private Jwt jwt = new Jwt();
  private List<String> publicPaths =
      List.of("/api/auth/login", "/api/auth/register", "/api/auth/validate", "/actuator/**");

  public Jwt getJwt() {
    return jwt;
  }

  public void setJwt(Jwt jwt) {
    this.jwt = jwt;
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
}
