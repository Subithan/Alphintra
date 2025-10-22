package com.alphintra.trading_engine.controller;

import com.alphintra.trading_engine.dto.BalanceInfoResponse;
import com.alphintra.trading_engine.dto.StartBotRequest;
import com.alphintra.trading_engine.dto.TradeOrderDTO;
import com.alphintra.trading_engine.model.Position;
import com.alphintra.trading_engine.model.PositionStatus;
import com.alphintra.trading_engine.model.TradeOrder;
import com.alphintra.trading_engine.model.TradingBot;
import com.alphintra.trading_engine.model.UserBalance;
import com.alphintra.trading_engine.repository.PositionRepository;
import com.alphintra.trading_engine.repository.TradeOrderRepository;
import com.alphintra.trading_engine.repository.UserBalanceRepository;
import com.alphintra.trading_engine.service.TradeHistoryService;
import com.alphintra.trading_engine.service.TradingService;
import lombok.RequiredArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/trading") 
@RequiredArgsConstructor
public class TradingController {

    private final TradingService tradingService;
    private final TradeHistoryService tradeHistoryService;
    private final PositionRepository positionRepository;
    private final TradeOrderRepository tradeOrderRepository;
    private final UserBalanceRepository userBalanceRepository;

    @Value("${trading.mock.enabled:false}")
    private boolean mockEnabled;

    @PostMapping("/bot/start") 
    public ResponseEntity<Map<String, Object>> startBot(@RequestBody StartBotRequest request) {
        Integer capitalAllocation = request.capitalAllocation() != null ? request.capitalAllocation() : 100;
        String symbol = request.symbol() != null ? request.symbol() : "ETC/USDT";
        
        System.out.println("🚀 Received request to start bot for user: " + request.userId() + 
                         ", symbol: " + symbol +
                         ", capital allocation: " + capitalAllocation + "%");
        
        // Start the bot
        TradingBot startedBot = tradingService.startBot(
            request.userId(), 
            request.strategyId(), 
            capitalAllocation, 
            symbol
        );
        
        // If mock mode is enabled, create a mock open position
        Position mockPosition = null;
        TradeOrder mockOrder = null;
        
        if (mockEnabled) {
            System.out.println("🎭 MOCK MODE: Creating mock open position for bot " + startedBot.getId());
            
            // Create mock trade order (BUY)
            mockOrder = new TradeOrder();
            mockOrder.setBotId(startedBot.getId());
            mockOrder.setExchangeOrderId("MOCK-" + System.currentTimeMillis());
            mockOrder.setSymbol(symbol);
            mockOrder.setType("MARKET");
            mockOrder.setSide("BUY");
            mockOrder.setStatus("FILLED");
            
            // Mock entry price based on symbol
            BigDecimal mockEntryPrice = getMockPrice(symbol);
            mockOrder.setPrice(mockEntryPrice);
            
            // Mock quantity based on capital allocation
            BigDecimal mockQuantity = calculateMockQuantity(symbol, capitalAllocation, mockEntryPrice);
            mockOrder.setAmount(mockQuantity);
            mockOrder.setCreatedAt(LocalDateTime.now());
            
            mockOrder = tradeOrderRepository.save(mockOrder);
            System.out.println("✅ Mock trade order created: " + mockOrder.getExchangeOrderId());
            
            // Find or create mock open position (handles unique constraint on user_id + asset)
            mockPosition = positionRepository.findFirstByUserIdAndSymbol(request.userId(), symbol)
                    .orElse(new Position());
            
            String asset = symbol.split("/")[0]; // Extract base asset (e.g., "ETC" from "ETC/USDT")
            mockPosition.setBotId(startedBot.getId());
            mockPosition.setUserId(request.userId());
            mockPosition.setSymbol(symbol);
            mockPosition.setAsset(asset);
            mockPosition.setQuantity(mockQuantity);
            mockPosition.setEntryPrice(mockEntryPrice);
            mockPosition.setStatus(PositionStatus.OPEN);
            mockPosition.setOpenedAt(LocalDateTime.now());
            mockPosition.setClosedAt(null); // Ensure closed_at is null for open positions
            
            mockPosition = positionRepository.save(mockPosition);
            System.out.println("✅ Mock open position created/updated: ID=" + mockPosition.getId() + 
                             ", Qty=" + mockQuantity + ", Entry=" + mockEntryPrice);
        }
        
        // Return comprehensive response
        Map<String, Object> response = Map.of(
            "bot", startedBot,
            "mockMode", mockEnabled,
            "position", mockPosition != null ? mockPosition : "No position created (real mode)",
            "order", mockOrder != null ? mockOrder : "No order created (real mode)"
        );
        
        return ResponseEntity.ok(response);
    }

    @PostMapping("/bots/stop") 
    public ResponseEntity<String> stopAllBots() {
        List<TradingBot> stoppedBots = tradingService.stopBots();
        return ResponseEntity.ok("Stop request processed. " + stoppedBots.size() + " bots were stopped.");
    }

