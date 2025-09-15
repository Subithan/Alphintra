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

        System.out.println("⚠️ WARN: Using hardcoded API credentials for testing.");
        WalletCredentialsDTO credentials = new WalletCredentialsDTO(
            "t6w9HbuLwN7F1m9fQi8CDf9e8w33pwRnu5fL0P7YoiawhbY4Y26fe2jTlPJiuUuU",
            "Ar355LF9iLmcRRYxdJVgqg0a6yu5xcVcCvHRbrQ94fUOkipPa18CNclxKP5QfHB8"
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