package com.alphintra.trading_engine.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public record CoinbaseBalancesResponse(List<CoinbaseBalanceDTO> balances) {
}
