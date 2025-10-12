package com.alphintra.trading_engine.service;

import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
import com.alphintra.trading_engine.model.BotStatus;
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
import java.util.Map;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class TradingTaskService {

    private final TradingBotRepository botRepository;
    private final OrderExecutionService orderExecutionService;
    private final PositionRepository positionRepository;
    private final BinanceTimeService binanceTimeService;

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

                    Map<String, BigDecimal> balances = fetchAccountBalanceDirectAPI(credentials, baseCurrency, quoteCurrency);
                    Signal signal = strategy.decide(bot.getSymbol(), currentPrice, balances, openPosition);

                    switch (signal) {
                        case BUY:
                            System.out.println("🔥 ACTION: Preparing to execute a BUY order.");
                            BigDecimal usdtToSpend = new BigDecimal("15.0");
                            BigDecimal rawBuyQuantity = usdtToSpend.divide(currentPrice, 8, RoundingMode.DOWN);
                            BigDecimal adjustedBuyQuantity = adjustQuantityToStepSize(rawBuyQuantity, ETC_USDT_STEP_SIZE);
                            orderExecutionService.placeMarketOrder(bot, credentials, bot.getSymbol(), "BUY", adjustedBuyQuantity, openPosition);
                            break;
                        case SELL:
                            if (openPosition.isPresent()) {
                                System.out.println("💰 ACTION: Preparing to execute a SELL order.");
                                BigDecimal sellQuantity = openPosition.get().getQuantity();
                                // We sell the exact quantity from our position, so no need to adjust
                                orderExecutionService.placeMarketOrder(bot, credentials, bot.getSymbol(), "SELL", sellQuantity, openPosition);
                            } else {
                                System.out.println("⚠️ STRATEGY WARNING: Received SELL signal but no open position found.");
                            }
                            break;
                        case HOLD:
                             // No action needed, but logging is handled by the strategy now.
                            break;
                    }
                    long sleepTime = (signal == Signal.BUY || signal == Signal.SELL) ? 15000 : 5000;
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
}




// package com.alphintra.trading_engine.service;

// import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
// import com.alphintra.trading_engine.model.BotStatus;
// import com.alphintra.trading_engine.model.PositionStatus;
// import com.alphintra.trading_engine.model.TradingBot;
// import com.alphintra.trading_engine.repository.PositionRepository;
// import com.alphintra.trading_engine.repository.TradingBotRepository;
// import com.alphintra.trading_engine.strategy.Signal;
// import com.alphintra.trading_engine.strategy.SimplePriceStrategy;
// import com.alphintra.trading_engine.strategy.TradingStrategy;
// import com.alphintra.trading_engine.model.Position;

// import lombok.RequiredArgsConstructor;

// import org.knowm.xchange.Exchange;
// import org.knowm.xchange.ExchangeFactory;
// import org.knowm.xchange.binance.BinanceExchange;
// import org.knowm.xchange.currency.CurrencyPair;
// import org.knowm.xchange.dto.marketdata.Ticker;
// import org.knowm.xchange.service.marketdata.MarketDataService;
// import org.springframework.scheduling.annotation.Async;
// import org.springframework.stereotype.Service;
// import org.springframework.transaction.annotation.Propagation;
// import org.springframework.transaction.annotation.Transactional;

// import javax.crypto.Mac;
// import javax.crypto.spec.SecretKeySpec;
// import java.net.http.HttpClient;
// import java.net.http.HttpRequest;
// import java.net.http.HttpResponse;
// import java.math.BigDecimal;
// import java.net.URI;
// import java.nio.charset.StandardCharsets;
// import java.time.Duration;
// import java.util.HashMap;
// import java.util.Map;
// import java.util.Optional;
// import java.math.RoundingMode;

// @Service
// @RequiredArgsConstructor
// public class TradingTaskService {

//     private final TradingBotRepository botRepository;
//     private final OrderExecutionService orderExecutionService;
//     private final PositionRepository positionRepository;

//     // The stepSize for ETC on the testnet appears to be 0.01, not 0.001.
//     private static final BigDecimal ETC_USDT_STEP_SIZE = new BigDecimal("0.01");

