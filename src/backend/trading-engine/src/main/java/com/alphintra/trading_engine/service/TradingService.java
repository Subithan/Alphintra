package com.alphintra.trading_engine.service;

import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
import com.alphintra.trading_engine.model.BotStatus;
import com.alphintra.trading_engine.model.TradingBot;
import com.alphintra.trading_engine.repository.TradingBotRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class TradingService {

    private final TradingBotRepository botRepository;
    private final TradingTaskService tradingTaskService;

    public TradingBot startBot(Long userId, Long strategyId, String symbol, BigDecimal capitalAllocationPercentage) {
        System.out.println("TradingService: startBot method called");
        System.out.println("   User ID: " + userId);
        System.out.println("   Strategy ID: " + strategyId);
        System.out.println("   Symbol: " + symbol);
        System.out.println("   Capital Allocation: " + capitalAllocationPercentage + "%");

        // Use defaults if not provided
        Long actualStrategyId = (strategyId != null) ? strategyId : 1L;
        String tradingSymbol = (symbol != null && !symbol.isEmpty()) ? symbol : "ETC/FDUSD";
        BigDecimal allocation = (capitalAllocationPercentage != null) ? capitalAllocationPercentage : new BigDecimal("90");

        System.out.println("🔧 Using Binance TESTNET API credentials for testing.");
        WalletCredentialsDTO credentials = new WalletCredentialsDTO(
            "HCwZWzdNFNVj6jYlunDyqh1tFScpTnxktaPLGDkZDaorhhQRoq5LGFReqQYN8Fbi",
            "1hbOBVTw20W1tOFSdXgn1VZBtQ8DWzrwC4w5p4CnfUDnGH5aRyhP7Ys6KOFuDzoq"
        );

        TradingBot bot = new TradingBot();
        bot.setUserId(userId);
        bot.setStrategyId(actualStrategyId);
        bot.setStatus(BotStatus.RUNNING);
        bot.setSymbol(tradingSymbol);
        bot.setCapitalAllocationPercentage(allocation);
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