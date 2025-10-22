package com.alphintra.trading_engine.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public record CoinbaseTickerDTO(
        @JsonProperty("productId") String productId,
        @JsonProperty("price") String price
) {
}
