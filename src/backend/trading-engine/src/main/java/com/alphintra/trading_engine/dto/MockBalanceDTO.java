package com.alphintra.trading_engine.dto;

import java.math.BigDecimal;

/**
 * Mock balance data for UI testing
 */
public record MockBalanceDTO(
    BigDecimal totalBalance,
    BigDecimal availableBalance,
    BigDecimal inOrders,
    String currency
) {
}