    @GetMapping("/trades")
    public ResponseEntity<List<TradeOrderDTO>> getTradeHistory(
            @RequestParam(name = "limit", required = false) Integer limit,
            @RequestHeader(value = "X-User-Id", required = false) String userId) {
        
        // If userId is provided from gateway (authenticated request), filter by user
        if (userId != null && !userId.isEmpty()) {
            List<TradeOrderDTO> trades = (limit == null) 
                ? tradeHistoryService.getTradesByUser(userId) 
                : tradeHistoryService.getTradesByUser(userId, limit);
            return ResponseEntity.ok(trades);
        }
        
        // Fallback to all trades (for backward compatibility)
        List<TradeOrderDTO> trades = (limit == null) 
            ? tradeHistoryService.getRecentTrades() 
            : tradeHistoryService.getRecentTrades(limit);
        return ResponseEntity.ok(trades);
    }

    @GetMapping("/balance")
    public ResponseEntity<BalanceInfoResponse> getUsdtBalance(
            @RequestHeader(value = "X-User-Id", required = false) String userId) {
        if (userId == null || userId.isBlank()) {
            System.out.println("⚠️ No X-User-Id header provided for /balance request");
            return ResponseEntity.badRequest().build();
        }

        Long userIdLong = Long.parseLong(userId);
        System.out.println("📊 Fetching Coinbase balances for user: " + userIdLong);
        BalanceInfoResponse balance = tradingService.getBalanceInfo(userIdLong);
        return ResponseEntity.ok(balance);
    }

    @GetMapping("/bots")
    public ResponseEntity<List<TradingBot>> getBots(@RequestHeader(value = "X-User-Id", required = false) String userId) {
        System.out.println("🤖 Fetching bots for user: " + userId);
        
        if (userId == null || userId.isEmpty()) {
            return ResponseEntity.badRequest().build();
        }
        
        Long userIdLong = Long.parseLong(userId);
        List<TradingBot> bots = tradingService.getBotsByUser(userIdLong);
        return ResponseEntity.ok(bots);
    }

    @GetMapping("/positions")
    public ResponseEntity<List<Position>> getPositions(@RequestHeader(value = "X-User-Id", required = false) String userId) {
        System.out.println("📊 Fetching positions for user: " + userId);
        
        if (userId == null || userId.isEmpty()) {
            return ResponseEntity.badRequest().build();
        }
        
        Long userIdLong = Long.parseLong(userId);
        List<Position> positions = positionRepository.findByUserId(userIdLong);
        return ResponseEntity.ok(positions);
    }

    // Helper method to get mock prices
    private BigDecimal getMockPrice(String symbol) {
        Map<String, BigDecimal> mockPrices = Map.of(
            "BTC/USDT", new BigDecimal("110814.01"),
            "ETH/USDT", new BigDecimal("4042.10"),
            "ETC/USDT", new BigDecimal("16.04"),
            "SOL/USDT", new BigDecimal("192.96"),
            "BNB/USDT", new BigDecimal("1120.59"),
            "XRP/USDT", new BigDecimal("2.47"),
            "ADA/USDT", new BigDecimal("0.67"),
            "DOGE/USDT", new BigDecimal("0.20")
        );
        return mockPrices.getOrDefault(symbol, new BigDecimal("100.00"));
    }

    // Helper method to calculate mock quantity
    private BigDecimal calculateMockQuantity(String symbol, int capitalAllocation, BigDecimal price) {
        // Assume 10,000 USDT available balance
        BigDecimal totalBalance = new BigDecimal("10000.00");
        BigDecimal allocatedAmount = totalBalance
            .multiply(new BigDecimal(capitalAllocation))
            .divide(new BigDecimal("100"), 2, java.math.RoundingMode.DOWN);
        
        BigDecimal quantity = allocatedAmount.divide(price, 8, java.math.RoundingMode.DOWN);
        
        // Adjust to step size
        Map<String, BigDecimal> stepSizes = Map.of(
            "BTC/USDT", new BigDecimal("0.00001"),
            "ETH/USDT", new BigDecimal("0.0001"),
            "ETC/USDT", new BigDecimal("0.01"),
            "SOL/USDT", new BigDecimal("0.01"),
            "BNB/USDT", new BigDecimal("0.001")
        );
        
        BigDecimal stepSize = stepSizes.getOrDefault(symbol, new BigDecimal("0.01"));
        return quantity.divide(stepSize, 0, java.math.RoundingMode.DOWN)
                      .multiply(stepSize);
    }

    @GetMapping("/user/balances")
    public ResponseEntity<List<UserBalance>> getUserBalances(
            @RequestHeader(value = "X-User-Id", required = false) String userId) {
        
        if (userId == null || userId.isEmpty()) {
            System.out.println("⚠️ No X-User-Id header provided for /user/balances");
            return ResponseEntity.badRequest().build();
        }
        
        System.out.println("💰 Fetching balances for user: " + userId);
        Long userIdLong = Long.parseLong(userId);
        List<UserBalance> balances = userBalanceRepository.findByUserId(userIdLong);
        
        System.out.println("✅ Found " + balances.size() + " balances for user " + userId);
        return ResponseEntity.ok(balances);
    }
}