//     @Transactional(propagation = Propagation.REQUIRES_NEW)
//     public Optional<TradingBot> getFreshBotState(Long botId) {
//         return botRepository.findById(botId);
//     }
    
//     // ... (extractBalanceFromJson and fetchAccountBalanceDirectAPI methods are unchanged) ...
//     private String extractBalanceFromJson(String responseBody, String asset) {
//         try {
//             String searchPattern = "\"asset\":\"" + asset + "\"";
//             int assetIndex = responseBody.indexOf(searchPattern);
//             if (assetIndex == -1) return "0.00000000";
//             int freeIndex = responseBody.indexOf("\"free\":\"", assetIndex);
//             if (freeIndex == -1) return "0.00000000";
//             int startQuote = freeIndex + 8;
//             int endQuote = responseBody.indexOf("\"", startQuote);
//             if (endQuote == -1) return "0.00000000";
//             return responseBody.substring(startQuote, endQuote);
//         } catch (Exception e) {
//             return "0.00000000";
//         }
//     }
    
//     private Map<String, BigDecimal>  fetchAccountBalanceDirectAPI(WalletCredentialsDTO credentials, String baseCurrency, String quoteCurrency) {
//         Map<String, BigDecimal> balances = new HashMap<>();
//         balances.put(baseCurrency, BigDecimal.ZERO);
//         balances.put(quoteCurrency, BigDecimal.ZERO);
//         try {
//             // System.out.println("🔍 Fetching account balances via direct Binance testnet API...");
//             String apiKey = credentials.apiKey();
//             String secretKey = credentials.secretKey();
//             long timestamp = System.currentTimeMillis();
//             String queryString = "timestamp=" + timestamp;
//             Mac mac = Mac.getInstance("HmacSHA256");
//             SecretKeySpec secretKeySpec = new SecretKeySpec(secretKey.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
//             mac.init(secretKeySpec);
//             byte[] hash = mac.doFinal(queryString.getBytes(StandardCharsets.UTF_8));
//             StringBuilder signature = new StringBuilder();
//             for (byte b : hash) {
//                 signature.append(String.format("%02x", b));
//             }
//             String url = "https://testnet.binance.vision/api/v3/account?" + queryString + "&signature=" + signature.toString();
//             HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();
//             HttpRequest request = HttpRequest.newBuilder().uri(URI.create(url)).timeout(Duration.ofSeconds(30)).header("X-MBX-APIKEY", apiKey).GET().build();
//             HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
//             if (response.statusCode() == 200) {
//                 // System.out.println("✅ Successfully fetched account info via direct API");
//                 String responseBody = response.body();
//                 String baseBalanceStr = extractBalanceFromJson(responseBody, baseCurrency);
//                 String quoteBalanceStr = extractBalanceFromJson(responseBody, quoteCurrency);
//                 balances.put(baseCurrency, new BigDecimal(baseBalanceStr));
//                 balances.put(quoteCurrency, new BigDecimal(quoteBalanceStr));
//                 System.out.println("   💰 Account Balances Updated:");
//                 System.out.println("      📊 " + baseCurrency + ": " + balances.get(baseCurrency) + " (Available)");
//                 System.out.println("      📊 " + quoteCurrency + ": " + balances.get(quoteCurrency) + " (Available)");
//             } else {
//                 System.err.println("❌ Direct API request failed with status: " + response.statusCode());
//                 System.err.println("   Response: " + response.body());
//             }
//         } catch (Exception e) {
//             System.err.println("❌ Error with direct API call: " + e.getMessage());
//         }
//         return balances;
//     }

//     @Async
//     public void runTradingLoop(TradingBot bot, WalletCredentialsDTO credentials) {
//         System.out.println("🚀 Starting background trading loop for bot ID: " + bot.getId());
//         try {
//             Exchange binance = ExchangeFactory.INSTANCE.createExchange(BinanceExchange.class);
//             binance.getExchangeSpecification().setApiKey(credentials.apiKey());
//             binance.getExchangeSpecification().setSecretKey(credentials.secretKey());
//             binance.getExchangeSpecification().setExchangeSpecificParametersItem("Use_Sandbox", true);
//             // binance.getExchangeSpecification().setSslUri("https://testnet.binance.vision");
//             // binance.getExchangeSpecification().setHost("testnet.binance.vision");
//             System.out.println("🔧 Configured Binance for testnet with API key: " + credentials.apiKey().substring(0, 8) + "...");
//             binance.remoteInit();

