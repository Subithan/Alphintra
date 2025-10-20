package com.alphintra.trading_engine.dto;

import java.math.BigDecimal;

/**
 * Request to start a trading bot
 * @param userId User ID
 * @param strategyId Strategy ID
 * @param symbol Trading pair (e.g., "BTC/FDUSD", "ETH/FDUSD", "ETC/FDUSD")
 * @param capitalAllocationPercentage Percentage of available balance to use (0-100)
 */
public record StartBotRequest(
    Long userId, 
    Long strategyId,
    String symbol,
    BigDecimal capitalAllocationPercentage
) {
    // Validation can be added here if needed
    public StartBotRequest {
        if (capitalAllocationPercentage != null) {
            if (capitalAllocationPercentage.compareTo(BigDecimal.ZERO) <= 0 || 
                capitalAllocationPercentage.compareTo(new BigDecimal("100")) > 0) {
                throw new IllegalArgumentException("Capital allocation percentage must be between 0 and 100");
            }
        }
    }
}
