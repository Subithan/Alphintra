package com.alphintra.trading_engine;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

@RestController
@RequestMapping("/api/trades")
public class TradeController {

    @Autowired
    private TradeRepository tradeRepository;

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    private static final String TRADE_CACHE_PREFIX = "trade:";

    @GetMapping("/{tradeUuid}")
    public ResponseEntity<TradeResponse> getTrade(@PathVariable UUID tradeUuid) {
        // Check Redis cache
        String cachedTradeJson = (String) redisTemplate.opsForValue().get(TRADE_CACHE_PREFIX + tradeUuid);
        if (cachedTradeJson != null) {
            try {
                Trade cachedTrade = objectMapper.readValue(cachedTradeJson, Trade.class);
                return ResponseEntity.ok(mapToResponse(cachedTrade));
            } catch (JsonProcessingException e) {
                throw new RuntimeException("Failed to deserialize trade from JSON", e);
            }
        }

        // Fetch from database
        Trade trade = tradeRepository.findByTradeUuid(tradeUuid);
        if (trade == null) {
            throw new RuntimeException("Trade not found");
        }

        // Cache in Redis as JSON
        try {
            String tradeJson = objectMapper.writeValueAsString(trade);
            redisTemplate.opsForValue().set(TRADE_CACHE_PREFIX + tradeUuid, tradeJson);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Failed to serialize trade to JSON", e);
        }

        return ResponseEntity.ok(mapToResponse(trade));
    }

    private TradeResponse mapToResponse(Trade trade) {
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