package com.alphintra.auth_service.controller;

import com.alphintra.auth_service.dto.CheckoutSessionRequest;
import com.alphintra.auth_service.dto.CheckoutSessionResponse;
import com.alphintra.auth_service.dto.SubscriptionDto;
import com.alphintra.auth_service.entity.User;
import com.alphintra.auth_service.repository.UserRepository;
import com.alphintra.auth_service.service.StripeService;
import com.alphintra.auth_service.service.SubscriptionService;
import jakarta.validation.Valid;
import java.util.Optional;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/subscriptions")
@CrossOrigin(origins = "http://localhost:3000")
public class SubscriptionController {

  private static final Logger logger = LoggerFactory.getLogger(SubscriptionController.class);

  private final StripeService stripeService;
  private final SubscriptionService subscriptionService;
  private final UserRepository userRepository;

  @Value("${stripe.webhook-secret}")
  private String webhookSecret;

  public SubscriptionController(
      StripeService stripeService,
      SubscriptionService subscriptionService,
      UserRepository userRepository) {
    this.stripeService = stripeService;
    this.subscriptionService = subscriptionService;
    this.userRepository = userRepository;
  }

  @PostMapping("/create-checkout-session")
  public ResponseEntity<CheckoutSessionResponse> createCheckoutSession(
      Authentication authentication, @Valid @RequestBody CheckoutSessionRequest request) {
    try {
      String username = authentication.getName();
      logger.info(
          "Creating checkout session for user: {}, priceId: {}", username, request.getPriceId());

      CheckoutSessionResponse response =
          stripeService.createCheckoutSession(username, request.getPriceId());

      logger.info("Checkout session created successfully: {}", response.getSessionId());
      return ResponseEntity.ok(response);
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
}