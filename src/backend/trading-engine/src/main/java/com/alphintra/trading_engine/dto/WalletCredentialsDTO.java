package com.alphintra.trading_engine.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public record WalletCredentialsDTO(
    @JsonProperty("apiKey") String apiKey,
    @JsonProperty("privateKey") @JsonAlias("secretKey") String privateKey
) {
}