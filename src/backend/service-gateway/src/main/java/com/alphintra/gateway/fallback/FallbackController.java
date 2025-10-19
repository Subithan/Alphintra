package com.alphintra.gateway.fallback;

import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/_fallback")
public class FallbackController {

  @RequestMapping(
      value = "/unavailable",
      method = {
        RequestMethod.GET,
        RequestMethod.POST,
        RequestMethod.PUT,
        RequestMethod.DELETE,
        RequestMethod.PATCH,
        RequestMethod.OPTIONS
      },
      produces = MediaType.APPLICATION_JSON_VALUE)
  public Mono<Void> serviceUnavailable(ServerHttpResponse response) {
    if (response.isCommitted()) {
      return Mono.empty();
    }
    response.setStatusCode(HttpStatus.SERVICE_UNAVAILABLE);
    byte[] body = "{\"message\":\"Upstream service unavailable\"}".getBytes();
    return response.writeWith(Mono.just(response.bufferFactory().wrap(body)));
  }
}