//             MarketDataService marketDataService = binance.getMarketDataService();
//             TradingStrategy strategy = new SimplePriceStrategy();
//             String[] parts = bot.getSymbol().split("/");
//             CurrencyPair pair = new CurrencyPair(parts[0], parts[1]);
//             String baseCurrency = parts[0];
//             String quoteCurrency = parts[1];

//             while (true) { 
//                 Optional<TradingBot> currentBotState = getFreshBotState(bot.getId());
//                 if (currentBotState.isEmpty() || currentBotState.get().getStatus() != BotStatus.RUNNING) {
//                     System.out.println("⏹️ Stopping trading loop for bot ID: " + bot.getId());
//                     break;
//                 }
                
//                 try {
//                     Optional<Position> openPosition = positionRepository.findByUserIdAndSymbolAndStatus(bot.getUserId(), bot.getSymbol(), PositionStatus.OPEN);

//                     // if (openPosition.isPresent()) {
//                     //     System.out.println("ℹ️ POSITION MANAGEMENT: Already in an open position for " + bot.getSymbol() + ". Skipping BUY logic.");
//                     //     // Here you would add logic to check if it's time to SELL
//                     //     // For now, we will just hold.
//                     //     Thread.sleep(10000); // Check less frequently when in a position
//                     //     continue; // Skip the rest of the loop
//                     // }

//                     Ticker ticker = marketDataService.getTicker(pair);
//                     if (ticker == null) {
//                         System.err.println("⚠️ Failed to fetch ticker for " + bot.getSymbol() + ". Skipping loop.");
//                         Thread.sleep(5000);
//                         continue;
//                     }
//                     BigDecimal currentPrice = ticker.getLast();
//                     System.out.println("📈 " + bot.getSymbol() + " price = " + currentPrice);
            
//                     Map<String, BigDecimal> balances = fetchAccountBalanceDirectAPI(credentials,  baseCurrency, quoteCurrency);
//                     Signal signal = strategy.decide(bot.getSymbol(), currentPrice, balances, openPosition);
                    
//                     switch (signal) {
//                         case BUY:
//                             System.out.println("🔥 ACTION: Preparing to execute a BUY order.");
//                             BigDecimal usdtToSpend = new BigDecimal("15.0"); 
//                             BigDecimal rawBuyQuantity = usdtToSpend.divide(currentPrice, 8, RoundingMode.DOWN);
                            
//                             BigDecimal adjustedBuyQuantity = adjustQuantityToStepSize(rawBuyQuantity, ETC_USDT_STEP_SIZE);
                    
//                             orderExecutionService.placeMarketOrder(bot, credentials, bot.getSymbol(), "BUY", adjustedBuyQuantity, openPosition);
//                             break;
//                         case SELL:
//                             // System.out.println("💰 ACTION: Preparing to execute a SELL order.");
//                             // BigDecimal rawSellQuantity = new BigDecimal("0.5");

//                             // BigDecimal adjustedSellQuantity = adjustQuantityToStepSize(rawSellQuantity, ETC_USDT_STEP_SIZE);
                            
//                             // orderExecutionService.placeMarketOrder(bot,credentials, bot.getSymbol(), "SELL", adjustedSellQuantity);
//                             // break;
//                             if (openPosition.isPresent()) {
//                                 System.out.println("💰 ACTION: Preparing to execute a SELL order to close position.");
//                                 // The quantity to sell is the entire quantity of our open position.
//                                 BigDecimal sellQuantity = openPosition.get().getQuantity();
//                                 BigDecimal adjustedSellQuantity = adjustQuantityToStepSize(sellQuantity, ETC_USDT_STEP_SIZE);
//                                 orderExecutionService.placeMarketOrder(bot, credentials, bot.getSymbol(), "SELL", adjustedSellQuantity, openPosition);
//                             } else {
//                                 System.out.println("⚠️ STRATEGY WARNING: Received SELL signal but no open position found.");
//                             }
//                             break;
//                         case HOLD:
//                             System.out.println("🧘 ACTION: Holding position. No trade executed.");
//                             break;
//                     }
//                     long sleepTime = (signal == Signal.BUY || signal == Signal.SELL) ? 15000 : 5000;
//                     Thread.sleep(sleepTime);
//                 } catch (InterruptedException e) {
//                     Thread.currentThread().interrupt();
//                     System.err.println("⏹️ Trading loop interrupted for bot " + bot.getId());
//                     break;
//                 } catch (Exception e) {
//                     System.err.println("❌ Error in trading loop: " + e.getMessage());
//                 }
//             }
//         } catch (Exception e) {
//             System.err.println("🔥 FATAL ERROR in trading loop for bot " + bot.getId() + ": " + e.getMessage());
//             e.printStackTrace();
//         }
//     }

