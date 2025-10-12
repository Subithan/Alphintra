package com.alphintra.trading_engine.strategy;

import java.math.BigDecimal;
import java.util.Map;
import java.util.Optional;

import com.alphintra.trading_engine.model.Position;

/**
 * Interface defining the contract for all trading strategy implementations.
 * A strategy's purpose is to analyze market data and account state to
 * produce a trading signal (BUY, SELL, or HOLD).
 */
public interface TradingStrategy {

    Signal decide(String symbol, BigDecimal currentPrice, Map<String, BigDecimal> balances, Optional<Position> openPosition);
}