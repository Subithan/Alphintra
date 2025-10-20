package com.alphintra.trading_engine.service;

import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
import com.alphintra.trading_engine.model.BotStatus;
import com.alphintra.trading_engine.model.PendingOrder;
import com.alphintra.trading_engine.model.Position;
import com.alphintra.trading_engine.model.PositionStatus;
import com.alphintra.trading_engine.model.TradingBot;
import com.alphintra.trading_engine.repository.PositionRepository;
import com.alphintra.trading_engine.repository.TradingBotRepository;
import com.alphintra.trading_engine.strategy.Signal;
import com.alphintra.trading_engine.strategy.SimplePriceStrategy;
import com.alphintra.trading_engine.strategy.TradingStrategy;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import org.knowm.xchange.Exchange;
import org.knowm.xchange.ExchangeFactory;
import org.knowm.xchange.binance.BinanceExchange;
import org.knowm.xchange.currency.CurrencyPair;
import org.knowm.xchange.dto.marketdata.Ticker;
import org.knowm.xchange.service.marketdata.MarketDataService;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class TradingTaskService {

    private final TradingBotRepository botRepository;
    private final OrderExecutionService orderExecutionService;
    private final PositionRepository positionRepository;
    private final BinanceTimeService binanceTimeService;
    
    // Mock mode for testing without valid API keys
    private static final boolean MOCK_MODE = Boolean.parseBoolean(System.getenv().getOrDefault("MOCK_TRADING_MODE", "false"));
    private final PendingOrderService pendingOrderService; // <-- ADD THIS

    private static final BigDecimal ETC_USDT_STEP_SIZE = new BigDecimal("0.01");

    // Singleton instances for the shared exchange connection
    private Exchange binanceExchange;
    private MarketDataService marketDataService;

    @PostConstruct
    public void initializeExchange() {
        System.out.println("🔧 Initializing shared Binance Exchange connection (this happens only once)...");
        try {
            binanceExchange = ExchangeFactory.INSTANCE.createExchange(BinanceExchange.class);
            binanceExchange.getExchangeSpecification().setExchangeSpecificParametersItem("Use_Sandbox", true);
            binanceExchange.getExchangeSpecification().setSslUri("https://testnet.binance.vision");
            binanceExchange.getExchangeSpecification().setHost("testnet.binance.vision");
            
            // The slow call, now executed only on application startup
            binanceExchange.remoteInit();
            marketDataService = binanceExchange.getMarketDataService();
            System.out.println("✅ Shared Binance Exchange connection initialized successfully.");
        } catch (IOException e) {
            System.err.println("🔥 FATAL ERROR: Could not initialize Binance Exchange on startup.");
            // In a production system, you might want to terminate the application if this fails.
            e.printStackTrace();
        }
    }

    @Async
    public void runTradingLoop(TradingBot bot, WalletCredentialsDTO credentials) {
        System.out.println("🚀 Starting background trading loop for bot ID: " + bot.getId());
        try {
            // --- The slow initialization is GONE from this loop ---
            TradingStrategy strategy = new SimplePriceStrategy();
            String[] parts = bot.getSymbol().split("/");
            CurrencyPair pair = new CurrencyPair(parts[0], parts[1]);
            String baseCurrency = parts[0];
            String quoteCurrency = parts[1];

            while (true) {
                Optional<TradingBot> currentBotState = getFreshBotState(bot.getId());
                if (currentBotState.isEmpty() || currentBotState.get().getStatus() != BotStatus.RUNNING) {
                    System.out.println("⏹️ Stopping trading loop for bot ID: " + bot.getId());
                    break;
                }

                try {
                    Optional<Position> openPosition = positionRepository.findByUserIdAndSymbolAndStatus(bot.getUserId(), bot.getSymbol(), PositionStatus.OPEN);

                    Ticker ticker = marketDataService.getTicker(pair);
                    if (ticker == null) {
                        System.err.println("⚠️ Failed to fetch ticker. Skipping loop.");
                        Thread.sleep(5000);
                        continue;
                    }
                    BigDecimal currentPrice = ticker.getLast();
                    System.out.println("📈 " + bot.getSymbol() + " price = " + currentPrice);

                    // --- CHECK PENDING ORDERS FIRST ---
                    checkAndTriggerPendingOrders(bot, credentials, currentPrice, openPosition);

                    // Only execute BUY orders if no position is open
                    // SELL orders are ONLY executed through pending order triggers (take-profit/stop-loss)
                    if (openPosition.isEmpty()) {
                        Map<String, BigDecimal> balances = fetchAccountBalanceDirectAPI(credentials, baseCurrency, quoteCurrency);
                        System.out.println("   💰 Balances: " + baseCurrency + "=" + balances.get(baseCurrency) + ", " + quoteCurrency + "=" + balances.get(quoteCurrency));
                        Signal signal = strategy.decide(bot.getSymbol(), currentPrice, balances, openPosition);
                        System.out.println("   🎯 Strategy Decision: " + signal);

                        if (signal == Signal.BUY) {
                            System.out.println("🔥 ACTION: Preparing to execute a BUY order.");
                            // Use bot's capital allocation percentage (convert from percentage to decimal)
                            BigDecimal availableUsdt = balances.get(quoteCurrency);
                            BigDecimal allocationDecimal = bot.getCapitalAllocationPercentage().divide(new BigDecimal("100"), 4, RoundingMode.DOWN);
                            BigDecimal usdtToSpend = availableUsdt.multiply(allocationDecimal);
                            System.out.println("   💵 Using " + usdtToSpend + " " + quoteCurrency + " (" + bot.getCapitalAllocationPercentage() + "% of " + availableUsdt + " available)");
                            
                            // Binance minimum notional check (typically $5-10 for most pairs)
                            BigDecimal MIN_NOTIONAL = new BigDecimal("5.0");
                            BigDecimal orderValue = usdtToSpend;
                            
                            if (orderValue.compareTo(MIN_NOTIONAL) < 0) {
                                System.out.println("⚠️ SKIPPING BUY: Order value " + orderValue + " " + quoteCurrency + " is below minimum notional " + MIN_NOTIONAL);
                                System.out.println("   ℹ️ You need at least $" + MIN_NOTIONAL + " worth of " + quoteCurrency + " to place an order.");
                                System.out.println("   ℹ️ Current allocation (" + bot.getCapitalAllocationPercentage() + "% of " + availableUsdt + ") = " + orderValue);
                            } else {
                                BigDecimal rawBuyQuantity = usdtToSpend.divide(currentPrice, 8, RoundingMode.DOWN);
                                BigDecimal adjustedBuyQuantity = adjustQuantityToStepSize(rawBuyQuantity, ETC_USDT_STEP_SIZE);
                                orderExecutionService.placeMarketOrder(bot, credentials, bot.getSymbol(), "BUY", adjustedBuyQuantity, openPosition, null, null, currentPrice);
                            }
                        } else {
                            System.out.println("   ⏸️ No position open. Waiting for BUY signal...");
                        }
                    } else {
                        System.out.println("   📊 Position is OPEN. Monitoring pending orders (TP/SL) for exit...");
                    }
                    
                    // Sleep: longer if position is open (waiting for TP/SL), shorter if searching for entry
                    long sleepTime = openPosition.isPresent() ? 3000 : 5000;
                    Thread.sleep(sleepTime);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    System.err.println("⏹️ Trading loop interrupted for bot " + bot.getId());
                    break;
                } catch (Exception e) {
                    System.err.println("❌ Error in trading loop: " + e.getMessage());
                    e.printStackTrace();
                }
            }
        } catch (Exception e) {
            System.err.println("🔥 FATAL ERROR in trading loop for bot " + bot.getId() + ": " + e.getMessage());
            e.printStackTrace();
        }
    }

    private Map<String, BigDecimal> fetchAccountBalanceDirectAPI(WalletCredentialsDTO credentials, String baseCurrency, String quoteCurrency) {
        Map<String, BigDecimal> balances = new HashMap<>();
        
        // MOCK MODE: Return fake balances for testing
        if (MOCK_MODE) {
            balances.put(baseCurrency, new BigDecimal("1000.0"));  // 1000 ETC
            balances.put(quoteCurrency, new BigDecimal("10000.0")); // 10,000 FDUSD
            System.out.println("🧪 MOCK MODE: Using fake balances - " + baseCurrency + "=1000.0, " + quoteCurrency + "=10000.0");
            return balances;
        }
        
        balances.put(baseCurrency, BigDecimal.ZERO);
        balances.put(quoteCurrency, BigDecimal.ZERO);
        try {
            String apiKey = credentials.apiKey();
            String secretKey = credentials.secretKey();
            long timestamp = binanceTimeService.getServerTime(); // Use synchronized time
            String queryString = "timestamp=" + timestamp;

            Mac mac = Mac.getInstance("HmacSHA256");
            SecretKeySpec secretKeySpec = new SecretKeySpec(secretKey.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
            mac.init(secretKeySpec);
            byte[] hash = mac.doFinal(queryString.getBytes(StandardCharsets.UTF_8));
            StringBuilder signature = new StringBuilder();
            for (byte b : hash) {
                signature.append(String.format("%02x", b));
            }
            String url = "https://testnet.binance.vision/api/v3/account?" + queryString + "&signature=" + signature.toString();
            HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();
            HttpRequest request = HttpRequest.newBuilder().uri(URI.create(url)).timeout(Duration.ofSeconds(30)).header("X-MBX-APIKEY", apiKey).GET().build();
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() == 200) {
                String responseBody = response.body();
                balances.put(baseCurrency, new BigDecimal(extractBalanceFromJson(responseBody, baseCurrency)));
                balances.put(quoteCurrency, new BigDecimal(extractBalanceFromJson(responseBody, quoteCurrency)));
                // Reduced logging noise for cleaner output
            } else {
                System.err.println("❌ Direct API request for balance failed with status: " + response.statusCode() + " | Response: " + response.body());
            }
        } catch (Exception e) {
            System.err.println("❌ Error with direct API call for balance: " + e.getMessage());
        }
        return balances;
    }
    
    // Unchanged helper methods
    @Transactional(propagation = Propagation.REQUIRES_NEW) public Optional<TradingBot> getFreshBotState(Long botId) { return botRepository.findById(botId); }
    private String extractBalanceFromJson(String responseBody, String asset) { try { String searchPattern = "\"asset\":\"" + asset + "\""; int assetIndex = responseBody.indexOf(searchPattern); if (assetIndex == -1) return "0.00000000"; int freeIndex = responseBody.indexOf("\"free\":\"", assetIndex); if (freeIndex == -1) return "0.00000000"; int startQuote = freeIndex + 8; int endQuote = responseBody.indexOf("\"", startQuote); if (endQuote == -1) return "0.00000000"; return responseBody.substring(startQuote, endQuote); } catch (Exception e) { return "0.00000000"; } }
    private BigDecimal adjustQuantityToStepSize(BigDecimal quantity, BigDecimal stepSize) { BigDecimal steps = quantity.divide(stepSize, 0, RoundingMode.DOWN); BigDecimal adjustedQuantity = steps.multiply(stepSize); int scale = stepSize.stripTrailingZeros().scale(); return adjustedQuantity.setScale(scale, RoundingMode.DOWN); }

    /**
     * Checks pending orders and triggers execution if price conditions are met
     * DISABLED: Auto-sell is turned off - positions remain open, pending orders are for display only
     */
    private void checkAndTriggerPendingOrders(TradingBot bot, WalletCredentialsDTO credentials, BigDecimal currentPrice, Optional<Position> openPosition) {
        // AUTO-SELL DISABLED - Positions will never be closed automatically
        // Pending orders are created for display purposes only (showing stop-loss and take-profit levels)
        
        if (openPosition.isEmpty()) {
            return; // No position = no pending orders to check
        }

        Position position = openPosition.get();
        List<PendingOrder> pendingOrders = pendingOrderService.getPendingOrdersBySymbol(bot.getSymbol());

        // Check and LOG if conditions would trigger, but don't execute
        for (PendingOrder pendingOrder : pendingOrders) {
            // Only check pending orders for the current position
            if (!pendingOrder.getPositionId().equals(position.getId())) {
                continue;
            }

            // Check take-profit condition (LOG ONLY)
            if (pendingOrder.getTakeProfitPrice() != null && 
                currentPrice.compareTo(pendingOrder.getTakeProfitPrice()) >= 0) {
                System.out.println("📊 TAKE_PROFIT LEVEL REACHED (not executing): Current: " + currentPrice + " >= Target: " + pendingOrder.getTakeProfitPrice());
            }
            // Check stop-loss condition (LOG ONLY)
            else if (pendingOrder.getStopLossPrice() != null && 
                     currentPrice.compareTo(pendingOrder.getStopLossPrice()) <= 0) {
                System.out.println("� STOP_LOSS LEVEL REACHED (not executing): Current: " + currentPrice + " <= Target: " + pendingOrder.getStopLossPrice());
            }

            // NOTE: No actual execution - positions stay open
            // Uncomment the code below to re-enable auto-sell:
            /*
            if (shouldTrigger) {
                pendingOrderService.markAsTriggered(pendingOrder, triggerReason);
                orderExecutionService.placeMarketOrder(
                    bot, credentials, bot.getSymbol(), "SELL", 
                    pendingOrder.getQuantity(), openPosition, triggerReason, pendingOrder.getId(), currentPrice
                );
                pendingOrderService.cancelOtherPendingOrders(position.getId(), pendingOrder.getId());
                break;
            }
            */
        }
    }
}


