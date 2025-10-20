package com.alphintra.trading_engine.dto;

import java.math.BigDecimal;

/**
 * Mock performance metrics for UI testing
 */
public record MockPerformanceDTO(
    BigDecimal totalPnl,
    BigDecimal totalPnlPercentage,
    Integer totalTrades,
    Integer winningTrades,
    Integer losingTrades,
    BigDecimal winRate,
    BigDecimal avgProfit,
    BigDecimal avgLoss,
    BigDecimal profitFactor,
    BigDecimal sharpeRatio,
    BigDecimal maxDrawdown
) {
}
