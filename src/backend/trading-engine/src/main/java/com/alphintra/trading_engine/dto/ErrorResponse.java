package com.alphintra.trading_engine.dto;

import java.time.LocalDateTime;

public record ErrorResponse(
    String error,
    String message,
    String currency,
    String currentBalance,
    String minimumRequired,
    LocalDateTime timestamp
) {
    public ErrorResponse(String error, String message, String currency, String currentBalance, String minimumRequired) {
        this(error, message, currency, currentBalance, minimumRequired, LocalDateTime.now());
    }
}
