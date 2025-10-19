package com.alphintra.gateway.client;

import com.alphintra.gateway.config.GatewaySecurityProperties;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatusCode;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;

@Component
public class AuthClient {

  private final WebClient webClient;
  private final long timeoutMs;

  public AuthClient(WebClient.Builder builder, GatewaySecurityProperties props) {
    this.webClient = builder.baseUrl(props.getAuthService().getBaseUrl()).build();
    this.timeoutMs = props.getAuthService().getTimeoutMs();
  }

  public Mono<IntrospectionResponse> introspect(String token) {
    return webClient
        .post()
        .uri("/api/auth/introspect")
        .header(HttpHeaders.AUTHORIZATION, "Bearer " + token)
        .retrieve()
        .onStatus(
            HttpStatusCode::isError,
            resp ->
                resp.bodyToMono(String.class)
                    .defaultIfEmpty("")
                    .flatMap(
                        body ->
                            Mono.error(
                                new WebClientResponseException(
                                    "Auth introspection failed: " + resp.statusCode(),
                                    resp.statusCode().value(),
                                    resp.statusCode().toString(),
                                    null,
                                    null,
                                    null))))
        .bodyToMono(IntrospectionResponse.class)
        .timeout(java.time.Duration.ofMillis(timeoutMs));
  }

  public static class IntrospectionResponse {
    private boolean active;
    private String sub;
    private java.util.List<String> roles;
    private Long iat;
    private Long exp;

    public boolean isActive() {
      return active;
    }

    public void setActive(boolean active) {
      this.active = active;
    }

    public String getSub() {
      return sub;
    }

    public void setSub(String sub) {
      this.sub = sub;
    }

    public java.util.List<String> getRoles() {
      return roles;
    }

    public void setRoles(java.util.List<String> roles) {
      this.roles = roles;
    }

    public Long getIat() {
      return iat;
    }

    public void setIat(Long iat) {
      this.iat = iat;
    }

    public Long getExp() {
      return exp;
    }

    public void setExp(Long exp) {
      this.exp = exp;
    }
  }
}

