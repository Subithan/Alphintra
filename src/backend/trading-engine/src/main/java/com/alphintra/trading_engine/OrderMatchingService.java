package com.alphintra.trading_engine;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

@Service
public class OrderMatchingService {

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private TradeRepository tradeRepository;

    @Autowired
    private TradingAccountRepository tradingAccountRepository;

    @Autowired
    private AssetBalanceRepository assetBalanceRepository;

    @Autowired
    private PositionRepository positionRepository;

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    private static final String TRADE_TOPIC = "trades";
    private static final String TRADE_CACHE_PREFIX = "trade:";
    private static final BigDecimal FEE_RATE = new BigDecimal("0.001"); // 0.1% fee

    @Transactional
    public void matchOrder(Order newOrder) {
        if (!newOrder.getOrderType().equals("LIMIT") || !newOrder.getStatus().equals("PENDING")) {
            return; // Only match LIMIT orders in PENDING status
        }

        String symbol = newOrder.getSymbol();
        String side = newOrder.getSide();
        BigDecimal price = newOrder.getPrice();
        BigDecimal remainingQuantity = newOrder.getQuantity().subtract(newOrder.getFilledQuantity());

        // Find matching orders (opposite side, same symbol, compatible price)
        String oppositeSide = side.equals("BUY") ? "SELL" : "BUY";
        List<Order> matchingOrders = orderRepository.findAll().stream()
                .filter(o -> o.getSymbol().equals(symbol)
                        && o.getSide().equals(oppositeSide)
                        && o.getStatus().equals("PENDING")
                        && o.getOrderType().equals("LIMIT")
                        && (side.equals("BUY") ? o.getPrice().compareTo(price) <= 0 : o.getPrice().compareTo(price) >= 0))
                .sorted((o1, o2) -> {
                    int priceCompare = side.equals("BUY") ? o1.getPrice().compareTo(o2.getPrice()) : o2.getPrice().compareTo(o1.getPrice());
                    if (priceCompare != 0) return priceCompare;
                    return o1.getCreatedAt().compareTo(o2.getCreatedAt());
                })
                .toList();

        for (Order matchingOrder : matchingOrders) {
            if (remainingQuantity.compareTo(BigDecimal.ZERO) <= 0) break;

            BigDecimal matchQuantity = remainingQuantity.min(matchingOrder.getQuantity().subtract(matchingOrder.getFilledQuantity()));
            if (matchQuantity.compareTo(BigDecimal.ZERO) <= 0) continue;

            BigDecimal tradePrice = matchingOrder.getCreatedAt().isBefore(newOrder.getCreatedAt()) ? matchingOrder.getPrice() : newOrder.getPrice();
            String tradeType = matchingOrder.getCreatedAt().isBefore(newOrder.getCreatedAt()) ? "MAKER" : "TAKER";

            // Create trade for buyer
            Trade buyTrade = new Trade();
            buyTrade.setTradeUuid(UUID.randomUUID());
            buyTrade.setOrder(side.equals("BUY") ? newOrder : matchingOrder);
            buyTrade.setUser(buyTrade.getOrder().getUser());
            buyTrade.setAccount(buyTrade.getOrder().getAccount());
            buyTrade.setSymbol(symbol);
            buyTrade.setSide("BUY");
            buyTrade.setQuantity(matchQuantity);
            buyTrade.setPrice(tradePrice);
            buyTrade.setFee(matchQuantity.multiply(tradePrice).multiply(FEE_RATE));
            buyTrade.setExchange("internal");
            buyTrade.setTradeType(tradeType);
            buyTrade.setTimestamp(OffsetDateTime.now());

            // Create trade for seller
            Trade sellTrade = new Trade();
            sellTrade.setTradeUuid(UUID.randomUUID());
            sellTrade.setOrder(side.equals("BUY") ? matchingOrder : newOrder);
            sellTrade.setUser(sellTrade.getOrder().getUser());
            sellTrade.setAccount(sellTrade.getOrder().getAccount());
            sellTrade.setSymbol(symbol);
            sellTrade.setSide("SELL");
            sellTrade.setQuantity(matchQuantity);
            sellTrade.setPrice(tradePrice);
            sellTrade.setFee(matchQuantity.multiply(tradePrice).multiply(FEE_RATE));
            sellTrade.setExchange("internal");
            sellTrade.setTradeType(tradeType);
            sellTrade.setTimestamp(OffsetDateTime.now());

            // Update orders
            newOrder.setFilledQuantity(newOrder.getFilledQuantity().add(matchQuantity));
            newOrder.setAveragePrice(calculateAveragePrice(newOrder, matchQuantity, tradePrice));
            newOrder.setFee(newOrder.getFee().add(buyTrade.getFee()));
            newOrder.setStatus(newOrder.getFilledQuantity().compareTo(newOrder.getQuantity()) >= 0 ? "FILLED" : "PARTIALLY_FILLED");
            newOrder.setUpdatedAt(OffsetDateTime.now());

            matchingOrder.setFilledQuantity(matchingOrder.getFilledQuantity().add(matchQuantity));
            matchingOrder.setAveragePrice(calculateAveragePrice(matchingOrder, matchQuantity, tradePrice));
            matchingOrder.setFee(matchingOrder.getFee().add(sellTrade.getFee()));
            matchingOrder.setStatus(matchingOrder.getFilledQuantity().compareTo(matchingOrder.getQuantity()) >= 0 ? "FILLED" : "PARTIALLY_FILLED");
            matchingOrder.setUpdatedAt(OffsetDateTime.now());

            // Update balances and positions
            updateBalancesAndPositions(newOrder, matchingOrder, matchQuantity, tradePrice);

            // Save trades and orders
            tradeRepository.save(buyTrade);
            tradeRepository.save(sellTrade);
            orderRepository.save(newOrder);
            orderRepository.save(matchingOrder);

            // Cache trades in Redis as JSON
            try {
                redisTemplate.opsForValue().set(TRADE_CACHE_PREFIX + buyTrade.getTradeUuid(), objectMapper.writeValueAsString(buyTrade));
                redisTemplate.opsForValue().set(TRADE_CACHE_PREFIX + sellTrade.getTradeUuid(), objectMapper.writeValueAsString(sellTrade));
            } catch (JsonProcessingException e) {
                throw new RuntimeException("Failed to serialize trade to JSON", e);
            }

            // Publish trades to Kafka
            kafkaTemplate.send(TRADE_TOPIC, buyTrade.getTradeUuid().toString(), buyTrade.toString());
            kafkaTemplate.send(TRADE_TOPIC, sellTrade.getTradeUuid().toString(), sellTrade.toString());

            remainingQuantity = remainingQuantity.subtract(matchQuantity);
        }

        if (remainingQuantity.compareTo(BigDecimal.ZERO) > 0 && newOrder.getTimeInForce().equals("IOC")) {
            newOrder.setStatus("CANCELED");
            orderRepository.save(newOrder);
        }
    }

