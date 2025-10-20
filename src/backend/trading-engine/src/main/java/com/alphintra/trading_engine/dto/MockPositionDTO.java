package com.alphintra.trading_engine.dto;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * Mock position data for UI testing
 */
public record MockPositionDTO(
    Long id,
    String symbol,
    String side,
    BigDecimal entryPrice,
    BigDecimal currentPrice,
    BigDecimal quantity,
    BigDecimal pnl,
    BigDecimal pnlPercentage,
    Integer leverage,
    LocalDateTime openedAt,
    String status
) {
}
