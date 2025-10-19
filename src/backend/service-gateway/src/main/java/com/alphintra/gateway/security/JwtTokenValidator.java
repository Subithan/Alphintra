package com.alphintra.gateway.security;

import com.alphintra.gateway.config.GatewaySecurityProperties;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jws;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import java.time.Duration;
import java.util.Set;
import javax.crypto.SecretKey;
import org.springframework.stereotype.Component;

@Component
public class JwtTokenValidator {

  private final SecretKey signingKey;
  private final Duration clockSkew;

  public JwtTokenValidator(GatewaySecurityProperties properties) {
    System.err.println("JWT Token Validator Initializing...");
    System.err.println("JWT Secret from config: " + properties.getJwt().getSecret());
    if (properties.getJwt().getSecret() == null) {
      System.err.println("JWT SECRET IS NULL!");
      throw new IllegalStateException("gateway.security.jwt.secret must be configured");
    }
    System.err.println("JWT Secret length: " + properties.getJwt().getSecret().length());
    System.err.println("JWT Clock Skew: " + properties.getJwt().getClockSkewSeconds() + " seconds");
    try {
      this.signingKey = Keys.hmacShaKeyFor(Decoders.BASE64.decode(properties.getJwt().getSecret()));
      System.err.println("JWT Signing key created successfully");
    } catch (Exception e) {
      System.err.println("Failed to create signing key: " + e.getMessage());
      e.printStackTrace();
      throw e;
    }
    this.clockSkew = Duration.ofSeconds(properties.getJwt().getClockSkewSeconds());
    System.err.println("JWT Token Validator initialized successfully");
  }

  public Jws<Claims> parse(String token) {
    System.err.println("Attempting to parse JWT token...");
    try {
      return Jwts.parserBuilder()
          .setAllowedClockSkewSeconds(clockSkew.getSeconds())
          .setSigningKey(signingKey)
          .build()
          .parseClaimsJws(token);
    } catch (Exception e) {
      System.err.println("JWT Parsing failed: " + e.getClass().getSimpleName() + ": " + e.getMessage());
      e.printStackTrace();
      throw e;
    }
  }

  public Set<String> extractRoles(Jws<Claims> claimsJws) {
    Object roles = claimsJws.getBody().get("roles");
    if (roles instanceof Iterable<?> iterable) {
      return java.util.stream.StreamSupport.stream(iterable.spliterator(), false)
          .map(Object::toString)
          .collect(java.util.stream.Collectors.toUnmodifiableSet());
    }
    return Set.of();
  }
}