//     private BigDecimal adjustQuantityToStepSize(BigDecimal quantity, BigDecimal stepSize) {
//         BigDecimal steps = quantity.divide(stepSize, 0, RoundingMode.DOWN);
//         BigDecimal adjustedQuantity = steps.multiply(stepSize);
//         int scale = stepSize.stripTrailingZeros().scale();
//         return adjustedQuantity.setScale(scale, RoundingMode.DOWN);
//     }
// }












// package com.alphintra.trading_engine.service;

// import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
// import com.alphintra.trading_engine.model.BotStatus;
// import com.alphintra.trading_engine.model.TradingBot;
// import com.alphintra.trading_engine.repository.TradingBotRepository;
// import com.alphintra.trading_engine.strategy.Signal;
// import com.alphintra.trading_engine.strategy.SimplePriceStrategy;
// import com.alphintra.trading_engine.strategy.TradingStrategy;

// import lombok.RequiredArgsConstructor;

// import org.knowm.xchange.Exchange;
// import org.knowm.xchange.ExchangeFactory;
// import org.knowm.xchange.binance.BinanceExchange;
// import org.knowm.xchange.currency.CurrencyPair;
// import org.knowm.xchange.dto.marketdata.Ticker;
// import org.knowm.xchange.service.marketdata.MarketDataService;
// import org.springframework.scheduling.annotation.Async;
// import org.springframework.stereotype.Service;
// import org.springframework.transaction.annotation.Propagation;
// import org.springframework.transaction.annotation.Transactional;

// import javax.crypto.Mac;
// import javax.crypto.spec.SecretKeySpec;
// import java.net.http.HttpClient;
// import java.net.http.HttpRequest;
// import java.net.http.HttpResponse;
// import java.math.BigDecimal;
// import java.net.URI;
// import java.nio.charset.StandardCharsets;
// import java.time.Duration;
// import java.util.HashMap;
// import java.util.Map;
// import java.util.Optional;
// import java.math.RoundingMode;

// @Service
// @RequiredArgsConstructor
// public class TradingTaskService {

//     private final TradingBotRepository botRepository;
//     private final OrderExecutionService orderExecutionService;

//     private static final BigDecimal ETC_USDT_STEP_SIZE = new BigDecimal("0.001");

//     @Transactional(propagation = Propagation.REQUIRES_NEW)
//     public Optional<TradingBot> getFreshBotState(Long botId) {
//         return botRepository.findById(botId);
//     }
    
//     private String extractBalanceFromJson(String responseBody, String asset) {
//         try {
//             String searchPattern = "\"asset\":\"" + asset + "\"";
//             int assetIndex = responseBody.indexOf(searchPattern);
//             if (assetIndex == -1) return "0.00000000";
            
//             // Find the "free" field after the asset
//             int freeIndex = responseBody.indexOf("\"free\":\"", assetIndex);
//             if (freeIndex == -1) return "0.00000000";
            
//             int startQuote = freeIndex + 8; // Skip "free":"
//             int endQuote = responseBody.indexOf("\"", startQuote);
//             if (endQuote == -1) return "0.00000000";
            
//             return responseBody.substring(startQuote, endQuote);
//         } catch (Exception e) {
//             return "0.00000000";
//         }
//     }
    
//     private Map<String, BigDecimal>  fetchAccountBalanceDirectAPI(WalletCredentialsDTO credentials, String baseCurrency, String quoteCurrency) {
//         Map<String, BigDecimal> balances = new HashMap<>();
//         // Initialize with zero to avoid nulls
//         balances.put(baseCurrency, BigDecimal.ZERO);
//         balances.put(quoteCurrency, BigDecimal.ZERO);

