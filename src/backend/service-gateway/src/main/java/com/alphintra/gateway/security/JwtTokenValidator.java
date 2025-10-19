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
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class JwtTokenValidator {

  private final SecretKey signingKey;
  private final Duration clockSkew;
  private static final Logger log = LoggerFactory.getLogger(JwtTokenValidator.class);

  public JwtTokenValidator(GatewaySecurityProperties properties) {
    log.debug("JWT Token Validator Initializing...");
    if (properties.getJwt().getSecret() == null) {
      throw new IllegalStateException("gateway.security.jwt.secret must be configured");
    }
    try {
      this.signingKey = Keys.hmacShaKeyFor(Decoders.BASE64.decode(properties.getJwt().getSecret()));
      log.debug("JWT Signing key created successfully, clockSkew={}s", properties.getJwt().getClockSkewSeconds());
    } catch (Exception e) {
      log.warn("Failed to create signing key: {}", e.getMessage(), e);
      throw e;
    }
    this.clockSkew = Duration.ofSeconds(properties.getJwt().getClockSkewSeconds());
    log.debug("JWT Token Validator initialized successfully");
  }

  public Jws<Claims> parse(String token) {
    try {
      return Jwts.parserBuilder()
          .setAllowedClockSkewSeconds(clockSkew.getSeconds())
          .setSigningKey(signingKey)
          .build()
          .parseClaimsJws(token);
    } catch (Exception e) {
      log.debug("JWT Parsing failed: {}: {}", e.getClass().getSimpleName(), e.getMessage(), e);
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
