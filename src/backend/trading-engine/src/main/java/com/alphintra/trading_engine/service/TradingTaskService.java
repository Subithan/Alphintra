package com.alphintra.trading_engine.service;

import com.alphintra.trading_engine.client.WalletServiceClient;
import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
import com.alphintra.trading_engine.model.BotStatus;
import com.alphintra.trading_engine.model.Position;
import com.alphintra.trading_engine.model.PositionStatus;
import com.alphintra.trading_engine.model.TradingBot;
import com.alphintra.trading_engine.repository.PositionRepository;
import com.alphintra.trading_engine.repository.TradingBotRepository;
import com.alphintra.trading_engine.strategy.Signal;
import com.alphintra.trading_engine.strategy.SimplePriceStrategy;
import com.alphintra.trading_engine.strategy.TradingStrategy;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import org.knowm.xchange.Exchange;
import org.knowm.xchange.ExchangeFactory;
import org.knowm.xchange.binance.BinanceExchange;
import org.knowm.xchange.currency.CurrencyPair;
import org.knowm.xchange.dto.marketdata.Ticker;
import org.knowm.xchange.service.marketdata.MarketDataService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import com.alphintra.trading_engine.config.ProxySettings;
import org.knowm.xchange.ExchangeSpecification;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class TradingTaskService {

    private final TradingBotRepository botRepository;
    private final OrderExecutionService orderExecutionService;
    private final PositionRepository positionRepository;
    private final ProxySettings proxySettings;
    private final WalletServiceClient walletServiceClient;

    @Value("${binance.api.enabled:true}")
    private boolean binanceApiEnabled;

    @Value("${binance.api.testnet.enabled:true}")
    private boolean binanceTestnetEnabled;

    // Step size mapping for different trading pairs
    private static final Map<String, BigDecimal> STEP_SIZE_MAP = Map.of(
        "BTC/USDT", new BigDecimal("0.00001"),
        "ETH/USDT", new BigDecimal("0.0001"),
        "BNB/USDT", new BigDecimal("0.001"),
        "SOL/USDT", new BigDecimal("0.01"),
        "ETC/USDT", new BigDecimal("0.01"),
        "XRP/USDT", new BigDecimal("0.1"),
        "ADA/USDT", new BigDecimal("0.1"),
        "DOGE/USDT", new BigDecimal("1")
    );
    
    private static final BigDecimal DEFAULT_STEP_SIZE = new BigDecimal("0.01"); // Fallback

    // Singleton instances for the shared exchange connection
    private Exchange binanceExchange;
    private MarketDataService marketDataService;

    @PostConstruct
    public void initializeExchange() {
        System.out.println("🔧 Initializing shared Binance Exchange connection (this happens only once)...");

        // Check if Binance API is enabled in configuration
        if (!binanceApiEnabled) {
            System.out.println("⚠️ Binance API is disabled in configuration. Trading functionality will be disabled.");
            System.out.println("   Set BINANCE_API_ENABLED=true to enable trading functionality.");
            binanceExchange = null;
            marketDataService = null;
            return;
        }

        System.out.println("🌐 Binance API is enabled. Attempting to initialize exchange connection...");
        try {
            binanceExchange = ExchangeFactory.INSTANCE.createExchange(BinanceExchange.class);

            // Always work against a single spec instance, then apply once
            ExchangeSpecification spec = binanceExchange.getExchangeSpecification();

            if (binanceTestnetEnabled) {
                System.out.println("🧪 Using Binance Testnet (testnet.binance.vision)");
                spec.setExchangeSpecificParametersItem("Use_Sandbox", true);
                spec.setSslUri("https://testnet.binance.vision");
                spec.setHost("testnet.binance.vision");
            } else {
                System.out.println("🚀 Using Binance Production API");
                spec.setExchangeSpecificParametersItem("Use_Sandbox", false);
                spec.setSslUri("https://api.binance.com");
                spec.setHost("api.binance.com");
            }

            // Apply proxy settings if provided
            if (proxySettings.isEnabled()) {
                spec.setProxyHost(proxySettings.getHost());
                spec.setProxyPort(proxySettings.getPort());
                System.out.println("🔌 Applied HTTP proxy to XChange: " + proxySettings.getHost() + ":" + proxySettings.getPort());
            }

            // Apply the full spec before remote init
            binanceExchange.applySpecification(spec);
            System.out.println("➡️ XChange target endpoint: " + spec.getSslUri() + " (host=" + spec.getHost() + ")");

            // The slow call, now executed only on application startup
            binanceExchange.remoteInit();
            marketDataService = binanceExchange.getMarketDataService();
            System.out.println("✅ Shared Binance Exchange connection initialized successfully.");
            System.out.println("   Environment: " + (binanceTestnetEnabled ? "Testnet" : "Production"));
        } catch (Exception e) {
            System.err.println("⚠️ WARNING: Could not initialize Binance Exchange on startup. Trading functionality will be disabled.");
            System.err.println("   Error: " + e.getMessage());
            if (e.getMessage().contains("HTTP status code was not OK: 451")) {
                System.err.println("   📍 This appears to be a geographic restriction issue.");
                System.err.println("   💡 Solutions:");
                System.err.println("      1. Set BINANCE_API_ENABLED=false to disable trading in cloud");
                System.err.println("      2. Deploy to a non-US region (e.g., Europe, Asia)");
                System.err.println("      3. Use a VPN/proxy solution");
                System.err.println("      4. Use a different exchange API");
            }
            System.err.println("   Application will continue without exchange integration.");
            // Set exchange to null to indicate it's not available
            binanceExchange = null;
            marketDataService = null;
        }
    }

    @Async
    public void runTradingLoop(TradingBot bot, WalletCredentialsDTO credentials) {
        System.out.println("🚀 Starting background trading loop for bot ID: " + bot.getId());

        // Check if exchange is available
        if (binanceExchange == null || marketDataService == null) {
            System.err.println("❌ Exchange service is not available. Trading loop cannot start for bot ID: " + bot.getId());
            return;
        }

        try {
            // --- The slow initialization is GONE from this loop ---
            TradingStrategy strategy = new SimplePriceStrategy();
            String[] parts = bot.getSymbol().split("/");
            String baseCurrency = parts[0].toUpperCase();
            String quoteCurrency = parts[1].toUpperCase();
            CurrencyPair pair = new CurrencyPair(baseCurrency, quoteCurrency);

            while (true) {
                Optional<TradingBot> currentBotState = getFreshBotState(bot.getId());
                if (currentBotState.isEmpty() || currentBotState.get().getStatus() != BotStatus.RUNNING) {
                    System.out.println("⏹️ Stopping trading loop for bot ID: " + bot.getId());
                    break;
                }

                try {
                    Optional<Position> openPosition = positionRepository.findByUserIdAndSymbolAndStatus(bot.getUserId(), bot.getSymbol(), PositionStatus.OPEN);

                    Ticker ticker = marketDataService.getTicker(pair);
                    if (ticker == null) {
                        System.err.println("⚠️ Failed to fetch ticker. Skipping loop.");
                        Thread.sleep(5000);
                        continue;
                    }
                    BigDecimal currentPrice = ticker.getLast();
                    System.out.println("📈 " + bot.getSymbol() + " price = " + currentPrice);

                    Map<String, BigDecimal> balances = getBalancesForUser(bot.getUserId(), baseCurrency, quoteCurrency);
                    Signal signal = strategy.decide(bot.getSymbol(), currentPrice, balances, openPosition);

                    switch (signal) {
                        case BUY:
                            System.out.println("🔥 ACTION: Preparing to execute a BUY order.");
                            
                            // Get the capital allocation percentage from the bot
                            Integer capitalAllocationPercent = bot.getCapitalAllocation();
                            if (capitalAllocationPercent == null) {
                                capitalAllocationPercent = 100; // Default to 100%
                            }
                            
                            // Calculate available USDT balance and apply capital allocation percentage
                            BigDecimal totalAvailableUsdt = balances.get(quoteCurrency);
                            BigDecimal allocatedUsdtToSpend = totalAvailableUsdt
                                .multiply(new BigDecimal(capitalAllocationPercent))
                                .divide(new BigDecimal("100"), 2, RoundingMode.DOWN);
                            
                            System.out.println("💰 Capital Allocation: " + capitalAllocationPercent + "% of " + totalAvailableUsdt + " USDT = " + allocatedUsdtToSpend + " USDT to spend");
                            
                            // Ensure we have a minimum USDT amount to trade
                            if (allocatedUsdtToSpend.compareTo(new BigDecimal("10.0")) < 0) {
                                System.out.println("⚠️ Allocated capital (" + allocatedUsdtToSpend + " USDT) is below minimum trade amount of 10 USDT. Skipping BUY.");
                                break;
                            }
                            
                            // Calculate how much crypto we can buy with the allocated USDT
                            BigDecimal stepSize = getStepSizeForSymbol(bot.getSymbol());
                            BigDecimal rawCryptoQuantityToBuy = allocatedUsdtToSpend.divide(currentPrice, 8, RoundingMode.DOWN);
                            BigDecimal adjustedCryptoQuantity = adjustQuantityToStepSize(rawCryptoQuantityToBuy, stepSize);
                            
                            System.out.println("📊 Buying " + adjustedCryptoQuantity + " " + baseCurrency + " with " + allocatedUsdtToSpend + " USDT at price " + currentPrice + " USDT per " + baseCurrency);
                            
                            orderExecutionService.placeMarketOrder(bot, credentials, bot.getSymbol(), "BUY", adjustedCryptoQuantity, openPosition);
                            break;
                        case SELL:
                            if (openPosition.isPresent()) {
                                System.out.println("💰 ACTION: Preparing to execute a SELL order.");
                                BigDecimal sellQuantity = openPosition.get().getQuantity();
                                // We sell the exact quantity from our position, so no need to adjust
                                orderExecutionService.placeMarketOrder(bot, credentials, bot.getSymbol(), "SELL", sellQuantity, openPosition);
                            } else {
                                System.out.println("⚠️ STRATEGY WARNING: Received SELL signal but no open position found.");
                            }
                            break;
                        case HOLD:
                             // No action needed, but logging is handled by the strategy now.
                            break;
                    }
                    long sleepTime = (signal == Signal.BUY || signal == Signal.SELL) ? 15000 : 5000;
                    Thread.sleep(sleepTime);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    System.err.println("⏹️ Trading loop interrupted for bot " + bot.getId());
                    break;
                } catch (Exception e) {
                    System.err.println("❌ Error in trading loop: " + e.getMessage());
                    e.printStackTrace();
                }
            }
        } catch (Exception e) {
            System.err.println("🔥 FATAL ERROR in trading loop for bot " + bot.getId() + ": " + e.getMessage());
            e.printStackTrace();
        }
    }

    private Map<String, BigDecimal> getBalancesForUser(Long userId, String baseCurrency, String quoteCurrency) {
        String normalizedBase = baseCurrency.toUpperCase();
        String normalizedQuote = quoteCurrency.toUpperCase();

        BigDecimal baseAmount = BigDecimal.ZERO;
        BigDecimal quoteAmount = BigDecimal.ZERO;

        try {
            Map<String, BigDecimal> walletServiceBalances = walletServiceClient.getCoinbaseBalances(userId);
            if (walletServiceBalances != null) {
                baseAmount = walletServiceBalances.getOrDefault(normalizedBase, BigDecimal.ZERO);
                quoteAmount = walletServiceBalances.getOrDefault(normalizedQuote, BigDecimal.ZERO);
            }
        } catch (Exception e) {
            System.err.println("❌ Failed to fetch Coinbase balances for userId " + userId + ": " + e.getMessage());
        }

        Map<String, BigDecimal> balances = new HashMap<>();
        balances.put(baseCurrency, baseAmount);
        balances.put(normalizedBase, baseAmount);
        balances.put(quoteCurrency, quoteAmount);
        balances.put(normalizedQuote, quoteAmount);
        return balances;
    }

    // Unchanged helper methods
    @Transactional(propagation = Propagation.REQUIRES_NEW) public Optional<TradingBot> getFreshBotState(Long botId) { return botRepository.findById(botId); }

    // Public method for balance check (used by TradingService before starting bot)
    public Map<String, BigDecimal> checkBalance(Long userId, String baseCurrency, String quoteCurrency) {
        return getBalancesForUser(userId, baseCurrency, quoteCurrency);
    }
    
    private BigDecimal getStepSizeForSymbol(String symbol) {
        return STEP_SIZE_MAP.getOrDefault(symbol, DEFAULT_STEP_SIZE);
    }
    
    private BigDecimal adjustQuantityToStepSize(BigDecimal quantity, BigDecimal stepSize) { BigDecimal steps = quantity.divide(stepSize, 0, RoundingMode.DOWN); BigDecimal adjustedQuantity = steps.multiply(stepSize); int scale = stepSize.stripTrailingZeros().scale(); return adjustedQuantity.setScale(scale, RoundingMode.DOWN); }
}
