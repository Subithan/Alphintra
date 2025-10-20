package com.alphintra.trading_engine.dto;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * Mock order data for UI testing
 */
public record MockOrderDTO(
    Long id,
    String symbol,
    String type,
    String side,
    BigDecimal price,
    BigDecimal quantity,
    BigDecimal filled,
    String status,
    LocalDateTime createdAt
) {
}
