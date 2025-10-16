// package com.alphintra.trading_engine.service;

// import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
// import com.alphintra.trading_engine.model.PositionStatus;
// import com.alphintra.trading_engine.repository.PositionRepository;
// import com.alphintra.trading_engine.repository.TradeOrderRepository;

// import jakarta.transaction.Transactional;

// import com.alphintra.trading_engine.model.Position;
// import com.alphintra.trading_engine.model.TradingBot;

// import lombok.RequiredArgsConstructor;

// import org.json.JSONArray;
// import org.json.JSONObject; 
// import org.springframework.stereotype.Service;

// import javax.crypto.Mac;
// import javax.crypto.spec.SecretKeySpec;
// import java.math.BigDecimal;
// import java.net.URI;
// import java.net.http.HttpClient;
// import java.net.http.HttpRequest;
// import java.net.http.HttpResponse;
// import java.nio.charset.StandardCharsets;
// import java.time.Duration;
// import java.time.LocalDateTime;
// import java.util.Optional;

// @Service
// @RequiredArgsConstructor
// public class OrderExecutionService {
//     private final PositionRepository positionRepository;
//     private final TradeOrderRepository tradeOrderRepository;
//     private final HttpClient httpClient = HttpClient.newBuilder()
//             .connectTimeout(Duration.ofSeconds(10))
//             .build();
//     @Transactional
//     public void placeMarketOrder(TradingBot bot, WalletCredentialsDTO credentials, String symbol, String side, BigDecimal quantity, Optional<Position> openPositionOpt) {
//         System.out.println("EXECUTING ORDER: " + side + " " + quantity + " " + symbol);

//         try {
//             String apiKey = credentials.apiKey();
//             String secretKey = credentials.secretKey();
//             long timestamp = System.currentTimeMillis();

//             // Note: Binance API requires the symbol without a slash (e.g., ETCUSDT)
//             String apiSymbol = symbol.replace("/", "");

//             // Build the query string with all required parameters for a market order
//             String queryString = "symbol=" + apiSymbol +
//                                  "&side=" + side +
//                                  "&type=MARKET" +
//                                  "&quantity=" + quantity.toPlainString() +
//                                  "&timestamp=" + timestamp;

//             // Generate HMAC-SHA256 signature (same logic as the account balance check)
//             Mac mac = Mac.getInstance("HmacSHA256");
//             SecretKeySpec secretKeySpec = new SecretKeySpec(secretKey.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
//             mac.init(secretKeySpec);
//             byte[] hash = mac.doFinal(queryString.getBytes(StandardCharsets.UTF_8));
            
//             StringBuilder signature = new StringBuilder();
//             for (byte b : hash) {
//                 signature.append(String.format("%02x", b));
//             }

//             // Build the complete URL
//             String url = "https://testnet.binance.vision/api/v3/order";

//             // Create the POST request with the query string as the body
//             HttpRequest request = HttpRequest.newBuilder()
//                 .uri(URI.create(url))
//                 .timeout(Duration.ofSeconds(30))
//                 .header("X-MBX-APIKEY", apiKey)
//                 .header("Content-Type", "application/x-www-form-urlencoded")
//                 .POST(HttpRequest.BodyPublishers.ofString(queryString + "&signature=" + signature.toString()))
//                 .build();

//             HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

//             if (response.statusCode() == 200) {
//                 System.out.println("✅ ORDER PLACED SUCCESSFULLY: " + response.body());
//                 // --- SAVE POSITION TO DATABASE ---
//                 if ("BUY".equals(side)) {
//                     // Parse the response to extract the executed price
//                     JSONObject responseJson = new JSONObject(response.body());
//                     JSONArray fills = responseJson.getJSONArray("fills");
//                     BigDecimal totalCost = BigDecimal.ZERO;
//                     BigDecimal totalQuantity = BigDecimal.ZERO;

//                     for (int i = 0; i < fills.length(); i++) {
//                         JSONObject fill = fills.getJSONObject(i);
//                         totalCost = totalCost.add(new BigDecimal(fill.getString("price")).multiply(new BigDecimal(fill.getString("qty"))));
//                         totalQuantity = totalQuantity.add(new BigDecimal(fill.getString("qty")));
//                     }
                        
//                     BigDecimal averageEntryPrice = totalCost.divide(totalQuantity, 8, BigDecimal.ROUND_HALF_UP);
//                     System.out.println("Calculated Average Entry Price: " + averageEntryPrice);

