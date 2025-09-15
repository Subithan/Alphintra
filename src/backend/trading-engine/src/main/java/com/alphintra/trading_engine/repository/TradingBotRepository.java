package com.alphintra.trading_engine.repository;

import com.alphintra.trading_engine.model.BotStatus;
import com.alphintra.trading_engine.model.TradingBot;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface TradingBotRepository extends JpaRepository<TradingBot, Long> {
    Optional<TradingBot> findByUserIdAndStrategyIdAndStatus(Long userId, Long strategyId, BotStatus status);
    List<TradingBot> findByUserId(Long userId);
    List<TradingBot> findByStatus(BotStatus status);
}