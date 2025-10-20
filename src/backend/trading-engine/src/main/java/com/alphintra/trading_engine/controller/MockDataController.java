package com.alphintra.trading_engine.controller;

import com.alphintra.trading_engine.dto.*;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Mock data controller for UI testing
 * Provides realistic mock data for balance, positions, orders, metrics, and charts
 */
@RestController
@RequestMapping("/api/v1/mock")
@CrossOrigin(origins = "*")
public class MockDataController {

    private final Random random = new Random();

    /**
     * Get mock balance data
     * GET /api/v1/mock/balance
     */
    @GetMapping("/balance")
    public MockBalanceDTO getBalance() {
        BigDecimal totalBalance = new BigDecimal("10000.00");
        BigDecimal inOrders = new BigDecimal(String.format("%.2f", random.nextDouble() * 2000));
        BigDecimal available = totalBalance.subtract(inOrders);
        
        return new MockBalanceDTO(
            totalBalance,
            available,
            inOrders,
            "USDT"
        );
    }

    /**
     * Get mock active positions
     * GET /api/v1/mock/positions
     */
    @GetMapping("/positions")
    public List<MockPositionDTO> getPositions() {
        List<MockPositionDTO> positions = new ArrayList<>();
        
        // Position 1: Profitable BTC position
        positions.add(new MockPositionDTO(
            1L,
            "BTC/USDT",
            "LONG",
            new BigDecimal("42500.00"),
            new BigDecimal("43200.00"),
            new BigDecimal("0.5"),
            new BigDecimal("350.00"),
            new BigDecimal("1.65"),
            10,
            LocalDateTime.now().minusHours(5),
            "OPEN"
        ));
        
        // Position 2: Losing ETH position
        positions.add(new MockPositionDTO(
            2L,
            "ETH/USDT",
            "SHORT",
            new BigDecimal("2250.00"),
            new BigDecimal("2280.00"),
            new BigDecimal("5.0"),
            new BigDecimal("-150.00"),
            new BigDecimal("-1.33"),
            5,
            LocalDateTime.now().minusHours(2),
            "OPEN"
        ));
        
        // Position 3: Small ETC position
        positions.add(new MockPositionDTO(
            3L,
            "ETC/FDUSD",
            "LONG",
            new BigDecimal("18.50"),
            new BigDecimal("18.75"),
            new BigDecimal("100.0"),
            new BigDecimal("25.00"),
            new BigDecimal("1.35"),
            3,
            LocalDateTime.now().minusMinutes(45),
            "OPEN"
        ));
        
        return positions;
    }

    /**
     * Get mock pending orders
     * GET /api/v1/mock/orders
     */
    @GetMapping("/orders")
    public List<MockOrderDTO> getOrders() {
        List<MockOrderDTO> orders = new ArrayList<>();
        
        // Take profit order
        orders.add(new MockOrderDTO(
            101L,
            "BTC/USDT",
            "LIMIT",
            "SELL",
            new BigDecimal("44000.00"),
            new BigDecimal("0.5"),
            new BigDecimal("0.0"),
            "PENDING",
            LocalDateTime.now().minusHours(5)
        ));
        
        // Stop loss order
        orders.add(new MockOrderDTO(
            102L,
            "BTC/USDT",
            "STOP_LOSS",
            "SELL",
            new BigDecimal("42000.00"),
            new BigDecimal("0.5"),
            new BigDecimal("0.0"),
            "PENDING",
            LocalDateTime.now().minusHours(5)
        ));
        
        // ETH take profit
        orders.add(new MockOrderDTO(
            103L,
            "ETH/USDT",
            "LIMIT",
            "BUY",
            new BigDecimal("2200.00"),
            new BigDecimal("5.0"),
            new BigDecimal("0.0"),
            "PENDING",
            LocalDateTime.now().minusHours(2)
        ));
        
        return orders;
    }

    /**
     * Get mock performance metrics
     * GET /api/v1/mock/performance
     */
    @GetMapping("/performance")
    public MockPerformanceDTO getPerformance() {
        return new MockPerformanceDTO(
            new BigDecimal("1250.50"),      // totalPnl
            new BigDecimal("12.51"),        // totalPnlPercentage
            48,                              // totalTrades
            32,                              // winningTrades
            16,                              // losingTrades
            new BigDecimal("66.67"),        // winRate
            new BigDecimal("85.50"),        // avgProfit
            new BigDecimal("-42.25"),       // avgLoss
            new BigDecimal("2.02"),         // profitFactor
            new BigDecimal("1.85"),         // sharpeRatio
            new BigDecimal("8.5")           // maxDrawdown
        );
    }

