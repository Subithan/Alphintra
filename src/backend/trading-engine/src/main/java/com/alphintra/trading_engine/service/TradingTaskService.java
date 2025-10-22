package com.alphintra.trading_engine.service;

import com.alphintra.trading_engine.client.WalletServiceClient;
import com.alphintra.trading_engine.dto.CoinbasePositionDTO;
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
import lombok.RequiredArgsConstructor;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.time.format.DateTimeParseException;
import java.time.OffsetDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class TradingTaskService {

    private final TradingBotRepository botRepository;
    private final OrderExecutionService orderExecutionService;
    private final PositionRepository positionRepository;
    private final WalletServiceClient walletServiceClient;

    @Async
    public void runTradingLoop(TradingBot bot, WalletCredentialsDTO credentials) {
        System.out.println("🚀 Starting background trading loop for bot ID: " + bot.getId());

        TradingStrategy strategy = new SimplePriceStrategy();
        String symbol = bot.getSymbol();
        String[] parts = symbol.split("/");
        String baseCurrency = parts[0].toUpperCase();
        String quoteCurrency = (parts.length > 1 ? parts[1] : "USDT").toUpperCase();

        while (true) {
            Optional<TradingBot> currentBotState = getFreshBotState(bot.getId());
            if (currentBotState.isEmpty() || currentBotState.get().getStatus() != BotStatus.RUNNING) {
                System.out.println("⏹️ Stopping trading loop for bot ID: " + bot.getId());
                break;
            }

            try {
                Optional<Position> openPosition = refreshOpenPosition(bot);

                BigDecimal currentPrice = walletServiceClient.getCoinbaseSpotPrice(symbol);
                if (currentPrice == null) {
                    System.err.println("⚠️ Wallet service returned null price for " + symbol + ". Retrying soon.");
                    Thread.sleep(5000);
                    continue;
                }

                System.out.println("📈 " + symbol + " price = " + currentPrice);

                Map<String, BigDecimal> balances = getBalancesForUser(bot.getUserId(), baseCurrency, quoteCurrency);
                Signal signal = strategy.decide(symbol, currentPrice, balances, openPosition);

                switch (signal) {
                    case BUY -> handleBuySignal(bot, symbol, baseCurrency, quoteCurrency, currentPrice, balances, openPosition, credentials);
                    case SELL -> handleSellSignal(bot, symbol, openPosition, credentials);
                    case HOLD -> {
                        // No action required.
                    }
                }

                long sleepTime = (signal == Signal.BUY || signal == Signal.SELL) ? 15000 : 5000;
                Thread.sleep(sleepTime);
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                System.err.println("⏹️ Trading loop interrupted for bot " + bot.getId());
                break;
            } catch (Exception e) {
                System.err.println("❌ Error in trading loop for bot " + bot.getId() + ": " + e.getMessage());
                e.printStackTrace();
            }
        }
    }

    private void handleBuySignal(TradingBot bot,
                                 String symbol,
                                 String baseCurrency,
                                 String quoteCurrency,
                                 BigDecimal currentPrice,
                                 Map<String, BigDecimal> balances,
                                 Optional<Position> openPosition,
                                 WalletCredentialsDTO credentials) {
        System.out.println("🔥 ACTION: Preparing to execute a BUY order.");

        Integer capitalAllocationPercent = bot.getCapitalAllocation() != null ? bot.getCapitalAllocation() : 100;
        BigDecimal totalAvailableQuote = balances.getOrDefault(quoteCurrency, BigDecimal.ZERO);
        BigDecimal allocatedQuoteToSpend = totalAvailableQuote
                .multiply(new BigDecimal(capitalAllocationPercent))
                .divide(new BigDecimal("100"), 2, RoundingMode.DOWN);

        System.out.println("💰 Capital Allocation: " + capitalAllocationPercent + "% of " + totalAvailableQuote + " " + quoteCurrency +
                " = " + allocatedQuoteToSpend + " " + quoteCurrency + " to spend");

        if (allocatedQuoteToSpend.compareTo(new BigDecimal("10.0")) < 0) {
            System.out.println("⚠️ Allocated capital (" + allocatedQuoteToSpend + " " + quoteCurrency + ") is below minimum trade amount. Skipping BUY.");
            return;
        }

        BigDecimal quantityToBuy = allocatedQuoteToSpend.divide(currentPrice, 8, RoundingMode.DOWN);
        if (quantityToBuy.compareTo(BigDecimal.ZERO) <= 0) {
            System.out.println("⚠️ Calculated quantity to buy is non-positive. Skipping BUY.");
            return;
        }

        System.out.println("📊 Buying " + quantityToBuy + " " + baseCurrency + " with " + allocatedQuoteToSpend + " " + quoteCurrency +
                " at price " + currentPrice + " " + quoteCurrency + " per " + baseCurrency);

        orderExecutionService.placeMarketOrder(bot, credentials, symbol, "BUY", quantityToBuy, openPosition);
    }

    private void handleSellSignal(TradingBot bot, String symbol, Optional<Position> openPosition, WalletCredentialsDTO credentials) {
        if (openPosition.isPresent()) {
            System.out.println("💰 ACTION: Preparing to execute a SELL order.");
            BigDecimal sellQuantity = openPosition.get().getQuantity();
            if (sellQuantity == null || sellQuantity.compareTo(BigDecimal.ZERO) <= 0) {
                System.out.println("⚠️ Open position quantity is invalid. Skipping SELL.");
                return;
            }
            orderExecutionService.placeMarketOrder(bot, credentials, symbol, "SELL", sellQuantity, openPosition);
        } else {
            System.out.println("⚠️ STRATEGY WARNING: Received SELL signal but no open position found.");
        }
    }

    private Optional<Position> refreshOpenPosition(TradingBot bot) {
        try {
            List<CoinbasePositionDTO> remotePositions = walletServiceClient.getCoinbasePositions(bot.getUserId());
            String targetProductId = normalizeProductId(bot.getSymbol());

            for (CoinbasePositionDTO remote : remotePositions) {
                String remoteProductId = firstNonBlank(remote.productId(), remote.symbol());
                if (remoteProductId == null || !remoteProductId.equalsIgnoreCase(targetProductId)) {
                    continue;
                }
                if ("CLOSED".equalsIgnoreCase(remote.status())) {
                    continue;
                }

                Position position = positionRepository.findFirstByUserIdAndSymbol(bot.getUserId(), bot.getSymbol())
                        .orElse(new Position());

                position.setUserId(bot.getUserId());
                position.setBotId(bot.getId());
                position.setAsset(Optional.ofNullable(remote.baseCurrency()).orElse(bot.getSymbol().split("/")[0]));
                position.setSymbol(bot.getSymbol());

                BigDecimal quantity = safeDecimal(remote.quantity());
                if (quantity != null) {
                    position.setQuantity(quantity);
                }

                BigDecimal entryPrice = safeDecimal(remote.entryPrice());
                if (entryPrice != null) {
                    position.setEntryPrice(entryPrice);
                }

                position.setStatus(PositionStatus.OPEN);
                position.setOpenedAt(parseTimestamp(remote.openedAt()).orElseGet(LocalDateTime::now));
                position.setClosedAt(null);

                return Optional.of(positionRepository.save(position));
            }

            closeStaleLocalPosition(bot);
            return Optional.empty();
        } catch (Exception e) {
            System.err.println("⚠️ Failed to refresh positions from wallet service: " + e.getMessage());
            return positionRepository.findByUserIdAndSymbolAndStatus(bot.getUserId(), bot.getSymbol(), PositionStatus.OPEN);
        }
    }

    private void closeStaleLocalPosition(TradingBot bot) {
        positionRepository.findByUserIdAndSymbolAndStatus(bot.getUserId(), bot.getSymbol(), PositionStatus.OPEN)
                .ifPresent(position -> {
                    position.setStatus(PositionStatus.CLOSED);
                    position.setClosedAt(LocalDateTime.now());
                    positionRepository.save(position);
                });
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

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public Optional<TradingBot> getFreshBotState(Long botId) {
        return botRepository.findById(botId);
    }

    public Map<String, BigDecimal> checkBalance(Long userId, String baseCurrency, String quoteCurrency) {
        return getBalancesForUser(userId, baseCurrency, quoteCurrency);
    }

    private BigDecimal safeDecimal(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        try {
            return new BigDecimal(value);
        } catch (NumberFormatException e) {
            System.err.println("⚠️ Unable to parse decimal from wallet service value: " + value);
            return null;
        }
    }

    private Optional<LocalDateTime> parseTimestamp(String value) {
        if (value == null || value.isBlank()) {
            return Optional.empty();
        }
        try {
            return Optional.of(OffsetDateTime.parse(value).toLocalDateTime());
        } catch (DateTimeParseException ex) {
            System.err.println("⚠️ Unable to parse timestamp from wallet service value: " + value);
            return Optional.empty();
        }
    }

    private String normalizeProductId(String symbol) {
        return symbol.replace("/", "-").toUpperCase();
    }

    private String firstNonBlank(String... values) {
        for (String value : values) {
            if (value != null && !value.isBlank()) {
                return value;
            }
        }
        return null;
    }
}
