package com.alphintra.trading_engine.dto;

import java.math.BigDecimal;

/**
 * Mock risk metrics for UI testing
 */
public record MockRiskMetricsDTO(
    BigDecimal currentRisk,
    BigDecimal maxRisk,
    BigDecimal riskPercentage,
    BigDecimal portfolioValue,
    BigDecimal exposure,
    BigDecimal leverage,
    BigDecimal marginUsed,
    BigDecimal marginAvailable,
    String riskLevel
) {
}