    private BigDecimal calculateAveragePrice(Order order, BigDecimal matchQuantity, BigDecimal tradePrice) {
        BigDecimal totalFilled = order.getFilledQuantity().add(matchQuantity);
        if (totalFilled.compareTo(BigDecimal.ZERO) <= 0) return order.getAveragePrice();
        BigDecimal previousValue = order.getAveragePrice() != null ? order.getAveragePrice().multiply(order.getFilledQuantity()) : BigDecimal.ZERO;
        return previousValue.add(matchQuantity.multiply(tradePrice)).divide(totalFilled, 8, BigDecimal.ROUND_HALF_UP);
    }

    private BigDecimal calculateAveragePrice(Position position, BigDecimal quantity, BigDecimal price) {
        BigDecimal totalQuantity = position.getQuantity().add(quantity);
        if (totalQuantity.compareTo(BigDecimal.ZERO) <= 0) return position.getAveragePrice();
        BigDecimal previousValue = position.getAveragePrice() != null ? position.getAveragePrice().multiply(position.getQuantity()) : BigDecimal.ZERO;
        return previousValue.add(quantity.multiply(price)).divide(totalQuantity, 8, BigDecimal.ROUND_HALF_UP);
    }

    private void updateBalancesAndPositions(Order buyOrder, Order sellOrder, BigDecimal quantity, BigDecimal price) {
        // Assume symbol is BASE/QUOTE (e.g., BTC/USD)
        String baseAsset = buyOrder.getSymbol().split("/")[0]; // e.g., BTC
        String quoteAsset = buyOrder.getSymbol().split("/")[1]; // e.g., USD

        // Update buyer's balances
        TradingAccount buyerAccount = buyOrder.getSide().equals("BUY") ? buyOrder.getAccount() : sellOrder.getAccount();
        AssetBalance buyerBase = assetBalanceRepository.findByAccountAccountIdAndAsset(buyerAccount.getAccountId(), baseAsset);
        AssetBalance buyerQuote = assetBalanceRepository.findByAccountAccountIdAndAsset(buyerAccount.getAccountId(), quoteAsset);

        if (buyerBase == null) {
            buyerBase = new AssetBalance();
            buyerBase.setAccount(buyerAccount);
            buyerBase.setAsset(baseAsset);
            buyerBase.setUpdatedAt(OffsetDateTime.now());
        }
        if (buyerQuote == null) {
            buyerQuote = new AssetBalance();
            buyerQuote.setAccount(buyerAccount);
            buyerQuote.setAsset(quoteAsset);
            buyerQuote.setUpdatedAt(OffsetDateTime.now());
        }

        BigDecimal quoteCost = quantity.multiply(price).add(quantity.multiply(price).multiply(FEE_RATE));
        buyerBase.setTotalBalance(buyerBase.getTotalBalance().add(quantity));
        buyerBase.setAvailableBalance(buyerBase.getAvailableBalance().add(quantity));
        buyerBase.setUpdatedAt(OffsetDateTime.now());
        buyerQuote.setTotalBalance(buyerQuote.getTotalBalance().subtract(quoteCost));
        buyerQuote.setAvailableBalance(buyerQuote.getAvailableBalance().subtract(quoteCost));
        buyerQuote.setUpdatedAt(OffsetDateTime.now());
        buyerAccount.setTotalBalance(buyerAccount.getTotalBalance().subtract(quoteCost));
        buyerAccount.setAvailableBalance(buyerAccount.getAvailableBalance().subtract(quoteCost));
        buyerAccount.setUpdatedAt(OffsetDateTime.now());

        // Update buyer's position
        Position buyerPosition = positionRepository.findAll().stream()
                .filter(p -> p.getAccount().getAccountId().equals(buyerAccount.getAccountId()) && p.getSymbol().equals(buyOrder.getSymbol()))
                .findFirst()
                .orElseGet(() -> {
                    Position p = new Position();
                    p.setUser(buyerAccount.getUser());
                    p.setAccount(buyerAccount);
                    p.setSymbol(buyOrder.getSymbol());
                    p.setUpdatedAt(OffsetDateTime.now());
                    return p;
                });
        buyerPosition.setQuantity(buyerPosition.getQuantity().add(quantity));
        buyerPosition.setAveragePrice(calculateAveragePrice(buyerPosition, quantity, price));
        buyerPosition.setUpdatedAt(OffsetDateTime.now());
        positionRepository.save(buyerPosition);

        // Update seller's balances
        TradingAccount sellerAccount = buyOrder.getSide().equals("SELL") ? buyOrder.getAccount() : sellOrder.getAccount();
        AssetBalance sellerBase = assetBalanceRepository.findByAccountAccountIdAndAsset(sellerAccount.getAccountId(), baseAsset);
        AssetBalance sellerQuote = assetBalanceRepository.findByAccountAccountIdAndAsset(sellerAccount.getAccountId(), quoteAsset);

        if (sellerBase == null) {
            sellerBase = new AssetBalance();
            sellerBase.setAccount(sellerAccount);
            sellerBase.setAsset(baseAsset);
            sellerBase.setUpdatedAt(OffsetDateTime.now());
        }
        if (sellerQuote == null) {
            sellerQuote = new AssetBalance();
            sellerQuote.setAccount(sellerAccount);
            sellerQuote.setAsset(quoteAsset);
            sellerQuote.setUpdatedAt(OffsetDateTime.now());
        }

        BigDecimal quoteReceived = quantity.multiply(price).subtract(quantity.multiply(price).multiply(FEE_RATE));
        sellerBase.setTotalBalance(sellerBase.getTotalBalance().subtract(quantity));
        sellerBase.setAvailableBalance(sellerBase.getAvailableBalance().subtract(quantity));
        sellerBase.setUpdatedAt(OffsetDateTime.now());
        sellerQuote.setTotalBalance(sellerQuote.getTotalBalance().add(quoteReceived));
        sellerQuote.setAvailableBalance(sellerQuote.getAvailableBalance().add(quoteReceived));
        sellerQuote.setUpdatedAt(OffsetDateTime.now());
        sellerAccount.setTotalBalance(sellerAccount.getTotalBalance().add(quoteReceived));
        sellerAccount.setAvailableBalance(sellerAccount.getAvailableBalance().add(quoteReceived));
        sellerAccount.setUpdatedAt(OffsetDateTime.now());

        // Update seller's position
        Position sellerPosition = positionRepository.findAll().stream()
                .filter(p -> p.getAccount().getAccountId().equals(sellerAccount.getAccountId()) && p.getSymbol().equals(buyOrder.getSymbol()))
                .findFirst()
                .orElseGet(() -> {
                    Position p = new Position();
                    p.setUser(sellerAccount.getUser());
                    p.setAccount(sellerAccount);
                    p.setSymbol(buyOrder.getSymbol());
                    p.setUpdatedAt(OffsetDateTime.now());
                    return p;
                });
        sellerPosition.setQuantity(sellerPosition.getQuantity().subtract(quantity));
        sellerPosition.setAveragePrice(calculateAveragePrice(sellerPosition, quantity.negate(), price));
        sellerPosition.setUpdatedAt(OffsetDateTime.now());
        positionRepository.save(sellerPosition);

        // Save updated balances
        assetBalanceRepository.save(buyerBase);
        assetBalanceRepository.save(buyerQuote);
        assetBalanceRepository.save(sellerBase);
        assetBalanceRepository.save(sellerQuote);
        tradingAccountRepository.save(buyerAccount);
        tradingAccountRepository.save(sellerAccount);
    }
}