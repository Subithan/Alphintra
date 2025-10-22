package com.alphintra.trading_engine.service;

import com.alphintra.trading_engine.client.WalletServiceClient;
import com.alphintra.trading_engine.dto.CoinbaseFillDTO;
import com.alphintra.trading_engine.dto.CoinbaseMarketOrderResponseDTO;
import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
import com.alphintra.trading_engine.model.Position;
import com.alphintra.trading_engine.model.PositionStatus;
import com.alphintra.trading_engine.model.TradeOrder;
import com.alphintra.trading_engine.model.TradingBot;
import com.alphintra.trading_engine.repository.PositionRepository;
import com.alphintra.trading_engine.repository.TradeOrderRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class OrderExecutionService {

    private final PositionRepository positionRepository;
    private final TradeOrderRepository tradeOrderRepository;
    private final WalletServiceClient walletServiceClient;

    @Transactional
    public void placeMarketOrder(TradingBot bot, WalletCredentialsDTO credentials, String symbol, String side, BigDecimal quantity, Optional<Position> openPositionOpt) {
        System.out.println("EXECUTING ORDER: " + side + " " + quantity + " " + symbol);
        try {
            CoinbaseMarketOrderResponseDTO orderResponse =
                    "BUY".equalsIgnoreCase(side)
                            ? walletServiceClient.placeCoinbaseMarketBuy(bot.getUserId(), symbol, quantity)
                            : walletServiceClient.placeCoinbaseMarketSell(bot.getUserId(), symbol, quantity);

            if (orderResponse == null) {
                System.err.println("❌ Wallet service returned null response when placing market order.");
                return;
            }

            TradeOrder tradeOrder = buildTradeOrder(bot, symbol, side, orderResponse);
            tradeOrderRepository.save(tradeOrder);
            System.out.println("✅ HISTORICAL TRADE ORDER saved to database.");

            if ("BUY".equalsIgnoreCase(side)) {
                upsertOpenPosition(bot, symbol, tradeOrder);
            } else if ("SELL".equalsIgnoreCase(side)) {
                closeExistingPosition(openPositionOpt);
            }
        } catch (Exception e) {
            System.err.println("🔥 FATAL ERROR placing order: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private TradeOrder buildTradeOrder(TradingBot bot, String symbol, String side, CoinbaseMarketOrderResponseDTO response) {
        TradeOrder tradeOrder = new TradeOrder();
        tradeOrder.setBotId(bot.getId());
        tradeOrder.setExchangeOrderId(response.orderId());
        tradeOrder.setSymbol(symbol);
        tradeOrder.setType(Optional.ofNullable(response.orderType()).orElse("MARKET"));
        tradeOrder.setSide(side.toUpperCase());
        tradeOrder.setStatus(Optional.ofNullable(response.status()).orElse("UNKNOWN"));
        tradeOrder.setCreatedAt(LocalDateTime.now());

        BigDecimal filledSize = Optional.ofNullable(parseDecimal(response.filledSize())).orElse(BigDecimal.ZERO);
        BigDecimal averagePrice = resolveAveragePrice(response);
        tradeOrder.setAmount(filledSize);
        tradeOrder.setPrice(averagePrice);

        return tradeOrder;
    }

    private void upsertOpenPosition(TradingBot bot, String symbol, TradeOrder tradeOrder) {
        Position position = positionRepository.findFirstByUserIdAndSymbol(bot.getUserId(), symbol)
                .orElse(new Position());
        String asset = symbol.split("/")[0];
        position.setUserId(bot.getUserId());
        position.setBotId(bot.getId());
        position.setAsset(asset);
        position.setSymbol(symbol);
        position.setQuantity(tradeOrder.getAmount());
        position.setEntryPrice(tradeOrder.getPrice());
        position.setStatus(PositionStatus.OPEN);
        position.setOpenedAt(Optional.ofNullable(position.getOpenedAt()).orElse(LocalDateTime.now()));
        position.setClosedAt(null);

        positionRepository.save(position);
        System.out.println("✅ POSITION OPENED and saved to database.");
    }

    private void closeExistingPosition(Optional<Position> openPositionOpt) {
        openPositionOpt.ifPresent(positionToClose -> {
            positionToClose.setStatus(PositionStatus.CLOSED);
            positionToClose.setClosedAt(LocalDateTime.now());
            positionRepository.save(positionToClose);
            System.out.println("✅ POSITION CLOSED and updated in database.");
        });
    }

    private BigDecimal resolveAveragePrice(CoinbaseMarketOrderResponseDTO response) {
        BigDecimal responseAverage = parseDecimal(response.averagePrice());
        if (responseAverage != null && responseAverage.compareTo(BigDecimal.ZERO) > 0) {
            return responseAverage;
        }

        List<CoinbaseFillDTO> fills = response.fills();
        if (fills == null || fills.isEmpty()) {
            return BigDecimal.ZERO;
        }

        BigDecimal totalCost = BigDecimal.ZERO;
        BigDecimal totalQuantity = BigDecimal.ZERO;
        for (CoinbaseFillDTO fill : fills) {
            BigDecimal price = parseDecimal(fill.price());
            BigDecimal qty = parseDecimal(fill.size());
            if (price == null || qty == null) {
                continue;
            }
            totalCost = totalCost.add(price.multiply(qty));
            totalQuantity = totalQuantity.add(qty);
        }

        if (totalQuantity.compareTo(BigDecimal.ZERO) == 0) {
            return BigDecimal.ZERO;
        }
        return totalCost.divide(totalQuantity, 8, RoundingMode.HALF_UP);
    }

    private BigDecimal parseDecimal(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        try {
            return new BigDecimal(value);
        } catch (NumberFormatException e) {
            System.err.println("⚠️ Unable to parse decimal value: " + value);
            return null;
        }
    }
}