//                     Position position = new Position();
//                     String asset = symbol.split("/")[0];
//                     position.setUserId(bot.getUserId());
//                     position.setBotId(bot.getId());
//                     position.setAsset(asset);
//                     position.setSymbol(symbol);
//                     position.setQuantity(quantity);
//                     position.setEntryPrice(averageEntryPrice);
//                     position.setStatus(PositionStatus.OPEN);
//                     position.setOpenedAt(LocalDateTime.now());
//                     positionRepository.save(position);
//                     System.out.println("✅ POSITION OPENED and saved to database.");
//                 }  else if ("SELL".equals(side)) {
//                     if (openPositionOpt.isPresent()) {
//                         Position positionToClose = openPositionOpt.get();
//                         positionToClose.setStatus(PositionStatus.CLOSED);
//                         positionToClose.setClosedAt(LocalDateTime.now());
//                         positionRepository.save(positionToClose);
//                         System.out.println("✅ POSITION CLOSED and updated in database.");
//                     } else {
//                         System.err.println("⚠️ ORDER EXECUTION WARNING: Received a successful SELL but could not find an open position to close.");
//                     } 
//                 }
//             } else {
//                 System.err.println("❌ ORDER PLACEMENT FAILED: " + response.statusCode());
//                 System.err.println("   Response: " + response.body());
//             }

//         } catch (Exception e) {
//             System.err.println("🔥 FATAL ERROR placing order: " + e.getMessage());
//             e.printStackTrace();
//         }
//     }
// }

// package com.alphintra.trading_engine.service;

// import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
// import com.alphintra.trading_engine.model.Position;
// import com.alphintra.trading_engine.model.PositionStatus;
// import com.alphintra.trading_engine.model.TradeOrder;
// import com.alphintra.trading_engine.model.TradingBot;
// import com.alphintra.trading_engine.repository.PositionRepository;
// import com.alphintra.trading_engine.repository.TradeOrderRepository;
// import lombok.RequiredArgsConstructor;
// import org.json.JSONArray;
// import org.json.JSONObject;
// import org.springframework.stereotype.Service;
// import org.springframework.transaction.annotation.Transactional;

// import javax.crypto.Mac;
// import javax.crypto.spec.SecretKeySpec;
// import java.math.BigDecimal;
// import java.math.RoundingMode;
// import java.net.URI;
// import java.net.http.HttpClient;
// import java.net.http.HttpRequest;
// import java.net.http.HttpResponse;
// import java.nio.charset.StandardCharsets;
// import java.time.Duration;
// import java.time.LocalDateTime;
// import java.util.Optional;

// @Service
// @RequiredArgsConstructor
// public class OrderExecutionService {

//     private final PositionRepository positionRepository;
//     private final TradeOrderRepository tradeOrderRepository;
//     private final HttpClient httpClient = HttpClient.newBuilder()
//             .connectTimeout(Duration.ofSeconds(10))
//             .build();

//     // @Transactional
//     public void placeMarketOrder(TradingBot bot, WalletCredentialsDTO credentials, String symbol, String side, BigDecimal quantity, Optional<Position> openPositionOpt) {
//         System.out.println("EXECUTING ORDER: " + side + " " + quantity + " " + symbol);

//         try {
//             String apiKey = credentials.apiKey();
//             String secretKey = credentials.secretKey();
//             String apiSymbol = symbol.replace("/", "");
//             long timestamp = System.currentTimeMillis();
//             String queryString = "symbol=" + apiSymbol + "&side=" + side + "&type=MARKET" + "&quantity=" + quantity.toPlainString() + "&timestamp=" + timestamp;

//             Mac mac = Mac.getInstance("HmacSHA256");
//             SecretKeySpec secretKeySpec = new SecretKeySpec(secretKey.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
//             mac.init(secretKeySpec);
//             byte[] hash = mac.doFinal(queryString.getBytes(StandardCharsets.UTF_8));
//             StringBuilder signature = new StringBuilder();
//             for (byte b : hash) {
//                 signature.append(String.format("%02x", b));
//             }

//             String url = "https://testnet.binance.vision/api/v3/order";
//             HttpRequest request = HttpRequest.newBuilder()
//                     .uri(URI.create(url))
//                     .timeout(Duration.ofSeconds(30))
//                     .header("X-MBX-APIKEY", apiKey)
//                     .header("Content-Type", "application/x-www-form-urlencoded")
//                     .POST(HttpRequest.BodyPublishers.ofString(queryString + "&signature=" + signature.toString()))
//                     .build();

//             HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

//             if (response.statusCode() == 200) {
//                 System.out.println("✅ ORDER PLACED SUCCESSFULLY: " + response.body());
//                 JSONObject responseJson = new JSONObject(response.body());

