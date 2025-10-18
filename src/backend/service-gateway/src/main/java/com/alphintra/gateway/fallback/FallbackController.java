package com.alphintra.gateway.fallback;

import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/_fallback")
public class FallbackController {

  @RequestMapping(
      value = "/unavailable",
      method = {RequestMethod.GET, RequestMethod.POST, RequestMethod.PUT, RequestMethod.DELETE, RequestMethod.PATCH, RequestMethod.OPTIONS},
      produces = MediaType.APPLICATION_JSON_VALUE)
  public ResponseEntity<String> serviceUnavailable() {
    return ResponseEntity.status(503).body("{\"message\":\"Upstream service unavailable\"}");
  }
}
