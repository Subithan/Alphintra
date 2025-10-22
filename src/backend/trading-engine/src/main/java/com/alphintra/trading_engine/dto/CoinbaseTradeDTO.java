package com.alphintra.trading_engine.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public record CoinbaseTradeDTO(
        @JsonProperty("tradeId") String tradeId,
        @JsonProperty("orderId") String orderId,
        @JsonProperty("productId") String productId,
        @JsonProperty("side") String side,
        @JsonProperty("price") String price,
        @JsonProperty("size") String size,
        @JsonProperty("fee") String fee,
        @JsonProperty("createdAt") String createdAt
) {
}
