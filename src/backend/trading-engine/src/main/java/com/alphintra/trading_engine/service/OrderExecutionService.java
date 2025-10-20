

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
    private final BinanceTimeService binanceTimeService;
    private final PendingOrderService pendingOrderService; // <-- ADD THIS
    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();
    
    // Mock mode for testing without valid API keys
    private static final boolean MOCK_MODE = Boolean.parseBoolean(System.getenv().getOrDefault("MOCK_TRADING_MODE", "false"));

    @Transactional
    public void placeMarketOrder(TradingBot bot, WalletCredentialsDTO credentials, String symbol, String side, BigDecimal quantity, Optional<Position> openPositionOpt) {
        placeMarketOrder(bot, credentials, symbol, side, quantity, openPositionOpt, null, null);
    }

    @Transactional
    public void placeMarketOrder(TradingBot bot, WalletCredentialsDTO credentials, String symbol, String side, BigDecimal quantity, Optional<Position> openPositionOpt, String exitReason, Long pendingOrderId) {
        System.out.println("EXECUTING ORDER: " + side + " " + quantity + " " + symbol);
        
        // MOCK MODE: Simulate order execution without calling Binance API
        if (MOCK_MODE) {
            System.out.println("🧪 MOCK MODE: Simulating order execution...");
            handleMockOrder(bot, symbol, side, quantity, openPositionOpt, exitReason, pendingOrderId);
            return;
        }
        
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
                tradeOrder.setExitReason(exitReason); // <-- ADD exit reason (TAKE_PROFIT / STOP_LOSS / MANUAL)
                tradeOrder.setPendingOrderId(pendingOrderId); // <-- ADD pending order reference
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

                    Position savedPosition = positionRepository.save(position);
                    System.out.println("✅ POSITION OPENED and saved to database.");

                    // Create pending orders (take-profit and stop-loss)
                    pendingOrderService.createPendingOrdersForPosition(savedPosition, averagePrice);

                } else if ("SELL".equals(side)) {
                    openPositionOpt.ifPresent(positionToClose -> {
                        positionToClose.setStatus(PositionStatus.CLOSED);
                        positionToClose.setClosedAt(LocalDateTime.now());
                        positionRepository.save(positionToClose);
                        System.out.println("✅ POSITION CLOSED and updated in database." + 
                                         (exitReason != null ? " Reason: " + exitReason : ""));
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
    
    /**
     * Mock order execution for testing without Binance API
     */
    private void handleMockOrder(TradingBot bot, String symbol, String side, BigDecimal quantity, Optional<Position> openPositionOpt, String exitReason, Long pendingOrderId) {
        // Simulate market price
        BigDecimal mockPrice = new BigDecimal("16.20"); // Mock ETC price
        
        System.out.println("✅ MOCK ORDER EXECUTED: " + side + " " + quantity + " " + symbol + " @ " + mockPrice);
        
        // Save trade order record
        TradeOrder order = new TradeOrder();
        order.setBotId(bot.getId());
        order.setSymbol(symbol);
        order.setType("MARKET");
        order.setSide(side);
        order.setPrice(mockPrice);
        order.setAmount(quantity);
        order.setStatus("FILLED");
        order.setExitReason(exitReason);
        order.setPendingOrderId(pendingOrderId);
        order.setCreatedAt(LocalDateTime.now());
        tradeOrderRepository.save(order);
        
        if ("BUY".equals(side)) {
            // Create a new position
            String asset = symbol.split("/")[0];
            Position position = new Position();
            position.setUserId(bot.getUserId());
            position.setBotId(bot.getId());
            position.setSymbol(symbol);
            position.setAsset(asset);
            position.setQuantity(quantity);
            position.setEntryPrice(mockPrice);
            position.setStatus(PositionStatus.OPEN);
            position.setOpenedAt(LocalDateTime.now());
            Position savedPosition = positionRepository.save(position);
            
            System.out.println("📊 MOCK POSITION CREATED: ID=" + savedPosition.getId() + ", Entry=" + mockPrice + ", Qty=" + quantity);
            
            // Create pending orders (take-profit and stop-loss)
            pendingOrderService.createPendingOrdersForPosition(savedPosition, mockPrice);
            System.out.println("✅ MOCK PENDING ORDERS CREATED for position " + savedPosition.getId());
            
        } else if ("SELL".equals(side) && openPositionOpt.isPresent()) {
            // Close the position
            Position position = openPositionOpt.get();
            position.setStatus(PositionStatus.CLOSED);
            position.setClosedAt(LocalDateTime.now());
            positionRepository.save(position);
            
            // Mark pending orders as triggered if this was from a pending order
            if (pendingOrderId != null) {
                // The pending order service will handle marking it as triggered
                System.out.println("📋 Pending order " + pendingOrderId + " was triggered");
            }
            
            BigDecimal profitLoss = mockPrice.subtract(position.getEntryPrice()).multiply(quantity);
            System.out.println("💰 MOCK POSITION CLOSED: P/L=" + profitLoss + " " + (exitReason != null ? ("(" + exitReason + ")") : ""));
        }
    }
}

