package com.alphintra.trading_engine.dto;

/**
 * Response for stopping bots
 */
public record StopBotsResponse(
    String message,
    int botsStoppedCount
) {
}
