package com.alphintra.auth_service.service;

import com.alphintra.auth_service.dto.SubscriptionDto;
import com.alphintra.auth_service.entity.Subscription;
import com.alphintra.auth_service.entity.User;
import com.alphintra.auth_service.repository.SubscriptionRepository;
import com.alphintra.auth_service.repository.UserRepository;
import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Optional;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class SubscriptionService {

  private static final Logger logger = LoggerFactory.getLogger(SubscriptionService.class);

  private final UserRepository userRepository;
  private final SubscriptionRepository subscriptionRepository;

  public SubscriptionService(
      UserRepository userRepository, SubscriptionRepository subscriptionRepository) {
    this.userRepository = userRepository;
    this.subscriptionRepository = subscriptionRepository;
  }

  public void updateUserSubscription(String email, String subscriptionId, String status) {
    User user =
        userRepository
            .findByEmail(email)
            .orElseThrow(() -> new RuntimeException("User not found: " + email));
    user.setSubscriptionId(subscriptionId);
    user.setSubscriptionStatus(status);
    userRepository.save(user);
  }

  @Transactional
  public Subscription createOrUpdateSubscription(
      User user, com.stripe.model.Subscription stripeSubscription) {
    logger.info(
        "Creating/updating subscription for user: {}, stripe subscription: {}",
        user.getUsername(),
        stripeSubscription.getId());

    Optional<Subscription> existingSubscription =
        subscriptionRepository.findByStripeSubscriptionId(stripeSubscription.getId());

    Subscription subscription = existingSubscription.orElse(new Subscription());
    subscription.setUser(user);
    subscription.setStripeSubscriptionId(stripeSubscription.getId());
    subscription.setStripeCustomerId(stripeSubscription.getCustomer());

    // Get price information
    if (stripeSubscription.getItems() != null
        && !stripeSubscription.getItems().getData().isEmpty()) {
      com.stripe.model.SubscriptionItem item = stripeSubscription.getItems().getData().get(0);
      subscription.setStripePriceId(item.getPrice().getId());

      // Set amount and currency
      Long amount = item.getPrice().getUnitAmount();
      if (amount != null) {
        subscription.setAmount(BigDecimal.valueOf(amount / 100.0));
      }
      subscription.setCurrency(item.getPrice().getCurrency());
      subscription.setInterval(item.getPrice().getRecurring().getInterval());
    }

    // Determine plan name from metadata or price
    String planName = stripeSubscription.getMetadata().get("plan");
    if (planName == null || planName.isEmpty()) {
      planName = determinePlanFromPrice(subscription.getStripePriceId());
    }
    subscription.setPlanName(planName);

    subscription.setStatus(stripeSubscription.getStatus());
    subscription.setCancelAtPeriodEnd(stripeSubscription.getCancelAtPeriodEnd());

    // Set dates
    if (stripeSubscription.getCurrentPeriodStart() != null) {
      subscription.setCurrentPeriodStart(
          LocalDateTime.ofInstant(
              Instant.ofEpochSecond(stripeSubscription.getCurrentPeriodStart()),
              ZoneId.systemDefault()));
    }

    if (stripeSubscription.getCurrentPeriodEnd() != null) {
      subscription.setCurrentPeriodEnd(
          LocalDateTime.ofInstant(
              Instant.ofEpochSecond(stripeSubscription.getCurrentPeriodEnd()),
              ZoneId.systemDefault()));
    }

    if (stripeSubscription.getCanceledAt() != null) {
      subscription.setCanceledAt(
          LocalDateTime.ofInstant(
              Instant.ofEpochSecond(stripeSubscription.getCanceledAt()), ZoneId.systemDefault()));
    }

    if (stripeSubscription.getTrialStart() != null) {
      subscription.setTrialStart(
          LocalDateTime.ofInstant(
              Instant.ofEpochSecond(stripeSubscription.getTrialStart()), ZoneId.systemDefault()));
    }

    if (stripeSubscription.getTrialEnd() != null) {
      subscription.setTrialEnd(
          LocalDateTime.ofInstant(
              Instant.ofEpochSecond(stripeSubscription.getTrialEnd()), ZoneId.systemDefault()));
    }

    // Save subscription
    Subscription savedSubscription = subscriptionRepository.save(subscription);

    // Update user subscription info
    user.setSubscriptionId(stripeSubscription.getId());
    user.setSubscriptionStatus(stripeSubscription.getStatus());
    user.setSubscriptionPlan(planName);
    user.setSubscriptionStartDate(subscription.getCurrentPeriodStart());
    user.setSubscriptionEndDate(subscription.getCurrentPeriodEnd());
    userRepository.save(user);

    logger.info("Subscription saved: {}", savedSubscription.getId());
    return savedSubscription;
  }

  @Transactional
  public void cancelSubscription(User user, com.stripe.model.Subscription stripeSubscription) {
    logger.info("Canceling subscription for user: {}", user.getUsername());

    Optional<Subscription> subscriptionOpt =
        subscriptionRepository.findByStripeSubscriptionId(stripeSubscription.getId());

    if (subscriptionOpt.isPresent()) {
      Subscription subscription = subscriptionOpt.get();
      subscription.setStatus("canceled");
      subscription.setCanceledAt(LocalDateTime.now());
      subscriptionRepository.save(subscription);
    }

    // Update user
    user.setSubscriptionStatus("canceled");
    userRepository.save(user);
  }

  public Optional<SubscriptionDto> getUserSubscription(User user) {
    return subscriptionRepository
        .findByUser(user)
        .map(
            subscription -> {
              SubscriptionDto dto = new SubscriptionDto();
              dto.setId(subscription.getId());
              dto.setPlanName(subscription.getPlanName());
              dto.setStatus(subscription.getStatus());
              dto.setCurrentPeriodStart(subscription.getCurrentPeriodStart());
              dto.setCurrentPeriodEnd(subscription.getCurrentPeriodEnd());
              dto.setCancelAtPeriodEnd(subscription.getCancelAtPeriodEnd());
              dto.setAmount(
                  subscription.getAmount() != null ? subscription.getAmount().toString() : null);
              dto.setCurrency(subscription.getCurrency());
              dto.setInterval(subscription.getInterval());
              return dto;
            });
  }

  private String determinePlanFromPrice(String priceId) {
    // This is a simple mapping - you should configure this properly
    if (priceId.contains("basic")) {
      return "basic";
    } else if (priceId.contains("pro")) {
      return "pro";
    } else if (priceId.contains("enterprise")) {
      return "enterprise";
    }
    return "unknown";
  }
}