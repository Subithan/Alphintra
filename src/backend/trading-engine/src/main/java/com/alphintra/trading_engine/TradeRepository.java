package com.alphintra.trading_engine;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.UUID;

public interface TradeRepository extends JpaRepository<Trade, Long> {
    Trade findByTradeUuid(UUID tradeUuid);
}