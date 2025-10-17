package com.alphintra.trading_engine.dto;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record TradeOrderDTO(
    Long id,
    Long botId,
    String exchangeOrderId,
    String symbol,
    String type,
    String side,
    BigDecimal price,
    BigDecimal amount,
    String status,
    LocalDateTime createdAt
) {}