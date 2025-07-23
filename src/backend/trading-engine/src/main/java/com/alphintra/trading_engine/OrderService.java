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
import java.util.stream.Collectors;

@Service
public class OrderService {

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private TradingAccountRepository tradingAccountRepository;

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    @Autowired
    private OrderMatchingService orderMatchingService;

    @Autowired
    private TradeRepository tradeRepository;

    @Autowired
    private ObjectMapper objectMapper;

    private static final String ORDER_TOPIC = "orders";
    private static final String ORDER_CACHE_PREFIX = "order:";

    @Transactional
    public OrderResponse createOrder(OrderRequest request) {
        User user = userRepository.findById(request.getUserId())
                .orElseThrow(() -> new RuntimeException("User not found"));
        TradingAccount account = tradingAccountRepository.findById(request.getAccountId())
                .orElseThrow(() -> new RuntimeException("Account not found"));

        Order order = new Order();
        order.setOrderUuid(UUID.randomUUID());
        order.setUser(user);
        order.setAccount(account);
        order.setSymbol(request.getSymbol());
        order.setSide(request.getSide());
        order.setOrderType(request.getOrderType());
        order.setQuantity(request.getQuantity());
        order.setPrice(request.getPrice());
        order.setStopPrice(request.getStopPrice());
        order.setTimeInForce(request.getTimeInForce());
        order.setClientOrderId(request.getClientOrderId());

        order = orderRepository.save(order);

        try {
            String orderJson = objectMapper.writeValueAsString(order);
            redisTemplate.opsForValue().set(ORDER_CACHE_PREFIX + order.getOrderUuid(), orderJson);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Failed to serialize order to JSON", e);
        }

        // Temporarily bypass Kafka (as suggested earlier)
        // kafkaTemplate.send(ORDER_TOPIC, order.getOrderUuid().toString(), order.toString());
        orderMatchingService.matchOrder(order);

        return mapToResponse(order);
    }

    public OrderResponse getOrder(UUID orderUuid) {
        String cachedOrderJson = (String) redisTemplate.opsForValue().get(ORDER_CACHE_PREFIX + orderUuid);
        if (cachedOrderJson != null) {
            try {
                Order cachedOrder = objectMapper.readValue(cachedOrderJson, Order.class);
                return mapToResponse(cachedOrder);
            } catch (JsonProcessingException e) {
                throw new RuntimeException("Failed to deserialize order from JSON", e);
            }
        }

        Order order = orderRepository.findByOrderUuid(orderUuid);
        if (order == null) {
            throw new RuntimeException("Order not found");
        }

        try {
            String orderJson = objectMapper.writeValueAsString(order);
            redisTemplate.opsForValue().set(ORDER_CACHE_PREFIX + orderUuid, orderJson);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Failed to serialize order to JSON", e);
        }

        return mapToResponse(order);
    }

    public List<TradeResponse> getTradeHistory() {
        return tradeRepository.findAll().stream()
                .map(this::mapToTradeResponse)
                .collect(Collectors.toList());
    }

    // Add this method
    public List<Order> getAllOrders() {
        return orderRepository.findAll();
    }

    public OrderResponse mapToResponse(Order order) {
        OrderResponse response = new OrderResponse();
        response.setOrderId(order.getOrderId());
        response.setOrderUuid(order.getOrderUuid());
        response.setUserId(order.getUser().getUserId());
        response.setAccountId(order.getAccount().getAccountId());
        response.setSymbol(order.getSymbol());
        response.setSide(order.getSide());
        response.setOrderType(order.getOrderType());
        response.setQuantity(order.getQuantity());
        response.setPrice(order.getPrice());
        response.setStopPrice(order.getStopPrice());
        response.setTimeInForce(order.getTimeInForce());
        response.setStatus(order.getStatus());
        response.setFilledQuantity(order.getFilledQuantity());
        response.setAveragePrice(order.getAveragePrice());
        response.setFee(order.getFee());
        response.setExchange(order.getExchange());
        response.setClientOrderId(order.getClientOrderId());
        response.setExchangeOrderId(order.getExchangeOrderId());
        response.setCreatedAt(order.getCreatedAt());
        response.setUpdatedAt(order.getUpdatedAt());
        response.setExpiresAt(order.getExpiresAt());
        return response;
    }

    private TradeResponse mapToTradeResponse(Trade trade) {
        TradeResponse response = new TradeResponse();
        response.setTradeId(trade.getTradeId());
        response.setTradeUuid(trade.getTradeUuid());
        response.setOrderId(trade.getOrder().getOrderId());
        response.setUserId(trade.getUser().getUserId());
        response.setAccountId(trade.getAccount().getAccountId());
        response.setSymbol(trade.getSymbol());
        response.setSide(trade.getSide());
        response.setQuantity(trade.getQuantity());
        response.setPrice(trade.getPrice());
        response.setFee(trade.getFee());
        response.setExchange(trade.getExchange());
        response.setTradeType(trade.getTradeType());
        response.setTimestamp(trade.getTimestamp());
        return response;
    }
}