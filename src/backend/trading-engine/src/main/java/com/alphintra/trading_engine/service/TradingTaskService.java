package com.alphintra.trading_engine.service;

import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
import com.alphintra.trading_engine.model.BotStatus;
import com.alphintra.trading_engine.model.TradingBot;
import com.alphintra.trading_engine.repository.TradingBotRepository;
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
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class TradingTaskService {

    private final TradingBotRepository botRepository;

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public Optional<TradingBot> getFreshBotState(Long botId) {
        return botRepository.findById(botId);
    }
    
    private String extractBalanceFromJson(String responseBody, String asset) {
        try {
            String searchPattern = "\"asset\":\"" + asset + "\"";
            int assetIndex = responseBody.indexOf(searchPattern);
            if (assetIndex == -1) return "0.00000000";
            
            // Find the "free" field after the asset
            int freeIndex = responseBody.indexOf("\"free\":\"", assetIndex);
            if (freeIndex == -1) return "0.00000000";
            
            int startQuote = freeIndex + 8; // Skip "free":"
            int endQuote = responseBody.indexOf("\"", startQuote);
            if (endQuote == -1) return "0.00000000";
            
            return responseBody.substring(startQuote, endQuote);
        } catch (Exception e) {
            return "0.00000000";
        }
    }
    
    private void fetchAccountBalanceDirectAPI(WalletCredentialsDTO credentials, CurrencyPair pair) {
        try {
            System.out.println("🔍 Fetching account balances via direct Binance testnet API...");
            
            String apiKey = credentials.apiKey();
            String secretKey = credentials.secretKey();
            long timestamp = System.currentTimeMillis();
            
            // Create query string
            String queryString = "timestamp=" + timestamp;
            
            // Generate HMAC signature
            Mac mac = Mac.getInstance("HmacSHA256");
            SecretKeySpec secretKeySpec = new SecretKeySpec(secretKey.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
            mac.init(secretKeySpec);
            byte[] hash = mac.doFinal(queryString.getBytes(StandardCharsets.UTF_8));
            
            StringBuilder signature = new StringBuilder();
            for (byte b : hash) {
                signature.append(String.format("%02x", b));
            }
            
            // Build complete URL
            String url = "https://testnet.binance.vision/api/v3/account?" + queryString + "&signature=" + signature.toString();
            
            // Create HTTP request
            HttpClient client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .build();
                
            HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(30))
                .header("X-MBX-APIKEY", apiKey)
                .GET()
                .build();
            
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
            
            if (response.statusCode() == 200) {
                System.out.println("✅ Successfully fetched account info via direct API");
                System.out.println("📋 Raw Response: " + response.body().substring(0, Math.min(300, response.body().length())) + "...");
                
                // Parse the JSON response and extract actual balance amounts
                String responseBody = response.body();
                if (responseBody.contains("balances")) {
                    System.out.println("   💰 Account Balance Details:");
                    
                    // Extract specific currency balances with actual amounts
                    String etcBalance = extractBalanceFromJson(responseBody, "ETC");
                    String usdtBalance = extractBalanceFromJson(responseBody, "USDT");
                    String btcBalance = extractBalanceFromJson(responseBody, "BTC");
                    String bnbBalance = extractBalanceFromJson(responseBody, "BNB");
                    
                    // Display balances for trading pair
                    System.out.println("      📊 " + pair.base + ": " + etcBalance + " (Available)");
                    System.out.println("      📊 " + pair.counter + ": " + usdtBalance + " (Available)");
                    
                    // Show additional balances if non-zero
                    if (!btcBalance.equals("0.00000000")) {
                        System.out.println("      📊 BTC: " + btcBalance + " (Available)");
                    }
                    if (!bnbBalance.equals("0.00000000")) {
                        System.out.println("      📊 BNB: " + bnbBalance + " (Available)");
                    }
                    
                    // Show summary
                    System.out.println("      ℹ️ Trading Pair: " + pair + " - Ready for trading");
                    
                } else {
                    System.out.println("   ⚠️ No balance information in response");
                }
            } else {
                System.err.println("❌ Direct API request failed with status: " + response.statusCode());
                System.err.println("   Response: " + response.body());
            }
            
        } catch (Exception e) {
            System.err.println("❌ Error with direct API call: " + e.getMessage());
        }
    }
    
    @Async
    public void runTradingLoop(TradingBot bot, WalletCredentialsDTO credentials) {
        System.out.println("🚀 Starting background trading loop for bot ID: " + bot.getId());

        try {
            Exchange binance = ExchangeFactory.INSTANCE.createExchange(BinanceExchange.class);
            
            // Set API credentials
            binance.getExchangeSpecification().setApiKey(credentials.apiKey());
            binance.getExchangeSpecification().setSecretKey(credentials.secretKey());
            
            // Configure for Binance testnet
            binance.getExchangeSpecification().setExchangeSpecificParametersItem("Use_Sandbox", true);
            binance.getExchangeSpecification().setSslUri("https://testnet.binance.vision");
            binance.getExchangeSpecification().setHost("testnet.binance.vision");
            
            System.out.println("🔧 Configured Binance for testnet with API key: " + 
                credentials.apiKey().substring(0, 8) + "...");
            
            // Initialize the exchange
            binance.remoteInit();

            MarketDataService marketDataService = binance.getMarketDataService();

            String[] parts = bot.getSymbol().split("/");
            CurrencyPair pair = new CurrencyPair(parts[0], parts[1]);

            while (true) { 
                Optional<TradingBot> currentBotState = getFreshBotState(bot.getId());

                if (currentBotState.isEmpty() || currentBotState.get().getStatus() != BotStatus.RUNNING) {
                    System.out.println("⏹️ Stopping trading loop for bot ID: " + bot.getId());
                    break;
                }
                
                try {
                    // Suppress deprecation warning - method still works
                    @SuppressWarnings("deprecation")
                    Ticker ticker = marketDataService.getTicker(pair);
                    if (ticker != null) {
                        System.out.println("📈 " + bot.getSymbol() + " price = " + ticker.getLast());
                    } else {
                        System.err.println("⚠️ Failed to fetch ticker for " + bot.getSymbol());
                    }

                    // --- FETCH ACCOUNT BALANCES VIA DIRECT API ---
                    fetchAccountBalanceDirectAPI(credentials, pair);

                    Thread.sleep(5000);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    System.err.println("⏹️ Trading loop interrupted for bot " + bot.getId());
                    break;
                } catch (Exception e) {
                    System.err.println("❌ Error in trading loop: " + e.getMessage());
                }
            }
        } catch (Exception e) {
            System.err.println("🔥 FATAL ERROR in trading loop for bot " + bot.getId() + ": " + e.getMessage());
        }
    }
}
