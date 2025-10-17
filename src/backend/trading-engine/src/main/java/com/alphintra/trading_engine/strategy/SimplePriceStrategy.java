package com.alphintra.trading_engine.strategy;

import com.alphintra.trading_engine.model.Position;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;
import java.util.Optional;

/**
 * A simple trading strategy that includes both a take-profit and a stop-loss exit strategy.
 * Works dynamically with any trading pair (BTC/USDT, ETH/USDT, etc.)
 */
public class SimplePriceStrategy implements TradingStrategy {

    // --- Entry Conditions ---
    // Buy when price drops 5% below current market (you can adjust this)
    private static final BigDecimal BUY_PRICE_DROP_PERCENTAGE = new BigDecimal("0.95"); // Buy at 5% below
    private static final BigDecimal MINIMUM_QUOTE_TO_TRADE = new BigDecimal("10.0"); // Minimum USDT/BUSD/etc to trade

    // --- Exit Conditions ---
    private static final BigDecimal TAKE_PROFIT_PERCENTAGE = new BigDecimal("1.03"); // Sell at 3% profit
    private static final BigDecimal STOP_LOSS_PERCENTAGE = new BigDecimal("0.98");   // Sell at 2% loss

    @Override
    public Signal decide(String symbol, BigDecimal currentPrice, Map<String, BigDecimal> balances, Optional<Position> openPositionOpt) {

        if (openPositionOpt.isPresent()) {
            // --- SELL LOGIC (POSITION IS OPEN) ---
            Position openPosition = openPositionOpt.get();
            BigDecimal entryPrice = openPosition.getEntryPrice();

            // Ensure entry price is not null before proceeding
            if (entryPrice == null) {
                System.out.println("⚠️ STRATEGY [HOLD]: In an open position but entry price is not set. Cannot determine exit.");
                return Signal.HOLD;
            }

            // Calculate exit targets
            BigDecimal takeProfitTarget = entryPrice.multiply(TAKE_PROFIT_PERCENTAGE).setScale(4, RoundingMode.HALF_UP);
            BigDecimal stopLossTarget = entryPrice.multiply(STOP_LOSS_PERCENTAGE).setScale(4, RoundingMode.HALF_UP);

            System.out.println("🎯 STRATEGY [SELL CHECK]: Entry: " + entryPrice.setScale(2, RoundingMode.HALF_UP) +
                               ", Current: " + currentPrice +
                               ", Stop-Loss Target: < " + stopLossTarget +
                               ", Take-Profit Target: > " + takeProfitTarget);

            if (currentPrice.compareTo(takeProfitTarget) > 0) {
                System.out.println("✅ STRATEGY [SELL]: Current price is above the TAKE PROFIT target. Signaling SELL.");
                return Signal.SELL;
            } else if (currentPrice.compareTo(stopLossTarget) < 0) {
                System.out.println("🚨 STRATEGY [SELL]: Current price is below the STOP LOSS target. Signaling SELL to limit losses.");
                return Signal.SELL;
            } else {
                return Signal.HOLD; // Price is between our targets, so we wait.
            }

        } else {
            // --- BUY LOGIC (NO POSITION IS OPEN) ---
            String[] parts = symbol.split("/");
            String baseCurrency = parts[0];  // e.g., BTC, ETH, ETC
            String quoteCurrency = parts[1]; // e.g., USDT, BUSD

            BigDecimal quoteBalance = balances.getOrDefault(quoteCurrency, BigDecimal.ZERO);

            // Dynamic buy threshold - could be based on moving average, support levels, etc.
            // For now, we'll use a simple strategy: always ready to buy if we have funds
            // You can modify this logic based on your trading strategy
            
            if (quoteBalance.compareTo(MINIMUM_QUOTE_TO_TRADE) > 0) {
                // Simple strategy: Buy at current market price if we have funds
                // You can add more sophisticated logic here (RSI, MACD, support levels, etc.)
                System.out.println("✅ STRATEGY [BUY]: Ready to buy " + baseCurrency + " at " + currentPrice + " " + quoteCurrency + ". Available balance: " + quoteBalance + " " + quoteCurrency);
                return Signal.BUY;
            } else {
                System.out.println("╔════════════════════════════════════════════════════════════════════╗");
                System.out.println("║                  ⚠️  INSUFFICIENT BALANCE ALERT  ⚠️                ║");
                System.out.println("╠════════════════════════════════════════════════════════════════════╣");
                System.out.println("║  Current Balance: " + String.format("%-46s", quoteBalance + " " + quoteCurrency) + "║");
                System.out.println("║  Minimum Required: " + String.format("%-45s", MINIMUM_QUOTE_TO_TRADE + " " + quoteCurrency) + "║");
                System.out.println("║  Symbol: " + String.format("%-59s", symbol) + "║");
                System.out.println("╠════════════════════════════════════════════════════════════════════╣");
                System.out.println("║  Action Required:                                                  ║");
                System.out.println("║  • Add funds to your testnet account                               ║");
                System.out.println("║  • Visit: https://testnet.binance.vision/                          ║");
                System.out.println("║  • Request testnet funds from faucet                               ║");
                System.out.println("║                                                                    ║");
                System.out.println("║  Bot Status: WAITING FOR FUNDS                                     ║");
                System.out.println("╚════════════════════════════════════════════════════════════════════╝");
                return Signal.HOLD; // Not enough funds
            }
        }
    }
}

