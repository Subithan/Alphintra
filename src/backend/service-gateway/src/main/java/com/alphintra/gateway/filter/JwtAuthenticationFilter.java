package com.alphintra.gateway.filter;

import com.alphintra.gateway.client.AuthClient;
import com.alphintra.gateway.config.GatewaySecurityProperties;
import com.alphintra.gateway.security.JwtTokenValidator;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jws;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.server.reactive.ServerHttpRequest;
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

  private static final Logger log = LoggerFactory.getLogger(JwtAuthenticationFilter.class);

  private final JwtTokenValidator validator;
  private final AuthClient authClient;
  private final List<PathPattern> publicPatterns;
  private final boolean authEnabled;
  private final boolean delegationEnabled;
  private final boolean fallbackLocal;
  private final PathPatternParser parser = new PathPatternParser();

  public JwtAuthenticationFilter(
      JwtTokenValidator validator, AuthClient authClient, GatewaySecurityProperties properties) {
    this.validator = validator;
    this.authClient = authClient;
    this.publicPatterns = properties.getPublicPaths().stream().map(parser::parse).toList();
    this.authEnabled = properties.isEnabled();
    this.delegationEnabled = properties.getAuthService().isDelegationEnabled();
    this.fallbackLocal = properties.getAuthService().isFallbackLocal();
  }

  @Override
  public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
    if (!authEnabled || isPublic(exchange)) {
      if (log.isDebugEnabled()) {
        log.debug(
            "Auth disabled or path public; skipping auth for path={} enabled={}",
            exchange.getRequest().getPath().pathWithinApplication().value(),
            authEnabled);
      }
      return chain.filter(exchange);
    }

    String authorization = exchange.getRequest().getHeaders().getFirst(HttpHeaders.AUTHORIZATION);
    if (authorization == null || !authorization.startsWith("Bearer ")) {
      log.debug("Missing or invalid Authorization header");
      return unauthorized(exchange.getResponse(), "Missing or invalid Authorization header");
    }
    String token = authorization.substring(7);

    if (delegationEnabled) {
      if (log.isDebugEnabled()) {
        log.debug("Delegating token validation to auth-service");
      }
      return authClient
          .introspect(token)
          .flatMap(
              resp -> {
                if (resp == null || !resp.isActive()) {
                  log.debug("Auth-service returned inactive token");
                  return unauthorized(exchange.getResponse(), "Invalid token");
                }
                String subject = resp.getSub();
                String roles = resp.getRoles() == null ? "" : String.join(",", resp.getRoles());

                exchange.getAttributes().put(ATTR_SUBJECT, subject);
                ServerHttpRequest mutated =
                    exchange
                        .getRequest()
                        .mutate()
                        .header("X-User-Id", subject)
                        .header("X-User-Roles", roles)
                        .build();
                log.debug("Authenticated request for subject={} roles={}", subject, roles);
                return chain.filter(exchange.mutate().request(mutated).build());
              })
          .onErrorResume(
              ex -> {
                log.warn("Auth delegation error: {}", ex.getMessage());
                if (fallbackLocal) {
                  log.debug("Falling back to local JWT validation");
                  try {
                    Jws<Claims> claims = validator.parse(token);
                    String subject = claims.getBody().getSubject();
                    String roles = String.join(",", validator.extractRoles(claims));
                    exchange.getAttributes().put(ATTR_SUBJECT, subject);
                    ServerHttpRequest mutated =
                        exchange
                            .getRequest()
                            .mutate()
                            .header("X-User-Id", subject)
                            .header("X-User-Roles", roles)
                            .build();
                    return chain.filter(exchange.mutate().request(mutated).build());
                  } catch (Exception e) {
                    log.debug("Local JWT validation failed: {}", e.getMessage());
                    return unauthorized(exchange.getResponse(), "Invalid token");
                  }
                }
                return unauthorized(exchange.getResponse(), "Invalid token");
              });
    } else {
      log.debug("Local JWT validation enabled");
      try {
        Jws<Claims> claims = validator.parse(token);
        String subject = claims.getBody().getSubject();
        String roles = String.join(",", validator.extractRoles(claims));
        exchange.getAttributes().put(ATTR_SUBJECT, subject);
        ServerHttpRequest mutated =
            exchange
                .getRequest()
                .mutate()
                .header("X-User-Id", subject)
                .header("X-User-Roles", roles)
                .build();
        return chain.filter(exchange.mutate().request(mutated).build());
      } catch (Exception ex) {
        log.debug(
            "JWT Validation Error (local): {}: {}",
            ex.getClass().getSimpleName(),
            ex.getMessage());
        return unauthorized(exchange.getResponse(), "Invalid token");
      }
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
