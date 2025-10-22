package com.alphintra.trading_engine.service;

import com.alphintra.trading_engine.client.WalletServiceClient;
import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
import com.alphintra.trading_engine.exception.InsufficientBalanceException;
import com.alphintra.trading_engine.model.BotStatus;
import com.alphintra.trading_engine.model.TradingBot;
import com.alphintra.trading_engine.repository.TradingBotRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class TradingService {

    private final TradingBotRepository botRepository;
    private final TradingTaskService tradingTaskService;
    private final WalletServiceClient walletServiceClient;

    public TradingBot startBot(Long userId, Long strategyId, Integer capitalAllocation, String symbol) {
        System.out.println("TradingService: startBot method called for userId=" + userId +
                         ", strategyId=" + strategyId +
                         ", symbol=" + symbol +
                         ", capitalAllocation=" + capitalAllocation + "%");

        System.out.println("🔐 Fetching Coinbase API credentials for user " + userId + " via wallet-service.");
        WalletCredentialsDTO credentials = walletServiceClient.getCredentials(userId);
        String apiKeyPrefix = credentials.apiKey().substring(0, Math.min(credentials.apiKey().length(), 5));
        System.out.println("🔑 Coinbase API key prefix for trading: " + apiKeyPrefix + "...");

        // Extract quote currency (USDT) from symbol
        String[] parts = symbol.split("/");
        String quoteCurrency = (parts.length > 1 ? parts[1] : "USDT").toUpperCase();
        String baseCurrency = parts[0].toUpperCase();

        // Check balance BEFORE creating the bot
        System.out.println("💰 Checking Coinbase balances before starting bot...");
        Map<String, BigDecimal> balances = tradingTaskService.checkBalance(userId, baseCurrency, quoteCurrency);
        BigDecimal availableQuote = balances.get(quoteCurrency);
        
        // Calculate allocated amount based on percentage
        int effectiveAllocation = capitalAllocation != null ? capitalAllocation : 100;
        BigDecimal allocatedAmount = availableQuote
            .multiply(new BigDecimal(effectiveAllocation))
            .divide(new BigDecimal("100"), 2, RoundingMode.DOWN);
        
        BigDecimal minimumRequired = new BigDecimal("10.0");
        
        System.out.println("💵 Available " + quoteCurrency + ": " + availableQuote);
        System.out.println("💵 Allocated (" + effectiveAllocation + "%): " + allocatedAmount);
        System.out.println("💵 Minimum Required: " + minimumRequired);
        
        if (allocatedAmount.compareTo(minimumRequired) < 0) {
            System.err.println("❌ INSUFFICIENT BALANCE - Bot will NOT be created!");
            throw new InsufficientBalanceException(
                quoteCurrency,
                allocatedAmount + " " + quoteCurrency + " (after " + effectiveAllocation + "% allocation)",
                minimumRequired + " " + quoteCurrency
            );
        }
        
        System.out.println("✅ Sufficient balance confirmed. Creating bot...");

        TradingBot bot = new TradingBot();
        bot.setUserId(userId);
        bot.setStrategyId(strategyId);
        bot.setStatus(BotStatus.RUNNING);
        bot.setSymbol(symbol);
        bot.setCapitalAllocation(effectiveAllocation);
        bot.setStartedAt(LocalDateTime.now());
        TradingBot savedBot = botRepository.save(bot);

        // Call the async method on the new service instance
        tradingTaskService.runTradingLoop(savedBot, credentials);
        
        return savedBot;
    }

    public com.alphintra.trading_engine.dto.BalanceInfoResponse getBalanceInfo(Long userId) {
        System.out.println("💰 Requesting Coinbase balance snapshot via wallet-service.");

        WalletCredentialsDTO credentials = walletServiceClient.getCredentials(userId);
        String balanceKeyPrefix = credentials.apiKey().substring(0, Math.min(credentials.apiKey().length(), 5));
        System.out.println("🔑 Coinbase API key prefix for balance request: " + balanceKeyPrefix + "...");

        try {
            // Check balance for BTC/USDT (we just need USDT balance)
            Map<String, BigDecimal> balances = tradingTaskService.checkBalance(userId, "BTC", "USDT");
            BigDecimal usdtBalance = balances.get("USDT");
            BigDecimal btcBalance = balances.get("BTC");

            // Check if balance fetch was successful (non-zero means API worked)
            if (usdtBalance.compareTo(BigDecimal.ZERO) == 0 && btcBalance.compareTo(BigDecimal.ZERO) == 0) {
                System.err.println("⚠️ Warning: Both balances are zero - API key may be invalid");
                return com.alphintra.trading_engine.dto.BalanceInfoResponse.error(
                    "API returned zero balance. Please check: 1) Coinbase API key is valid 2) Key has trading permissions 3) Account has funds"
                );
            }

            System.out.println("✅ Balance retrieved successfully!");
            System.out.println("   USDT: " + usdtBalance);
            System.out.println("   BTC: " + btcBalance);

            return com.alphintra.trading_engine.dto.BalanceInfoResponse.success(
                String.format("%.8f", usdtBalance),
                String.format("%.8f", btcBalance)
            );
        } catch (Exception e) {
            System.err.println("❌ Error fetching balance: " + e.getMessage());
            return com.alphintra.trading_engine.dto.BalanceInfoResponse.error(
                "Failed to retrieve Coinbase balances: " + e.getMessage()
            );
        }
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

    public List<TradingBot> getBotsByUser(Long userId) {
        System.out.println("📋 Fetching all bots for user: " + userId);
        return botRepository.findByUserId(userId);
    }
}