//         try {
//             System.out.println("🔍 Fetching account balances via direct Binance testnet API...");
            
//             String apiKey = credentials.apiKey();
//             String secretKey = credentials.secretKey();
//             long timestamp = System.currentTimeMillis();
            
//             // Create query string
//             String queryString = "timestamp=" + timestamp;
            
//             // Generate HMAC signature
//             Mac mac = Mac.getInstance("HmacSHA256");
//             SecretKeySpec secretKeySpec = new SecretKeySpec(secretKey.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
//             mac.init(secretKeySpec);
//             byte[] hash = mac.doFinal(queryString.getBytes(StandardCharsets.UTF_8));
            
//             StringBuilder signature = new StringBuilder();
//             for (byte b : hash) {
//                 signature.append(String.format("%02x", b));
//             }
            
//             // Build complete URL
//             String url = "https://testnet.binance.vision/api/v3/account?" + queryString + "&signature=" + signature.toString();
            
//             // Create HTTP request
//             HttpClient client = HttpClient.newBuilder()
//                 .connectTimeout(Duration.ofSeconds(10))
//                 .build();
                
//             HttpRequest request = HttpRequest.newBuilder()
//                 .uri(URI.create(url))
//                 .timeout(Duration.ofSeconds(30))
//                 .header("X-MBX-APIKEY", apiKey)
//                 .GET()
//                 .build();
            
//             HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
            
//             if (response.statusCode() == 200) {
//                 System.out.println("✅ Successfully fetched account info via direct API");
//                 String responseBody = response.body();
                
//                 String baseBalanceStr = extractBalanceFromJson(responseBody, baseCurrency);
//                 String quoteBalanceStr = extractBalanceFromJson(responseBody, quoteCurrency);
                
//                 balances.put(baseCurrency, new BigDecimal(baseBalanceStr));
//                 balances.put(quoteCurrency, new BigDecimal(quoteBalanceStr));

//                 System.out.println("   💰 Account Balances Updated:");
//                 System.out.println("      📊 " + baseCurrency + ": " + balances.get(baseCurrency) + " (Available)");
//                 System.out.println("      📊 " + quoteCurrency + ": " + balances.get(quoteCurrency) + " (Available)");
                
//             } else {
//                 System.err.println("❌ Direct API request failed with status: " + response.statusCode());
//                 System.err.println("   Response: " + response.body());
//             }
            
//         } catch (Exception e) {
//             System.err.println("❌ Error with direct API call: " + e.getMessage());
//         }
//         return balances;
//     }

//     @Async
//     public void runTradingLoop(TradingBot bot, WalletCredentialsDTO credentials) {
//         System.out.println("🚀 Starting background trading loop for bot ID: " + bot.getId());

//         try {
//             Exchange binance = ExchangeFactory.INSTANCE.createExchange(BinanceExchange.class);
            
//             // Set API credentials
//             binance.getExchangeSpecification().setApiKey(credentials.apiKey());
//             binance.getExchangeSpecification().setSecretKey(credentials.secretKey());
            
//             // Configure for Binance testnet
//             binance.getExchangeSpecification().setExchangeSpecificParametersItem("Use_Sandbox", true);
//             binance.getExchangeSpecification().setSslUri("https://testnet.binance.vision");
//             binance.getExchangeSpecification().setHost("testnet.binance.vision");
            
//             System.out.println("🔧 Configured Binance for testnet with API key: " + 
//                 credentials.apiKey().substring(0, 8) + "...");
            
//             // Initialize the exchange
//             binance.remoteInit();

//             MarketDataService marketDataService = binance.getMarketDataService();
//             TradingStrategy strategy = new SimplePriceStrategy();

//             String[] parts = bot.getSymbol().split("/");
//             CurrencyPair pair = new CurrencyPair(parts[0], parts[1]);
//             String baseCurrency = parts[0];
//             String quoteCurrency = parts[1];

//             while (true) { 
//                 Optional<TradingBot> currentBotState = getFreshBotState(bot.getId());

