package com.alphintra.trading_engine.dto;

// Using a record is a concise way to create a simple data carrier.
public record StartBotRequest(Long userId, Long strategyId, Integer capitalAllocation, String symbol) {
    
    // Compact constructor with validation only
    public StartBotRequest {
        // Validate if capitalAllocation is provided
        if (capitalAllocation != null && (capitalAllocation < 0 || capitalAllocation > 100)) {
            throw new IllegalArgumentException("Capital allocation must be between 0 and 100");
        }
        // Validate symbol format
        if (symbol != null && !symbol.matches("[A-Z]+/[A-Z]+")) {
            throw new IllegalArgumentException("Symbol must be in format 'BASE/QUOTE' (e.g., 'BTC/USDT')");
        }
    }
}