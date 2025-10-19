package com.alphintra.auth_service.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "subscriptions")
public class Subscription {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "user_id", nullable = false)
  private User user;

  @Column(name = "stripe_subscription_id", unique = true, nullable = false)
  private String stripeSubscriptionId;

  @Column(name = "stripe_customer_id", nullable = false)
  private String stripeCustomerId;

  @Column(name = "stripe_price_id", nullable = false)
  private String stripePriceId;

  @Column(name = "plan_name", nullable = false)
  private String planName; // basic, pro, enterprise

  @Column(name = "status", nullable = false)
  private String status; // active, canceled, past_due, incomplete, trialing

  @Column(name = "current_period_start")
  private LocalDateTime currentPeriodStart;

  @Column(name = "current_period_end")
  private LocalDateTime currentPeriodEnd;

  @Column(name = "cancel_at_period_end")
  private Boolean cancelAtPeriodEnd = false;

  @Column(name = "canceled_at")
  private LocalDateTime canceledAt;

  @Column(name = "trial_start")
  private LocalDateTime trialStart;

  @Column(name = "trial_end")
  private LocalDateTime trialEnd;

  @Column(name = "amount", precision = 10, scale = 2)
  private BigDecimal amount;

  @Column(name = "currency")
  private String currency;

  @Column(name = "interval")
  private String interval; // month, year

  @Column(name = "created_at", nullable = false)
  private LocalDateTime createdAt;

  @Column(name = "updated_at", nullable = false)
  private LocalDateTime updatedAt;

  @PrePersist
  void onCreate() {
    LocalDateTime now = LocalDateTime.now();
    this.createdAt = now;
    this.updatedAt = now;
  }

  @PreUpdate
  void onUpdate() {
    this.updatedAt = LocalDateTime.now();
  }

  // Getters and setters
  public Long getId() {
    return id;
  }

  public void setId(Long id) {
    this.id = id;
  }

  public User getUser() {
    return user;
  }

  public void setUser(User user) {
    this.user = user;
  }

  public String getStripeSubscriptionId() {
    return stripeSubscriptionId;
  }

  public void setStripeSubscriptionId(String stripeSubscriptionId) {
    this.stripeSubscriptionId = stripeSubscriptionId;
  }

  public String getStripeCustomerId() {
    return stripeCustomerId;
  }

  public void setStripeCustomerId(String stripeCustomerId) {
    this.stripeCustomerId = stripeCustomerId;
  }

  public String getStripePriceId() {
    return stripePriceId;
  }

  public void setStripePriceId(String stripePriceId) {
    this.stripePriceId = stripePriceId;
  }

  public String getPlanName() {
    return planName;
  }

  public void setPlanName(String planName) {
    this.planName = planName;
  }

  public String getStatus() {
    return status;
  }

  public void setStatus(String status) {
    this.status = status;
  }

  public LocalDateTime getCurrentPeriodStart() {
    return currentPeriodStart;
  }

  public void setCurrentPeriodStart(LocalDateTime currentPeriodStart) {
    this.currentPeriodStart = currentPeriodStart;
  }

  public LocalDateTime getCurrentPeriodEnd() {
    return currentPeriodEnd;
  }

  public void setCurrentPeriodEnd(LocalDateTime currentPeriodEnd) {
    this.currentPeriodEnd = currentPeriodEnd;
  }

  public Boolean getCancelAtPeriodEnd() {
    return cancelAtPeriodEnd;
  }

  public void setCancelAtPeriodEnd(Boolean cancelAtPeriodEnd) {
    this.cancelAtPeriodEnd = cancelAtPeriodEnd;
  }

  public LocalDateTime getCanceledAt() {
    return canceledAt;
  }

  public void setCanceledAt(LocalDateTime canceledAt) {
    this.canceledAt = canceledAt;
  }

  public LocalDateTime getTrialStart() {
    return trialStart;
  }

  public void setTrialStart(LocalDateTime trialStart) {
    this.trialStart = trialStart;
  }

  public LocalDateTime getTrialEnd() {
    return trialEnd;
  }

  public void setTrialEnd(LocalDateTime trialEnd) {
    this.trialEnd = trialEnd;
  }

  public BigDecimal getAmount() {
    return amount;
  }

  public void setAmount(BigDecimal amount) {
    this.amount = amount;
  }

  public String getCurrency() {
    return currency;
  }

  public void setCurrency(String currency) {
    this.currency = currency;
  }

  public String getInterval() {
    return interval;
  }

  public void setInterval(String interval) {
    this.interval = interval;
  }

  public LocalDateTime getCreatedAt() {
    return createdAt;
  }

  public void setCreatedAt(LocalDateTime createdAt) {
    this.createdAt = createdAt;
  }

  public LocalDateTime getUpdatedAt() {
    return updatedAt;
  }

  public void setUpdatedAt(LocalDateTime updatedAt) {
    this.updatedAt = updatedAt;
  }
}
