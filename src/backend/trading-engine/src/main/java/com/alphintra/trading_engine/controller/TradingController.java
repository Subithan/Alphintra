package com.alphintra.trading_engine.controller;

import com.alphintra.trading_engine.dto.StartBotRequest;
import com.alphintra.trading_engine.dto.TradeOrderDTO;
import com.alphintra.trading_engine.model.TradingBot;
import com.alphintra.trading_engine.service.BalanceService;
import com.alphintra.trading_engine.service.TradeHistoryService;
import com.alphintra.trading_engine.service.TradingService;
import lombok.RequiredArgsConstructor;

import java.util.List;
import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/trading") 
@RequiredArgsConstructor
public class TradingController {

    private final TradingService tradingService;
    private final TradeHistoryService tradeHistoryService;
    private final BalanceService balanceService;

    @PostMapping("/bot/start") 
    public ResponseEntity<TradingBot> startBot(@RequestBody StartBotRequest request) {
        System.out.println("Received request to start bot for user: " + request.userId());
        TradingBot startedBot = tradingService.startBot(
            request.userId(), 
            request.strategyId(),
            request.symbol(),
            request.capitalAllocationPercentage()
        );
        return ResponseEntity.ok(startedBot);
    }

    @PostMapping("/bots/stop") 
    public ResponseEntity<String> stopAllBots() {
        List<TradingBot> stoppedBots = tradingService.stopBots();
        return ResponseEntity.ok("Stop request processed. " + stoppedBots.size() + " bots were stopped.");
    }

    @GetMapping("/trades")
    public ResponseEntity<List<TradeOrderDTO>> getTradeHistory(@RequestParam(name = "limit", required = false) Integer limit) {
        List<TradeOrderDTO> trades = (limit == null) ? tradeHistoryService.getRecentTrades() : tradeHistoryService.getRecentTrades(limit);
        return ResponseEntity.ok(trades);
    }

    @GetMapping("/balance")
    public ResponseEntity<Map<String, java.math.BigDecimal>> getBalance(@RequestParam Long userId) {
        Map<String, java.math.BigDecimal> balances = balanceService.getAccountBalance(userId);
        return ResponseEntity.ok(balances);
    }
}