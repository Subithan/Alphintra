package com.alphintra.trading_engine.exception;

public class InsufficientBalanceException extends RuntimeException {
    private final String currency;
    private final String currentBalance;
    private final String minimumRequired;

    public InsufficientBalanceException(String currency, String currentBalance, String minimumRequired) {
        super(String.format("Insufficient %s balance. Current: %s, Minimum required: %s", 
              currency, currentBalance, minimumRequired));
        this.currency = currency;
        this.currentBalance = currentBalance;
        this.minimumRequired = minimumRequired;
    }

    public String getCurrency() {
        return currency;
    }

    public String getCurrentBalance() {
        return currentBalance;
    }

    public String getMinimumRequired() {
        return minimumRequired;
    }
}
