package com.alphintra.trading_engine.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.Map;

@JsonIgnoreProperties(ignoreUnknown = true)
public record StrategyDTO(Long id, String name, String symbol, Map<String, String> parameters) {
    // Example parameters: {"rsiPeriod": "14", "buyThreshold": "30"}
}