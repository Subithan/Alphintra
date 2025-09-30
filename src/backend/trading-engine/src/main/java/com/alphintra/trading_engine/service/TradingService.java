package com.alphintra.trading_engine.service;

import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
import com.alphintra.trading_engine.model.BotStatus;
import com.alphintra.trading_engine.model.TradingBot;
import com.alphintra.trading_engine.repository.TradingBotRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class TradingService {

    private final TradingBotRepository botRepository;
    private final TradingTaskService tradingTaskService;

    public TradingBot startBot(Long userId, Long strategyId) {
        System.out.println("TradingService: startBot method called for userId=" + userId + ", strategyId=" + strategyId);

        System.out.println("🔧 Using Binance TESTNET API credentials for testing.");
        WalletCredentialsDTO credentials = new WalletCredentialsDTO(
            "HCwZWzdNFNVj6jYlunDyqh1tFScpTnxktaPLGDkZDaorhhQRoq5LGFReqQYN8Fbi",
            "1hbOBVTw20W1tOFSdXgn1VZBtQ8DWzrwC4w5p4CnfUDnGH5aRyhP7Ys6KOFuDzoq"
        );

        TradingBot bot = new TradingBot();
        bot.setUserId(userId);
        bot.setStrategyId(strategyId);
        bot.setStatus(BotStatus.RUNNING);
        bot.setSymbol("ETC/USDT");
        bot.setStartedAt(LocalDateTime.now());
        TradingBot savedBot = botRepository.save(bot);

        // Call the async method on the new service instance
        tradingTaskService.runTradingLoop(savedBot, credentials);
        
        return savedBot;
    }

    public List<TradingBot> stopBots() {
        List<TradingBot> runningBots = botRepository.findByStatus(BotStatus.RUNNING);
        if (runningBots.isEmpty()) {
            System.out.println("--> No running bots found to stop.");
            return List.of();
        }
        System.out.println("--> Found " + runningBots.size() + " running bots. Setting status to STOPPED.");
        for (TradingBot bot : runningBots) {
            bot.setStatus(BotStatus.STOPPED);
            bot.setStoppedAt(LocalDateTime.now());
        }
        return botRepository.saveAll(runningBots);
    }
}