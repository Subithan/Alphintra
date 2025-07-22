package com.alphintra.trading_engine;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

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
    private ObjectMapper objectMapper;

    private static final String ORDER_TOPIC = "orders";
    private static final String ORDER_CACHE_PREFIX = "order:";

    @Transactional
    public OrderResponse createOrder(OrderRequest request) {
        // Validate user and account
        User user = userRepository.findById(request.getUserId())
                .orElseThrow(() -> new RuntimeException("User not found"));
        TradingAccount account = tradingAccountRepository.findById(request.getAccountId())
                .orElseThrow(() -> new RuntimeException("Account not found"));

        // Create order
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

        // Save order
        order = orderRepository.save(order);

        // Cache order in Redis as JSON
        try {
            String orderJson = objectMapper.writeValueAsString(order);
            redisTemplate.opsForValue().set(ORDER_CACHE_PREFIX + order.getOrderUuid(), orderJson);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Failed to serialize order to JSON", e);
        }

        // Publish to Kafka
        kafkaTemplate.send(ORDER_TOPIC, order.getOrderUuid().toString(), order.toString());

        // Trigger order matching
        orderMatchingService.matchOrder(order);

        return mapToResponse(order);
    }

    public OrderResponse getOrder(UUID orderUuid) {
        // Check Redis cache
        String cachedOrderJson = (String) redisTemplate.opsForValue().get(ORDER_CACHE_PREFIX + orderUuid);
        if (cachedOrderJson != null) {
            try {
                Order cachedOrder = objectMapper.readValue(cachedOrderJson, Order.class);
                return mapToResponse(cachedOrder);
            } catch (JsonProcessingException e) {
                throw new RuntimeException("Failed to deserialize order from JSON", e);
            }
        }

        // Fetch from database
        Order order = orderRepository.findByOrderUuid(orderUuid);
        if (order == null) {
            throw new RuntimeException("Order not found");
        }

        // Cache in Redis as JSON
        try {
            String orderJson = objectMapper.writeValueAsString(order);
            redisTemplate.opsForValue().set(ORDER_CACHE_PREFIX + orderUuid, orderJson);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Failed to serialize order to JSON", e);
        }

        return mapToResponse(order);
    }

    private OrderResponse mapToResponse(Order order) {
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
}