//                 if (currentBotState.isEmpty() || currentBotState.get().getStatus() != BotStatus.RUNNING) {
//                     System.out.println("⏹️ Stopping trading loop for bot ID: " + bot.getId());
//                     break;
//                 }
                
//                 try {
//                     // --- 1. FETCH MARKET DATA ---
//                     Ticker ticker = marketDataService.getTicker(pair);
//                     if (ticker == null) {
//                         System.err.println("⚠️ Failed to fetch ticker for " + bot.getSymbol() + ". Skipping loop.");
//                         Thread.sleep(5000);
//                         continue;
//                     }
//                     BigDecimal currentPrice = ticker.getLast();
//                     System.out.println("📈 " + bot.getSymbol() + " price = " + currentPrice);
            

//                     // --- FETCH ACCOUNT BALANCES VIA DIRECT API ---
//                     Map<String, BigDecimal> balances = fetchAccountBalanceDirectAPI(credentials,  baseCurrency, quoteCurrency);

//                     // --- 2. MAKE DECISION ---
//                     // Pass the prepared data to the strategy to get a signal
//                     Signal signal = strategy.decide(bot.getSymbol(), currentPrice, balances);
                    
//                     // --- 3. ACT ON DECISION ---
//                     switch (signal) {
//                         case BUY:
//                             System.out.println("🔥 ACTION: Preparing to execute a BUY order.");
//                             // TODO: Next step is to call the Order Placement service here.
//                             BigDecimal usdtToSpend = new BigDecimal("15.0"); 
//                             BigDecimal rawBuyQuantity = usdtToSpend.divide(currentPrice, 8, RoundingMode.DOWN);

//                             // --- FIX IS HERE: Format the quantity ---
//                             BigDecimal formattedBuyQuantity = adjustQuantityToStepSize(rawBuyQuantity, ETC_USDT_STEP_SIZE);
                    
//                             // --- 3. EXECUTE THE ORDER ---
//                             orderExecutionService.placeMarketOrder(credentials, bot.getSymbol(), "BUY", formattedBuyQuantity);
//                             break;
//                         case SELL:
//                             System.out.println("💰 ACTION: Preparing to execute a SELL order.");
//                             // TODO: Next step is to call the Order Placement service here.
//                             // Example: Sell 0.5 ETC
//                             BigDecimal rawSellQuantity = new BigDecimal("0.5");

//                             // --- FIX IS HERE: Format the quantity ---
//                             BigDecimal formattedSellQuantity = adjustQuantityToStepSize(rawSellQuantity, ETC_USDT_STEP_SIZE);

//                             // Pass the CORRECTLY formatted quantity to the service
//                             orderExecutionService.placeMarketOrder(credentials, bot.getSymbol(), "SELL", formattedSellQuantity);
//                             break;
//                         case HOLD:
//                             System.out.println("🧘 ACTION: Holding position. No trade executed.");
//                             break;
//                     }
//                     long sleepTime = (signal == Signal.BUY || signal == Signal.SELL) ? 15000 : 5000;
//                     Thread.sleep(sleepTime);
//                 } catch (InterruptedException e) {
//                     Thread.currentThread().interrupt();
//                     System.err.println("⏹️ Trading loop interrupted for bot " + bot.getId());
//                     break;
//                 } catch (Exception e) {
//                     System.err.println("❌ Error in trading loop: " + e.getMessage());
//                 }
//             }
//         } catch (Exception e) {
//             System.err.println("🔥 FATAL ERROR in trading loop for bot " + bot.getId() + ": " + e.getMessage());
//         }
//     }

//     private BigDecimal adjustQuantityToStepSize(BigDecimal quantity, BigDecimal stepSize) {
//         // 1. Divide the quantity by the step size to see how many "steps" it contains.
//         BigDecimal steps = quantity.divide(stepSize, 0, RoundingMode.DOWN);
        
//         // 2. Multiply the integer number of steps by the step size to get the final adjusted quantity.
//         BigDecimal adjustedQuantity = steps.multiply(stepSize);

//         // 3. Format to the correct number of decimal places to avoid scientific notation.
//         int scale = stepSize.stripTrailingZeros().scale();
//         return adjustedQuantity.setScale(scale, RoundingMode.DOWN);
//     }
// }
