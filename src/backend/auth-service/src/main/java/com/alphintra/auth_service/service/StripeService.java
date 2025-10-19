package com.alphintra.auth_service.service;

import com.alphintra.auth_service.dto.CheckoutSessionResponse;
import com.alphintra.auth_service.entity.User;
import com.alphintra.auth_service.repository.UserRepository;
import com.stripe.Stripe;
import com.stripe.exception.SignatureVerificationException;
import com.stripe.exception.StripeException;
import com.stripe.model.Customer;
import com.stripe.model.Event;
import com.stripe.model.EventDataObjectDeserializer;
import com.stripe.model.StripeObject;
import com.stripe.model.checkout.Session;
import com.stripe.net.Webhook;
import com.stripe.param.CustomerCreateParams;
import com.stripe.param.checkout.SessionCreateParams;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class StripeService {

  private static final Logger logger = LoggerFactory.getLogger(StripeService.class);

  private final UserRepository userRepository;
  private final SubscriptionService subscriptionService;

  @Value("${stripe.api-key}")
  private String stripeApiKey;

  @Value("${stripe.webhook-secret}")
  private String webhookSecret;

  @Value("${stripe.success-url}")
  private String successUrl;

  @Value("${stripe.cancel-url}")
  private String cancelUrl;

  public StripeService(
      UserRepository userRepository, SubscriptionService subscriptionService) {
    this.userRepository = userRepository;
    this.subscriptionService = subscriptionService;
  }

  @PostConstruct
  public void init() {
    Stripe.apiKey = stripeApiKey;
    logger.info("Stripe API initialized");
  }

  @Transactional
  public CheckoutSessionResponse createCheckoutSession(String username, String priceId)
      throws StripeException {
    logger.info("Creating checkout session for user: {}, priceId: {}", username, priceId);

    User user =
        userRepository
            .findByUsername(username)
            .orElseThrow(() -> new IllegalArgumentException("User not found: " + username));

    // Get or create Stripe customer
    String customerId = getOrCreateStripeCustomer(user);

    // Create checkout session
    SessionCreateParams.Builder paramsBuilder =
        SessionCreateParams.builder()
            .setMode(SessionCreateParams.Mode.SUBSCRIPTION)
            .setCustomer(customerId)
            .setSuccessUrl(successUrl + "?session_id={CHECKOUT_SESSION_ID}")
            .setCancelUrl(cancelUrl)
            .addLineItem(
                SessionCreateParams.LineItem.builder()
                    .setPrice(priceId)
                    .setQuantity(1L)
                    .build())
            .putMetadata("username", username)
            .putMetadata("user_id", user.getId().toString());

    Session session = Session.create(paramsBuilder.build());

    logger.info("Checkout session created: {}", session.getId());
    return new CheckoutSessionResponse(session.getId(), session.getUrl());
  }

  @Transactional
  public String getOrCreateStripeCustomer(User user) throws StripeException {
    // Check if user already has a Stripe customer ID
    if (user.getStripeCustomerId() != null && !user.getStripeCustomerId().isEmpty()) {
      logger.info("Using existing Stripe customer ID: {}", user.getStripeCustomerId());
      return user.getStripeCustomerId();
    }

    // Create new Stripe customer
    CustomerCreateParams params =
        CustomerCreateParams.builder()
            .setEmail(user.getEmail())
            .setName(user.getFirstName() + " " + user.getLastName())
            .putMetadata("user_id", user.getId().toString())
            .putMetadata("username", user.getUsername())
            .build();

    Customer customer = Customer.create(params);
    logger.info("Created new Stripe customer: {}", customer.getId());

    // Save customer ID to user
    user.setStripeCustomerId(customer.getId());
    userRepository.save(user);

    return customer.getId();
  }

  public void handleWebhook(String payload, String sigHeader, String webhookSecret) {
    Event event = null;

    try {
      event = Webhook.constructEvent(payload, sigHeader, webhookSecret);
    } catch (SignatureVerificationException e) {
      logger.error("Invalid Stripe webhook signature", e);
      throw new IllegalArgumentException("Invalid signature");
    }

    logger.info("Processing Stripe webhook event: {}", event.getType());

    // Handle the event
    EventDataObjectDeserializer dataObjectDeserializer = event.getDataObjectDeserializer();
    StripeObject stripeObject = null;

    if (dataObjectDeserializer.getObject().isPresent()) {
      stripeObject = dataObjectDeserializer.getObject().get();
    } else {
      logger.error("Unable to deserialize Stripe event data");
      throw new IllegalStateException("Unable to deserialize event data");
    }

    switch (event.getType()) {
      case "checkout.session.completed":
        handleCheckoutSessionCompleted((Session) stripeObject);
        break;
      case "customer.subscription.created":
        handleSubscriptionCreated((com.stripe.model.Subscription) stripeObject);
        break;
      case "customer.subscription.updated":
        handleSubscriptionUpdated((com.stripe.model.Subscription) stripeObject);
        break;
      case "customer.subscription.deleted":
        handleSubscriptionDeleted((com.stripe.model.Subscription) stripeObject);
        break;
      case "invoice.payment_succeeded":
        handleInvoicePaymentSucceeded((com.stripe.model.Invoice) stripeObject);
        break;
      case "invoice.payment_failed":
        handleInvoicePaymentFailed((com.stripe.model.Invoice) stripeObject);
        break;
      default:
        logger.info("Unhandled event type: {}", event.getType());
    }
  }

  @Transactional
  protected void handleCheckoutSessionCompleted(Session session) {
    logger.info("Checkout session completed: {}", session.getId());

    String customerId = session.getCustomer();
    String subscriptionId = session.getSubscription();

    User user =
        userRepository
            .findByStripeCustomerId(customerId)
            .orElseThrow(
                () -> new IllegalArgumentException("User not found for customer: " + customerId));

    try {
      // Fetch the full subscription details from Stripe
      com.stripe.model.Subscription stripeSubscription =
          com.stripe.model.Subscription.retrieve(subscriptionId);
      subscriptionService.createOrUpdateSubscription(user, stripeSubscription);
    } catch (StripeException e) {
      logger.error("Failed to retrieve subscription details", e);
      throw new RuntimeException("Failed to process checkout session", e);
    }
  }

  @Transactional
  protected void handleSubscriptionCreated(com.stripe.model.Subscription subscription) {
    logger.info("Subscription created: {}", subscription.getId());

    User user =
        userRepository
            .findByStripeCustomerId(subscription.getCustomer())
            .orElseThrow(
                () ->
                    new IllegalArgumentException(
                        "User not found for customer: " + subscription.getCustomer()));

    subscriptionService.createOrUpdateSubscription(user, subscription);
  }

  @Transactional
  protected void handleSubscriptionUpdated(com.stripe.model.Subscription subscription) {
    logger.info("Subscription updated: {}", subscription.getId());

    User user =
        userRepository
            .findByStripeCustomerId(subscription.getCustomer())
            .orElseThrow(
                () ->
                    new IllegalArgumentException(
                        "User not found for customer: " + subscription.getCustomer()));

    subscriptionService.createOrUpdateSubscription(user, subscription);
  }

  @Transactional
  protected void handleSubscriptionDeleted(com.stripe.model.Subscription subscription) {
    logger.info("Subscription deleted: {}", subscription.getId());

    User user =
        userRepository
            .findByStripeCustomerId(subscription.getCustomer())
            .orElseThrow(
                () ->
                    new IllegalArgumentException(
                        "User not found for customer: " + subscription.getCustomer()));

    subscriptionService.cancelSubscription(user, subscription);
  }

  @Transactional
  protected void handleInvoicePaymentSucceeded(com.stripe.model.Invoice invoice) {
    logger.info("Invoice payment succeeded: {}", invoice.getId());
    // Optional: Send confirmation email or update payment history
  }

  @Transactional
  protected void handleInvoicePaymentFailed(com.stripe.model.Invoice invoice) {
    logger.warn("Invoice payment failed: {}", invoice.getId());

    User user =
        userRepository
            .findByStripeCustomerId(invoice.getCustomer())
            .orElseThrow(
                () ->
                    new IllegalArgumentException(
                        "User not found for customer: " + invoice.getCustomer()));

    // Update subscription status to past_due
    user.setSubscriptionStatus("past_due");
    userRepository.save(user);

    // Optional: Send notification email to user
  }
}
