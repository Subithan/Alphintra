package com.alphintra.trading_engine.dto;

// Using a record is a concise way to create a simple data carrier.
public record StartBotRequest(Long userId, Long strategyId) {
}