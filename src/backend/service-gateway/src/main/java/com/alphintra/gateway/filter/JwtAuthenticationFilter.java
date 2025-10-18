package com.alphintra.gateway.filter;

import com.alphintra.gateway.config.GatewaySecurityProperties;
import com.alphintra.gateway.security.JwtTokenValidator;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jws;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.util.pattern.PathPattern;
import org.springframework.web.util.pattern.PathPatternParser;
import reactor.core.publisher.Mono;

@Component
public class JwtAuthenticationFilter implements GlobalFilter, Ordered {

  public static final String ATTR_CLAIMS = "gateway.jwt.claims";
  public static final String ATTR_SUBJECT = "gateway.jwt.subject";

  private final JwtTokenValidator validator;
  private final List<PathPattern> publicPatterns;
  private final PathPatternParser parser = new PathPatternParser();

  public JwtAuthenticationFilter(
      JwtTokenValidator validator, GatewaySecurityProperties properties) {
    this.validator = validator;
    this.publicPatterns = properties.getPublicPaths().stream().map(parser::parse).toList();
  }

  @Override
  public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
    if (isPublic(exchange)) {
      return chain.filter(exchange);
    }
    String authorization = exchange.getRequest().getHeaders().getFirst(HttpHeaders.AUTHORIZATION);
    if (authorization == null || !authorization.startsWith("Bearer ")) {
      return unauthorized(exchange.getResponse(), "Missing or invalid Authorization header");
    }
    String token = authorization.substring(7);
    try {
      Jws<Claims> claims = validator.parse(token);
      exchange.getAttributes().put(ATTR_CLAIMS, claims);
      exchange.getAttributes().put(ATTR_SUBJECT, claims.getBody().getSubject());
      // Preserve the original Authorization header for downstream services
      // but also add user info headers for gateway-level operations
      exchange
          .getRequest()
          .mutate()
          .header("X-User-Id", claims.getBody().getSubject())
          .header("X-User-Roles", String.join(",", validator.extractRoles(claims)))
          .build();
      return chain.filter(exchange);
    } catch (Exception ex) {
      return unauthorized(exchange.getResponse(), "Invalid token");
    }
  }

  @Override
  public int getOrder() {
    return -200;
  }

  private boolean isPublic(ServerWebExchange exchange) {
    var path = exchange.getRequest().getPath().pathWithinApplication();
    return publicPatterns.stream().anyMatch(pattern -> pattern.matches(path));
  }

  private Mono<Void> unauthorized(ServerHttpResponse response, String message) {
    response.setStatusCode(HttpStatus.UNAUTHORIZED);
    response.getHeaders().setContentType(MediaType.APPLICATION_JSON);
    String body = String.format("{\"message\":\"%s\"}", message);
    return response.writeWith(
        Mono.just(response.bufferFactory().wrap(body.getBytes(StandardCharsets.UTF_8))));
  }
}
