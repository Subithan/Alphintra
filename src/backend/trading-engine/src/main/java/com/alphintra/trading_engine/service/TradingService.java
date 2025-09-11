package com.alphintra.trading_engine.service;

import com.alphintra.trading_engine.client.WalletServiceClient;
import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
import com.alphintra.trading_engine.model.BotStatus;
import com.alphintra.trading_engine.model.TradingBot;
import com.alphintra.trading_engine.repository.TradingBotRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import java.time.LocalDateTime;
import org.knowm.xchange.Exchange;
import org.knowm.xchange.ExchangeFactory;
import org.knowm.xchange.binance.BinanceExchange;
import org.knowm.xchange.currency.CurrencyPair;
import org.knowm.xchange.service.marketdata.MarketDataService;
import org.knowm.xchange.service.trade.TradeService;
import org.knowm.xchange.dto.marketdata.Ticker;
import org.knowm.xchange.exceptions.ExchangeException;

@Service
@RequiredArgsConstructor
public class TradingService {

    private final TradingBotRepository botRepository;
    private final WalletServiceClient walletServiceClient; // Dependency is now injected

    public TradingBot startBot(Long userId, Long strategyId) {
        System.out.println("TradingService: startBot method called for userId=" + userId + ", strategyId=" + strategyId);

        // STEP 1: Call the WalletServiceClient to get the credentials
        System.out.println("--> Now calling WalletServiceClient...");
        WalletCredentialsDTO credentials = walletServiceClient.getCredentials(userId);
        System.out.println("--> Credentials received` successfully from Wallet Service!");

        // STEP 2: Create and save the bot entity to the database
        TradingBot bot = new TradingBot();
        bot.setUserId(userId);
        bot.setStrategyId(strategyId);
        bot.setStatus(BotStatus.RUNNING);
        bot.setSymbol("ETC/USDT"); // Example symbol
        bot.setStartedAt(LocalDateTime.now());
        TradingBot savedBot = botRepository.save(bot);

        // STEP 3: Start the actual trading loop in a background thread
        runTradingLoop(savedBot, credentials);
        
        return savedBot;
    }

    /**
     * This method runs in a separate background thread because of the @Async annotation.
     * This is where the actual bot logic will live.
     */
    @Async
    public void runTradingLoop(TradingBot bot, WalletCredentialsDTO credentials) {
        System.out.println("🚀 Starting background trading loop for bot ID: " + bot.getId());

        try {
            // 1. CONNECT TO BINANCE
            Exchange binance = ExchangeFactory.INSTANCE.createExchange(BinanceExchange.class);
            binance.getExchangeSpecification().setApiKey(credentials.apiKey());
            binance.getExchangeSpecification().setSecretKey(credentials.secretKey());

            MarketDataService marketDataService = binance.getMarketDataService();
            TradeService tradeService = binance.getTradeService();

            // 2. PARSE THE SYMBOL (e.g., "BTC/USDT")
            String[] parts = bot.getSymbol().split("/");
            CurrencyPair pair = new CurrencyPair(parts[0], parts[1]);

            // 3. LOOP TO FETCH MARKET PRICE
            while (bot.getStatus() == BotStatus.RUNNING) {
                try {
                    Ticker ticker = marketDataService.getTicker(pair);

                    if (ticker != null) {
                        System.out.println("📈 " + bot.getSymbol() + " price = " + ticker.getLast());
                    } else {
                        System.err.println("⚠️ Failed to fetch ticker for " + bot.getSymbol());
                    }

                    Thread.sleep(5000); // wait 5 seconds before next fetch
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    System.err.println("⏹️ Trading loop interrupted for bot " + bot.getId());
                    break;
                } catch (Exception e) {
                    System.err.println("❌ Error fetching ticker: " + e.getMessage());
                }
            }

        } catch (Exception e) {
            System.err.println("🔥 FATAL ERROR in trading loop for bot " + bot.getId() + ": " + e.getMessage());
            bot.setStatus(BotStatus.ERROR);
            botRepository.save(bot);
        }
    }

}