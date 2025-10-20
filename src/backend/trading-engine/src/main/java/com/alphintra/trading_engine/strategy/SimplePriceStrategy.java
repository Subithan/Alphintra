// package com.alphintra.trading_engine.strategy;

// import com.alphintra.trading_engine.model.Position;
// import java.math.BigDecimal;
// import java.util.Map;
// import java.util.Optional;
// import java.math.RoundingMode;

// /**
//  * A simple trading strategy that decides to buy or sell based on fixed price thresholds.
//  */
// public class SimplePriceStrategy implements TradingStrategy {

//     // Define the price thresholds using BigDecimal for precision.
//     private static final BigDecimal BUY_PRICE_THRESHOLD = new BigDecimal("19.50");
//     private static final BigDecimal SELL_PRICE_THRESHOLD = new BigDecimal("20.50");
//     private static final BigDecimal MINIMUM_USDT_TO_TRADE = new BigDecimal("10.0"); // Min balance to attempt a buy
//     private static final BigDecimal MINIMUM_ETC_TO_TRADE = new BigDecimal("0.1"); // Min balance to attempt a sell

//     // --- NEW SELL LOGIC ---
//     // Sell when the current price is 3% higher than our entry price.
//     private static final BigDecimal TAKE_PROFIT_PERCENTAGE = new BigDecimal("1.03"); // 103%

//     @Override
//     public Signal decide(String symbol, BigDecimal currentPrice, Map<String, BigDecimal> balances) {
//         // Extract the base and quote currency from the symbol (e.g., ETC/USDT -> ETC, USDT)
//         String[] parts = symbol.split("/");
//         String baseCurrency = parts[0];  // e.g., ETC
//         String quoteCurrency = parts[1]; // e.g., USDT

//         // Get available balances, defaulting to zero if not present.
//         BigDecimal baseBalance = balances.getOrDefault(baseCurrency, BigDecimal.ZERO);
//         BigDecimal quoteBalance = balances.getOrDefault(quoteCurrency, BigDecimal.ZERO);

//         // --- Decision Logic ---

//         // 1. Check for BUY signal
//         // Condition: Is the current price below our buy threshold?
//         if (currentPrice.compareTo(BUY_PRICE_THRESHOLD) < 0) {
//             // Condition: Do we have enough USDT to make a trade?
//             if (quoteBalance.compareTo(MINIMUM_USDT_TO_TRADE) > 0) {
//                 System.out.println("✅ STRATEGY [BUY]: Price " + currentPrice + " is below threshold " + BUY_PRICE_THRESHOLD + ". Sufficient " + quoteCurrency + " balance available.");
//                 return Signal.BUY;
//             } else {
//                 System.out.println("ℹ️ STRATEGY [HOLD]: Price is low, but insufficient " + quoteCurrency + " balance (" + quoteBalance + ") to buy.");
//                 return Signal.HOLD;
//             }
//         }
//         // 2. Check for SELL signal
//         // Condition: Is the current price above our sell threshold?
//         else if (currentPrice.compareTo(SELL_PRICE_THRESHOLD) > 0) {
//             // Condition: Do we have any ETC to sell?
//             if (baseBalance.compareTo(MINIMUM_ETC_TO_TRADE) > 0) {
//                 System.out.println("✅ STRATEGY [SELL]: Price " + currentPrice + " is above threshold " + SELL_PRICE_THRESHOLD + ". Sufficient " + baseCurrency + " balance available.");
//                 return Signal.SELL;
//             } else {
//                 System.out.println("ℹ️ STRATEGY [HOLD]: Price is high, but insufficient " + baseCurrency + " balance (" + baseBalance + ") to sell.");
//                 return Signal.HOLD;
//             }
//         }
//         // 3. Otherwise, HOLD
//         else {
//             System.out.println("ℹ️ STRATEGY [HOLD]: Price " + currentPrice + " is between thresholds. No action.");
//             return Signal.HOLD;
//         }
//     }
// }


// package com.alphintra.trading_engine.strategy;

// import com.alphintra.trading_engine.model.Position; // <-- Import Position

// import java.math.BigDecimal;
// import java.math.RoundingMode;
// import java.util.Map;
// import java.util.Optional; // <-- Import Optional

// /**
//  * A simple strategy that now includes a "Take Profit" target for selling.
//  */
// public class SimplePriceStrategy implements TradingStrategy {

//     private static final BigDecimal BUY_PRICE_THRESHOLD = new BigDecimal("19.50"); // Reset to a realistic value
    
