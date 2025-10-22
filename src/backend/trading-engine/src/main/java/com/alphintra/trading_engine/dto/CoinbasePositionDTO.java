package com.alphintra.trading_engine.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public record CoinbasePositionDTO(
        @JsonProperty("positionId") String positionId,
        @JsonProperty("productId") String productId,
        @JsonProperty("symbol") String symbol,
        @JsonProperty("baseCurrency") String baseCurrency,
        @JsonProperty("quoteCurrency") String quoteCurrency,
        @JsonProperty("quantity") String quantity,
        @JsonProperty("entryPrice") String entryPrice,
        @JsonProperty("status") String status,
        @JsonProperty("openedAt") String openedAt,
        @JsonProperty("closedAt") String closedAt
) {
}
