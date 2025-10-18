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
    if (properties.getJwt().getSecret() == null) {
      throw new IllegalStateException("gateway.security.jwt.secret must be configured");
    }
    this.signingKey = Keys.hmacShaKeyFor(Decoders.BASE64.decode(properties.getJwt().getSecret()));
    this.clockSkew = Duration.ofSeconds(properties.getJwt().getClockSkewSeconds());
  }

  public Jws<Claims> parse(String token) {
    return Jwts.parserBuilder()
        .setAllowedClockSkewSeconds(clockSkew.getSeconds())
        .setSigningKey(signingKey)
        .build()
        .parseClaimsJws(token);
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
