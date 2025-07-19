package com.alphintra.trading_engine;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.UUID;

public interface OrderRepository extends JpaRepository<Order, Long> {
    Order findByOrderUuid(UUID orderUuid);
}