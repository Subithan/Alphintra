package com.alphintra.trading_engine.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public record CoinbaseOrderDTO(
        @JsonProperty("orderId") String orderId,
        @JsonProperty("productId") String productId,
        @JsonProperty("side") String side,
        @JsonProperty("status") String status,
        @JsonProperty("orderType") String orderType,
        @JsonProperty("createdAt") String createdAt,
        @JsonProperty("filledSize") String filledSize,
        @JsonProperty("averagePrice") String averagePrice
) {
}