//                 // --- 1. CREATE THE HISTORICAL TRADE ORDER RECORD (MATCHING YOUR SCHEMA) ---
//                 TradeOrder tradeOrder = new TradeOrder();
//                 tradeOrder.setBotId(bot.getId());
//                 tradeOrder.setExchangeOrderId(String.valueOf(responseJson.getLong("orderId")));
//                 tradeOrder.setSymbol(symbol);
//                 tradeOrder.setType(responseJson.getString("type")); // "MARKET"
//                 tradeOrder.setSide(side);
//                 tradeOrder.setStatus(responseJson.getString("status")); // "FILLED"
//                 tradeOrder.setAmount(new BigDecimal(responseJson.getString("executedQty"))); // Use 'amount'
//                 tradeOrder.setCreatedAt(LocalDateTime.now()); // Use 'createdAt'

//                 BigDecimal averagePrice = calculateAveragePrice(responseJson);
//                 tradeOrder.setPrice(averagePrice);

//                 tradeOrderRepository.save(tradeOrder);
//                 System.out.println("✅ HISTORICAL TRADE ORDER saved to database.");

//                 // --- 2. MANAGE THE CURRENT POSITION STATE ---
//                 if ("BUY".equals(side)) {
//                     Position position = new Position();
//                     String asset = symbol.split("/")[0];
//                     position.setUserId(bot.getUserId());
//                     position.setBotId(bot.getId());
//                     position.setAsset(asset);
//                     position.setSymbol(symbol);
//                     position.setQuantity(tradeOrder.getAmount()); // Use 'amount' from the confirmed trade
//                     position.setEntryPrice(averagePrice);
//                     position.setStatus(PositionStatus.OPEN);
//                     position.setOpenedAt(LocalDateTime.now());
//                     positionRepository.save(position);
//                     System.out.println("✅ POSITION OPENED and saved to database.");
//                 } else if ("SELL".equals(side)) {
//                     if (openPositionOpt.isPresent()) {
//                         Position positionToClose = openPositionOpt.get();
//                         positionToClose.setStatus(PositionStatus.CLOSED);
//                         positionToClose.setClosedAt(LocalDateTime.now());
//                         positionRepository.save(positionToClose);
//                         System.out.println("✅ POSITION CLOSED and updated in database.");
//                     } else {
//                         System.err.println("⚠️ ORDER EXECUTION WARNING: SELL successful but no open position found to close.");
//                     }
//                 }
//             } else {
//                 System.err.println("❌ ORDER PLACEMENT FAILED: " + response.statusCode());
//                 System.err.println("   Response: " + response.body());
//             }

//         } catch (Exception e) {
//             System.err.println("🔥 FATAL ERROR placing order: " + e.getMessage());
//             e.printStackTrace();
//         }
//     }

//     private BigDecimal calculateAveragePrice(JSONObject responseJson) {
//         JSONArray fills = responseJson.getJSONArray("fills");
//         if (fills.isEmpty()) return BigDecimal.ZERO;

//         BigDecimal totalCost = BigDecimal.ZERO;
//         BigDecimal totalQuantity = BigDecimal.ZERO;

//         for (int i = 0; i < fills.length(); i++) {
//             JSONObject fill = fills.getJSONObject(i);
//             BigDecimal price = new BigDecimal(fill.getString("price"));
//             BigDecimal qty = new BigDecimal(fill.getString("qty"));
//             totalCost = totalCost.add(price.multiply(qty));
//             totalQuantity = totalQuantity.add(qty);
//         }

//         if (totalQuantity.compareTo(BigDecimal.ZERO) == 0) return BigDecimal.ZERO;

//         return totalCost.divide(totalQuantity, 8, RoundingMode.HALF_UP);
//     }
// }


package com.alphintra.trading_engine.service;

