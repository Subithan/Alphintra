package com.alphintra.trading_engine.service;

import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
import com.alphintra.trading_engine.model.BotStatus;
import com.alphintra.trading_engine.model.TradingBot;
import com.alphintra.trading_engine.repository.TradingBotRepository;
import lombok.RequiredArgsConstructor;
import org.knowm.xchange.Exchange;
import org.knowm.xchange.ExchangeFactory;
import org.knowm.xchange.binance.BinanceExchange;
import org.knowm.xchange.currency.CurrencyPair;
import org.knowm.xchange.dto.account.AccountInfo;
import org.knowm.xchange.dto.account.Balance;
import org.knowm.xchange.dto.account.Wallet;
import org.knowm.xchange.dto.marketdata.Ticker;
import org.knowm.xchange.service.account.AccountService;
import org.knowm.xchange.service.marketdata.MarketDataService;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Service
@RequiredArgsConstructor
public class TradingTaskService {

    private final TradingBotRepository botRepository;

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public Optional<TradingBot> getFreshBotState(Long botId) {
        return botRepository.findById(botId);
    }
    
    @Async
    public void runTradingLoop(TradingBot bot, WalletCredentialsDTO credentials) {
        System.out.println("🚀 Starting background trading loop for bot ID: " + bot.getId());

        try {
            Exchange binance = ExchangeFactory.INSTANCE.createExchange(BinanceExchange.class);
            binance.getExchangeSpecification().setApiKey(credentials.apiKey());
            binance.getExchangeSpecification().setSecretKey(credentials.secretKey());
            
            // Enable testnet/sandbox mode for test API keys
            binance.getExchangeSpecification().setExchangeSpecificParametersItem("Use_Sandbox", true);
            binance.getExchangeSpecification().setSslUri("https://testnet.binance.vision/");
            binance.getExchangeSpecification().setHost("testnet.binance.vision");
            
            binance.remoteInit();

            MarketDataService marketDataService = binance.getMarketDataService();
            AccountService accountService = binance.getAccountService();

            String[] parts = bot.getSymbol().split("/");
            CurrencyPair pair = new CurrencyPair(parts[0], parts[1]);

            while (true) { 
                Optional<TradingBot> currentBotState = getFreshBotState(bot.getId());

                if (currentBotState.isEmpty() || currentBotState.get().getStatus() != BotStatus.RUNNING) {
                    System.out.println("⏹️ Stopping trading loop for bot ID: " + bot.getId());
                    break;
                }
                
                try {
                    Ticker ticker = marketDataService.getTicker(pair);
                    if (ticker != null) {
                        System.out.println("📈 " + bot.getSymbol() + " price = " + ticker.getLast());
                    } else {
                        System.err.println("⚠️ Failed to fetch ticker for " + bot.getSymbol());
                    }

                    // --- NEW: FETCH AND DISPLAY ACCOUNT BALANCES ---
                    AccountInfo accountInfo = accountService.getAccountInfo();
                    Wallet wallet = accountInfo.getWallet();
                    Balance baseCurrencyBalance = wallet.getBalance(pair.base);   // e.g., ETC
                    Balance counterCurrencyBalance = wallet.getBalance(pair.counter); // e.g., USDT

                    System.out.println("   💰 Account Balances | "
                            + baseCurrencyBalance.getCurrency() + ": " + baseCurrencyBalance.getAvailable()
                            + " | "
                            + counterCurrencyBalance.getCurrency() + ": " + counterCurrencyBalance.getAvailable());
               

                    Thread.sleep(5000);
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
        }
    }
}