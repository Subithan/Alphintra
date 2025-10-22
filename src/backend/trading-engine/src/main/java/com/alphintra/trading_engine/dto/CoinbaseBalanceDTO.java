package com.alphintra.trading_engine.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public record CoinbaseBalanceDTO(String asset, String free, String locked) {
}