import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
import com.alphintra.trading_engine.model.Position;
import com.alphintra.trading_engine.model.PositionStatus;
import com.alphintra.trading_engine.model.TradeOrder;
import com.alphintra.trading_engine.model.TradingBot;
import com.alphintra.trading_engine.repository.PositionRepository;
import com.alphintra.trading_engine.repository.TradeOrderRepository;
import lombok.RequiredArgsConstructor;
import org.json.JSONArray;
import org.json.JSONObject;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.LocalDateTime;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class OrderExecutionService {

    private final PositionRepository positionRepository;
    private final TradeOrderRepository tradeOrderRepository;
    private final BinanceTimeService binanceTimeService; // <-- INJECT THE TIME SERVICE
    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();

    @Transactional
    public void placeMarketOrder(TradingBot bot, WalletCredentialsDTO credentials, String symbol, String side, BigDecimal quantity, Optional<Position> openPositionOpt) {
        System.out.println("EXECUTING ORDER: " + side + " " + quantity + " " + symbol);
        try {
            String apiKey = credentials.apiKey();
            String secretKey = credentials.secretKey();
            
            // --- FIX IS HERE: Use synchronized server time ---
            long timestamp = binanceTimeService.getServerTime();
            
            String apiSymbol = symbol.replace("/", "");

            // --- FIX IS HERE: The timestamp must be part of the signed query string ---
            String queryString = "symbol=" + apiSymbol +
                                 "&side=" + side +
                                 "&type=MARKET" +
                                 "&quantity=" + quantity.toPlainString() +
                                 "&timestamp=" + timestamp;

            Mac mac = Mac.getInstance("HmacSHA256");
            SecretKeySpec secretKeySpec = new SecretKeySpec(secretKey.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
            mac.init(secretKeySpec);
            byte[] hash = mac.doFinal(queryString.getBytes(StandardCharsets.UTF_8));
            StringBuilder signature = new StringBuilder();
            for (byte b : hash) {
                signature.append(String.format("%02x", b));
            }

            String url = "https://testnet.binance.vision/api/v3/order";
            // The signature is appended at the end, but the signed string does not include the signature itself
            String requestBody = queryString + "&signature=" + signature.toString();

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .timeout(Duration.ofSeconds(30))
                    .header("X-MBX-APIKEY", apiKey)
                    .header("Content-Type", "application/x-www-form-urlencoded")
                    .POST(HttpRequest.BodyPublishers.ofString(requestBody))
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() == 200) {
                System.out.println("✅ ORDER PLACED SUCCESSFULLY: " + response.body());
                JSONObject responseJson = new JSONObject(response.body());

                // Create the historical trade record
                TradeOrder tradeOrder = new TradeOrder();
                tradeOrder.setBotId(bot.getId());
                tradeOrder.setExchangeOrderId(String.valueOf(responseJson.getLong("orderId")));
                tradeOrder.setSymbol(symbol);
                tradeOrder.setType(responseJson.getString("type"));
                tradeOrder.setSide(side);
                tradeOrder.setStatus(responseJson.getString("status"));
                tradeOrder.setAmount(new BigDecimal(responseJson.getString("executedQty")));
                tradeOrder.setCreatedAt(LocalDateTime.now());
                BigDecimal averagePrice = calculateAveragePrice(responseJson);
                tradeOrder.setPrice(averagePrice);
                tradeOrderRepository.save(tradeOrder);
                System.out.println("✅ HISTORICAL TRADE ORDER saved to database.");

                // Manage the current position state
                if ("BUY".equals(side)) {
                    Position position = positionRepository.findFirstByUserIdAndSymbol(bot.getUserId(), symbol)
                            .orElse(new Position());
                    String asset = symbol.split("/")[0];
                    position.setUserId(bot.getUserId());
                    position.setBotId(bot.getId());
                    position.setAsset(asset);
                    position.setSymbol(symbol);
                    position.setQuantity(tradeOrder.getAmount());
                    position.setEntryPrice(averagePrice);
                    position.setStatus(PositionStatus.OPEN);
                    position.setOpenedAt(LocalDateTime.now());
                    position.setClosedAt(null);

                    positionRepository.save(position);
                    System.out.println("✅ POSITION OPENED and saved to database.");
                } else if ("SELL".equals(side)) {
                    openPositionOpt.ifPresent(positionToClose -> {
                        positionToClose.setStatus(PositionStatus.CLOSED);
                        positionToClose.setClosedAt(LocalDateTime.now());
                        positionRepository.save(positionToClose);
                        System.out.println("✅ POSITION CLOSED and updated in database.");
                    });
                }
            } else {
                System.err.println("❌ ORDER PLACEMENT FAILED: " + response.statusCode() + " | Response: " + response.body());
            }

        } catch (Exception e) {
            System.err.println("🔥 FATAL ERROR placing order: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private BigDecimal calculateAveragePrice(JSONObject responseJson) {
        JSONArray fills = responseJson.getJSONArray("fills");
        if (fills.isEmpty()) return BigDecimal.ZERO;
        BigDecimal totalCost = BigDecimal.ZERO;
        BigDecimal totalQuantity = BigDecimal.ZERO;
        for (int i = 0; i < fills.length(); i++) {
            JSONObject fill = fills.getJSONObject(i);
            BigDecimal price = new BigDecimal(fill.getString("price"));
            BigDecimal qty = new BigDecimal(fill.getString("qty"));
            totalCost = totalCost.add(price.multiply(qty));
            totalQuantity = totalQuantity.add(qty);
        }
        if (totalQuantity.compareTo(BigDecimal.ZERO) == 0) return BigDecimal.ZERO;
        return totalCost.divide(totalQuantity, 8, RoundingMode.HALF_UP);
    }
}

