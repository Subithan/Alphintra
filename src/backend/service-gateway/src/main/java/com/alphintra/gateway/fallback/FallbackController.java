package com.alphintra.gateway.fallback;

import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/_fallback")
public class FallbackController {

  @GetMapping(value = "/unavailable", produces = MediaType.APPLICATION_JSON_VALUE)
  public ResponseEntity<String> serviceUnavailable() {
    return ResponseEntity.status(503).body("{\"message\":\"Upstream service unavailable\"}");
  }
}
