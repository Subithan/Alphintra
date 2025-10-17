package com.alphintra.trading_engine.dto;

public record BalanceInfoResponse(
    String status,
    String usdtBalance,
    String btcBalance,
    String message,
    String apiKeyStatus
) {
    public static BalanceInfoResponse success(String usdt, String btc) {
        return new BalanceInfoResponse(
            "SUCCESS",
            usdt + " USDT",
            btc + " BTC",
            "Balance retrieved successfully from Binance Testnet",
            "API Key: Valid and Connected"
        );
    }
    
    public static BalanceInfoResponse error(String message) {
        return new BalanceInfoResponse(
            "ERROR",
            "0.00 USDT",
            "0.00 BTC",
            message,
            "API Key: Invalid or Insufficient Permissions"
        );
    }
}