//     // --- NEW SELL LOGIC ---
//     // Sell when the current price is 3% higher than our entry price.
//     private static final BigDecimal TAKE_PROFIT_PERCENTAGE = new BigDecimal("1.03"); // 103%
//     private static final BigDecimal STOP_LOSS_PERCENTAGE = new BigDecimal("0.98");   // Sell at 2% loss

//     // We still need a minimum balance to attempt a sell.
//     private static final BigDecimal MINIMUM_ETC_TO_TRADE = new BigDecimal("0.1");

//     // The decide method signature needs to change to accept the position
//     public Signal decide(String symbol, BigDecimal currentPrice, Map<String, BigDecimal> balances, Optional<Position> openPositionOpt) {
//         String baseCurrency = symbol.split("/")[0];
//         BigDecimal baseBalance = balances.getOrDefault(baseCurrency, BigDecimal.ZERO);

//         // --- 1. CHECK IF WE ARE IN A POSITION ---
//         if (openPositionOpt.isPresent()) {
//             Position openPosition = openPositionOpt.get();
//             BigDecimal entryPrice = openPosition.getEntryPrice();

//             // If entry price is null for some reason, we can't make a decision.
//             if (entryPrice == null) {
//                 System.out.println("ℹ️ STRATEGY [HOLD]: In position, but entry price is unknown. Holding.");
//                 return Signal.HOLD;
//             }

//             BigDecimal takeProfitTarget = entryPrice.multiply(TAKE_PROFIT_PERCENTAGE);
//             BigDecimal stopLossTarget = entryPrice.multiply(STOP_LOSS_PERCENTAGE).setScale(4, RoundingMode.HALF_UP);
//             System.out.println("🎯 STRATEGY [SELL CHECK]: Entry Price: " + entryPrice + ", Current Price: " + currentPrice + ", Take Profit Target: " + takeProfitTarget);

//             if (currentPrice.compareTo(takeProfitTarget) > 0) {
//                 System.out.println("✅ STRATEGY [SELL]: Current price is above the TAKE PROFIT target. Signaling SELL.");
//                 return Signal.SELL;
//             } else if (currentPrice.compareTo(stopLossTarget) < 0) {
//                 System.out.println("🚨 STRATEGY [SELL]: Current price is below the STOP LOSS target. Signaling SELL to limit losses.");
//                 return Signal.SELL;
//             } else {
//                 return Signal.HOLD; // Price is between our targets, so we wait.
//             }
//         } 
        
//         // --- 2. IF NOT IN A POSITION, CHECK FOR BUY SIGNAL ---
//         else {
//             if (currentPrice.compareTo(BUY_PRICE_THRESHOLD) < 0) {
//                 // (Your existing BUY logic can remain here)
//                 System.out.println("✅ STRATEGY [BUY]: Price is below threshold. Signaling BUY.");
//                 return Signal.BUY;
//             }
//         }

//         // 3. If none of the above, hold.
//         System.out.println("ℹ️ STRATEGY [HOLD]: Conditions not met for BUY or SELL.");
//         return Signal.HOLD;
//     }
// }


package com.alphintra.trading_engine.strategy;

import com.alphintra.trading_engine.model.Position;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;
import java.util.Optional;

/**
 * A simple trading strategy that includes both a take-profit and a stop-loss exit strategy.
 */
public class SimplePriceStrategy implements TradingStrategy {

    // --- Entry Conditions ---
    private static final BigDecimal BUY_PRICE_THRESHOLD = new BigDecimal("17.00");  // Lower than current price of ~$16.12
    private static final BigDecimal MINIMUM_USDT_TO_TRADE = new BigDecimal("0.50");  // Lower minimum to allow trading with testnet balance

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
            String quoteCurrency = symbol.split("/")[1]; // e.g., USDT
            BigDecimal quoteBalance = balances.getOrDefault(quoteCurrency, BigDecimal.ZERO);

            if (currentPrice.compareTo(BUY_PRICE_THRESHOLD) < 0) {
                if (quoteBalance.compareTo(MINIMUM_USDT_TO_TRADE) > 0) {
                    System.out.println("✅ STRATEGY [BUY]: Price is below threshold. Signaling BUY.");
                    return Signal.BUY;
                } else {
                    return Signal.HOLD; // Price is good, but not enough funds
                }
            } else {
                return Signal.HOLD; // Price is too high to buy
            }
        }
    }
}

