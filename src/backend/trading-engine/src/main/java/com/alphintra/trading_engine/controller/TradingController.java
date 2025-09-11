package com.alphintra.trading_engine.controller;

import com.alphintra.trading_engine.dto.StartBotRequest;
import com.alphintra.trading_engine.model.TradingBot;
import com.alphintra.trading_engine.service.TradingService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/trading") // Base path for all endpoints in this class
@RequiredArgsConstructor
public class TradingController {

    private final TradingService tradingService;

    @PostMapping("/bot/start") // Handles POST requests to /api/trading/bot/start
    public ResponseEntity<TradingBot> startBot(@RequestBody StartBotRequest request) {
        System.out.println("Received request to start bot for user: " + request.userId());
        TradingBot startedBot = tradingService.startBot(request.userId(), request.strategyId());
        return ResponseEntity.ok(startedBot);
    }
}