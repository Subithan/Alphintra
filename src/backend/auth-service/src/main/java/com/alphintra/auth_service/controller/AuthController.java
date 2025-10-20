// Path:
// Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/controller/AuthController.java
// Purpose: REST controller for authentication endpoints (/api/auth/register, /api/auth/login,
// /api/auth/validate).

package com.alphintra.auth_service.controller;

import com.alphintra.auth_service.dto.AuthRequest;
import com.alphintra.auth_service.dto.AuthResponse;
import com.alphintra.auth_service.dto.RegisterRequest;
import com.alphintra.auth_service.service.AuthService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/auth")
@CrossOrigin(origins = "https://alphintra.com")
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

  @PostMapping("/activate-subscription")
  public ResponseEntity<?> activateSubscription(@RequestBody Map<String, Object> request) {
    try {
      Long userId = ((Number) request.get("userId")).longValue();
      String planName = (String) request.get("planName");
      
      boolean success = authService.activateSubscription(userId, planName);
      
      if (success) {
        return ResponseEntity.ok(Map.of(
          "success", true,
          "message", "Subscription activated successfully"
        ));
      } else {
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
          .body(Map.of(
            "success", false,
            "message", "User not found"
          ));
      }
    } catch (Exception e) {
      return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
        .body(Map.of(
          "success", false,
          "message", "Error activating subscription: " + e.getMessage()
        ));
    }
  }

  // JWT validation endpoints removed
}
