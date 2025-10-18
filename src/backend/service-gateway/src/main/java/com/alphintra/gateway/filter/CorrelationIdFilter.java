package com.alphintra.gateway.filter;

import java.util.UUID;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

@Component
public class CorrelationIdFilter implements GlobalFilter, Ordered {

  public static final String CORRELATION_ID_HEADER = "X-Correlation-Id";

  @Override
  public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
    HttpHeaders headers = exchange.getRequest().getHeaders();
    String existing = headers.getFirst(CORRELATION_ID_HEADER);
    String correlationId =
        (existing == null || existing.isBlank()) ? UUID.randomUUID().toString() : existing;

    ServerWebExchange mutated = exchange;
    if (existing == null || existing.isBlank()) {
      mutated =
          exchange
              .mutate()
              .request(builder -> builder.header(CORRELATION_ID_HEADER, correlationId))
              .build();
    }
    mutated.getResponse().getHeaders().set(CORRELATION_ID_HEADER, correlationId);
    return chain.filter(mutated);
  }

  @Override
  public int getOrder() {
    return -250;
  }
}
