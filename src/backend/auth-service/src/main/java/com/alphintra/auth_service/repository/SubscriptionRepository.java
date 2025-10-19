package com.alphintra.auth_service.repository;

import com.alphintra.auth_service.entity.Subscription;
import com.alphintra.auth_service.entity.User;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface SubscriptionRepository extends JpaRepository<Subscription, Long> {

  Optional<Subscription> findByStripeSubscriptionId(String stripeSubscriptionId);

  Optional<Subscription> findByUser(User user);

  Optional<Subscription> findByUserAndStatus(User user, String status);

  Optional<Subscription> findByStripeCustomerId(String stripeCustomerId);
}
