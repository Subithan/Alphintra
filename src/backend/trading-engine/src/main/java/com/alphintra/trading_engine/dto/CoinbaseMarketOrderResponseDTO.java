package com.alphintra.trading_engine.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public record CoinbaseMarketOrderResponseDTO(
        @JsonProperty("orderId") String orderId,
        @JsonProperty("productId") String productId,
        @JsonProperty("side") String side,
        @JsonProperty("status") String status,
        @JsonProperty("orderType") String orderType,
        @JsonProperty("filledSize") String filledSize,
        @JsonProperty("averagePrice") String averagePrice,
        @JsonProperty("fills") List<CoinbaseFillDTO> fills
) {
}