    /**
     * Get mock risk metrics
     * GET /api/v1/mock/risk
     */
    @GetMapping("/risk")
    public MockRiskMetricsDTO getRiskMetrics() {
        BigDecimal portfolioValue = new BigDecimal("10000.00");
        BigDecimal exposure = new BigDecimal("2500.00");
        BigDecimal marginUsed = new BigDecimal("1200.00");
        
        return new MockRiskMetricsDTO(
            new BigDecimal("250.00"),       // currentRisk
            new BigDecimal("500.00"),       // maxRisk
            new BigDecimal("2.5"),          // riskPercentage
            portfolioValue,                  // portfolioValue
            exposure,                        // exposure
            new BigDecimal("5.0"),          // leverage
            marginUsed,                      // marginUsed
            portfolioValue.subtract(marginUsed), // marginAvailable
            "MODERATE"                       // riskLevel
        );
    }

    /**
     * Get mock chart data with trade markers
     * GET /api/v1/mock/chart?symbol=BTC/USDT&interval=1h
     */
    @GetMapping("/chart")
    public MockChartDataDTO getChartData(
            @RequestParam(defaultValue = "BTC/USDT") String symbol,
            @RequestParam(defaultValue = "1h") String interval) {
        
        List<MockChartDataDTO.CandleData> candles = new ArrayList<>();
        List<MockChartDataDTO.TradeMarker> trades = new ArrayList<>();
        
        // Generate 50 candles
        BigDecimal basePrice = new BigDecimal("42000.00");
        LocalDateTime time = LocalDateTime.now().minusHours(50);
        
        for (int i = 0; i < 50; i++) {
            BigDecimal open = basePrice.add(new BigDecimal(random.nextInt(1000) - 500));
            BigDecimal close = open.add(new BigDecimal(random.nextInt(400) - 200));
            BigDecimal high = open.max(close).add(new BigDecimal(random.nextInt(200)));
            BigDecimal low = open.min(close).subtract(new BigDecimal(random.nextInt(200)));
            BigDecimal volume = new BigDecimal(String.format("%.2f", random.nextDouble() * 100));
            
            candles.add(new MockChartDataDTO.CandleData(
                time.plusHours(i),
                open,
                high,
                low,
                close,
                volume
            ));
            
            basePrice = close;
        }
        
        // Add trade markers
        trades.add(new MockChartDataDTO.TradeMarker(
            LocalDateTime.now().minusHours(10),
            new BigDecimal("41800.00"),
            "ENTRY",
            "BUY"
        ));
        
        trades.add(new MockChartDataDTO.TradeMarker(
            LocalDateTime.now().minusHours(3),
            new BigDecimal("42900.00"),
            "EXIT",
            "SELL"
        ));
        
        trades.add(new MockChartDataDTO.TradeMarker(
            LocalDateTime.now().minusHours(5),
            new BigDecimal("42500.00"),
            "ENTRY",
            "BUY"
        ));
        
        return new MockChartDataDTO(symbol, interval, candles, trades);
    }

    /**
     * Get list of available strategies
     * GET /api/v1/mock/strategies
     */
    @GetMapping("/strategies")
    public List<StrategyOption> getStrategies() {
        return List.of(
            new StrategyOption(1L, "RSI Momentum", "Trades based on RSI indicators"),
            new StrategyOption(2L, "EMA Crossover", "Moving average crossover strategy"),
            new StrategyOption(3L, "Bollinger Bands", "Trades on band breakouts"),
            new StrategyOption(4L, "MACD Trend", "MACD histogram strategy"),
            new StrategyOption(5L, "Grid Trading", "Automated grid bot")
        );
    }
    
    record StrategyOption(Long id, String name, String description) {}

    /**
     * Get list of available trading pairs
     * GET /api/v1/mock/pairs
     */
    @GetMapping("/pairs")
    public List<TradingPairOption> getTradingPairs() {
        return List.of(
            new TradingPairOption("BTC/USDT", "Bitcoin", "42,500", "2.5"),
            new TradingPairOption("BTC/FDUSD", "Bitcoin", "42,480", "2.4"),
            new TradingPairOption("ETH/USDT", "Ethereum", "2,280", "3.2"),
            new TradingPairOption("ETH/FDUSD", "Ethereum", "2,275", "3.1"),
            new TradingPairOption("ETC/FDUSD", "Ethereum Classic", "18.75", "1.8"),
            new TradingPairOption("BNB/USDT", "Binance Coin", "315.20", "1.5")
        );
    }
    
    record TradingPairOption(String symbol, String name, String price, String change24h) {}
}
