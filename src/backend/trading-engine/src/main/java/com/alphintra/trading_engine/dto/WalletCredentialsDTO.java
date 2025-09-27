package com.alphintra.trading_engine.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public record WalletCredentialsDTO(String apiKey, String secretKey) {
}