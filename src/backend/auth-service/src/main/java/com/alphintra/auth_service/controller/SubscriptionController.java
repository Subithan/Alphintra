package com.alphintra.auth_service.controller;

import com.alphintra.auth_service.dto.CheckoutSessionRequest;
import com.alphintra.auth_service.dto.CheckoutSessionResponse;
import com.alphintra.auth_service.dto.SubscriptionDto;
import com.alphintra.auth_service.entity.User;
import com.alphintra.auth_service.repository.UserRepository;
import com.alphintra.auth_service.service.StripeService;
import com.alphintra.auth_service.service.SubscriptionService;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import jakarta.validation.Valid;
import java.util.Optional;
import javax.crypto.SecretKey;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/subscriptions")
@CrossOrigin(origins = "https://alphintra.com")
public class SubscriptionController {

  private static final Logger logger = LoggerFactory.getLogger(SubscriptionController.class);

  private final StripeService stripeService;
  private final SubscriptionService subscriptionService;
  private final UserRepository userRepository;
  private final SecretKey jwtSigningKey;

  @Value("${stripe.webhook-secret}")
  private String webhookSecret;

  public SubscriptionController(
      StripeService stripeService,
      SubscriptionService subscriptionService,
      UserRepository userRepository,
      @Value("${jwt.secret}") String jwtSecret) {
    this.stripeService = stripeService;
    this.subscriptionService = subscriptionService;
    this.userRepository = userRepository;
    this.jwtSigningKey = Keys.hmacShaKeyFor(Decoders.BASE64.decode(jwtSecret));
  }

  /**
   * Extract user ID from JWT token in Authorization header
   */
  private Long extractUserIdFromToken(@RequestHeader(value = "Authorization", required = false) String authHeader) {
    if (authHeader == null || !authHeader.startsWith("Bearer ")) {
      throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Missing or invalid Authorization header");
    }
    
    String token = authHeader.substring(7);
    try {
      Claims claims = Jwts.parserBuilder()
          .setSigningKey(jwtSigningKey)
          .build()
          .parseClaimsJws(token)
          .getBody();
      
      // Extract user_id from claims
      Object userIdObj = claims.get("user_id");
      if (userIdObj == null) {
        throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "User ID not found in token");
      }
      
      // Handle both Integer and Long types
      if (userIdObj instanceof Integer) {
        return ((Integer) userIdObj).longValue();
      } else if (userIdObj instanceof Long) {
        return (Long) userIdObj;
      } else {
        return Long.parseLong(userIdObj.toString());
      }
    } catch (ResponseStatusException e) {
      throw e;
    } catch (Exception e) {
      logger.error("Failed to parse JWT token", e);
      throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Invalid JWT token");
    }
  }

  @PostMapping("/create-checkout-session")
  public ResponseEntity<CheckoutSessionResponse> createCheckoutSession(
      @RequestHeader(value = "Authorization", required = false) String authHeader,
      @Valid @RequestBody CheckoutSessionRequest request) {
    try {
      Long userId = extractUserIdFromToken(authHeader);
      logger.info(
          "Creating checkout session for userId: {}, priceId: {}", userId, request.getPriceId());

      User user = userRepository
          .findById(userId)
          .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "User not found"));

      CheckoutSessionResponse response =
          stripeService.createCheckoutSession(user.getUsername(), request.getPriceId());

      logger.info("Checkout session created successfully: {}", response.getSessionId());
      return ResponseEntity.ok(response);
    } catch (ResponseStatusException e) {
      logger.error("Authentication error: {}", e.getReason());
      return ResponseEntity.status(e.getStatusCode())
          .body(CheckoutSessionResponse.error(e.getReason()));
    } catch (IllegalArgumentException e) {
      logger.error("Invalid request for checkout session: {}", e.getMessage());
      return ResponseEntity.badRequest()
          .body(CheckoutSessionResponse.error("Invalid request: " + e.getMessage()));
    } catch (Exception e) {
      logger.error("Failed to create checkout session", e);
      return ResponseEntity.internalServerError()
          .body(
              CheckoutSessionResponse.error("Failed to create checkout session: " + e.getMessage()));
    }
  }

  @GetMapping("/current")
  public ResponseEntity<?> getCurrentSubscription(Authentication authentication) {
    try {
      String username = authentication.getName();
      User user =
          userRepository
              .findByUsername(username)
              .orElseThrow(() -> new IllegalArgumentException("User not found"));

      Optional<SubscriptionDto> subscription = subscriptionService.getUserSubscription(user);

      if (subscription.isPresent()) {
        return ResponseEntity.ok(subscription.get());
      } else {
        return ResponseEntity.ok()
            .body(new SubscriptionDto()); // Return empty subscription
      }
    } catch (Exception e) {
      logger.error("Failed to get subscription", e);
      return ResponseEntity.internalServerError()
          .body("Failed to get subscription: " + e.getMessage());
    }
  }

  @PostMapping("/webhook")
  public ResponseEntity<String> handleWebhook(
      @RequestBody String payload, @RequestHeader("Stripe-Signature") String sigHeader) {
    try {
      logger.info("Received Stripe webhook");
      stripeService.handleWebhook(payload, sigHeader, webhookSecret);
      return ResponseEntity.ok("Webhook processed successfully");
    } catch (Exception e) {
      logger.error("Webhook processing failed", e);
      return ResponseEntity.badRequest().body("Webhook error: " + e.getMessage());
    }
  }

  @PostMapping("/confirm-payment")
  public ResponseEntity<?> confirmPayment(
      @RequestHeader(value = "Authorization", required = false) String authHeader,
      @RequestBody(required = false) java.util.Map<String, String> requestBody) {
    try {
      Long userId = extractUserIdFromToken(authHeader);
      logger.info("Confirming payment for userId: {}", userId);

      User user = userRepository
          .findById(userId)
          .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "User not found"));

      // Update subscription status to ACTIVE
      user.setSubscriptionStatus("ACTIVE");
      user.setSubscriptionStartDate(java.time.LocalDateTime.now());
      
      // Set plan name from request body if provided
      if (requestBody != null && requestBody.containsKey("planName")) {
        user.setSubscriptionPlan(requestBody.get("planName"));
      }
      
      userRepository.save(user);

      logger.info("Payment confirmed and subscription activated for userId: {}", userId);
      return ResponseEntity.ok()
          .body(java.util.Map.of(
              "success", true,
              "message", "Subscription activated successfully",
              "userId", userId,
              "username", user.getUsername(),
              "subscriptionStatus", "ACTIVE"
          ));
    } catch (ResponseStatusException e) {
      logger.error("Error confirming payment: {}", e.getReason());
      return ResponseEntity.status(e.getStatusCode())
          .body(java.util.Map.of("success", false, "message", e.getReason()));
    } catch (Exception e) {
      logger.error("Failed to confirm payment", e);
      return ResponseEntity.internalServerError()
          .body(java.util.Map.of("success", false, "message", "Failed to confirm payment: " + e.getMessage()));
    }
  }
}