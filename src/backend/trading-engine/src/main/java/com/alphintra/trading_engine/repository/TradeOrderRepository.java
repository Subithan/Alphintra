package com.alphintra.trading_engine.repository;

import com.alphintra.trading_engine.model.TradeOrder;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TradeOrderRepository extends JpaRepository<TradeOrder, Long> {
    List<TradeOrder> findByBotIdOrderByCreatedAtDesc(Long botId);
}