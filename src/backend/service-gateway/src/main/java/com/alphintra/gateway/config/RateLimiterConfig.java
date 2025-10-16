package com.alphintra.gateway.config;

import com.alphintra.gateway.filter.JwtAuthenticationFilter;
import java.util.Optional;
import org.springframework.cloud.gateway.filter.ratelimit.KeyResolver;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import reactor.core.publisher.Mono;

@Configuration
public class RateLimiterConfig {

  @Bean
  public KeyResolver principalKeyResolver() {
    return exchange ->
        Mono.justOrEmpty(
                Optional.ofNullable(exchange.getAttribute(JwtAuthenticationFilter.ATTR_SUBJECT))
                    .map(Object::toString))
            .defaultIfEmpty(
                exchange.getRequest().getRemoteAddress() == null
                    ? "anonymous"
                    : exchange.getRequest().getRemoteAddress().getAddress().getHostAddress());
  }
}
