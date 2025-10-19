// Path:
// Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/controller/AuthController.java
// Purpose: REST controller for authentication endpoints (/api/auth/register, /api/auth/login,
// /api/auth/validate).

package com.alphintra.auth_service.controller;

import com.alphintra.auth_service.dto.AuthRequest;
import com.alphintra.auth_service.dto.AuthResponse;
import com.alphintra.auth_service.dto.RegisterRequest;
import com.alphintra.auth_service.dto.TokenIntrospectionResponse;
import com.alphintra.auth_service.dto.TokenValidationRequest;
import com.alphintra.auth_service.service.AuthService;
import jakarta.validation.Valid;
import io.jsonwebtoken.JwtException;
import java.util.Collections;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/auth")
public class AuthController {
  private final AuthService authService;

  public AuthController(AuthService authService) {
    this.authService = authService;
  }

  @PostMapping("/register")
  public ResponseEntity<AuthResponse> register(@Valid @RequestBody RegisterRequest request) {
    AuthResponse response = authService.register(request);
    return ResponseEntity.status(HttpStatus.CREATED).body(response);
  }

  @PostMapping("/login")
  public ResponseEntity<AuthResponse> login(@Valid @RequestBody AuthRequest request) {
    AuthResponse response = authService.authenticate(request);
    return ResponseEntity.ok(response);
  }

  @PostMapping("/validate")
  public ResponseEntity<Boolean> validate(@Valid @RequestBody TokenValidationRequest request) {
    return ResponseEntity.ok(authService.validateToken(request.getToken()));
  }

  @PostMapping("/introspect")
  public ResponseEntity<TokenIntrospectionResponse> introspect(
      @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String authorization,
      @RequestBody(required = false) TokenValidationRequest body) {
    String token = null;
    if (authorization != null && authorization.startsWith("Bearer ")) {
      token = authorization.substring(7);
    } else if (body != null && body.getToken() != null && !body.getToken().isBlank()) {
      token = body.getToken();
    }
    if (token == null || token.isBlank()) {
      return ResponseEntity.status(HttpStatus.BAD_REQUEST)
          .body(TokenIntrospectionResponse.inactive());
    }
    try {
      TokenIntrospectionResponse resp = authService.introspect(token);
      return ResponseEntity.ok(resp);
    } catch (JwtException | IllegalArgumentException ex) {
      return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
          .body(TokenIntrospectionResponse.inactive());
    }
  }
}
