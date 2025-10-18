package com.alphintra.trading_engine.service;

import com.alphintra.trading_engine.dto.TradeOrderDTO;
import com.alphintra.trading_engine.model.TradeOrder;
import com.alphintra.trading_engine.model.TradingBot;
import com.alphintra.trading_engine.repository.TradeOrderRepository;
import com.alphintra.trading_engine.repository.TradingBotRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class TradeHistoryService {

    private final TradeOrderRepository tradeOrderRepository;
    private final TradingBotRepository tradingBotRepository;

    // default: return latest N orders (limit param optional)
    public List<TradeOrderDTO> getRecentTrades(int limit) {
        List<TradeOrder> all = tradeOrderRepository.findAllByOrderByCreatedAtDesc();
        return all.stream()
            .limit(Math.max(0, limit))
            .map(this::toDto)
            .collect(Collectors.toList());
    }

    public List<TradeOrderDTO> getRecentTrades() {
        return getRecentTrades(100);
    }

    public List<TradeOrderDTO> getTradesByUser(String userId, int limit) {
        // Get all bots for this user
        List<TradingBot> userBots = tradingBotRepository.findByUserId(Long.parseLong(userId));
        List<Long> botIds = userBots.stream().map(TradingBot::getId).collect(Collectors.toList());
        
        if (botIds.isEmpty()) {
            return List.of();
        }
        
        // Get trades for user's bots
        List<TradeOrder> trades = tradeOrderRepository.findByBotIdInOrderByCreatedAtDesc(botIds);
        return trades.stream()
            .limit(Math.max(0, limit))
            .map(this::toDto)
            .collect(Collectors.toList());
    }

    public List<TradeOrderDTO> getTradesByUser(String userId) {
        return getTradesByUser(userId, 100);
    }

    private TradeOrderDTO toDto(TradeOrder o) {
        return new TradeOrderDTO(
            o.getId(),
            o.getBotId(),
            o.getExchangeOrderId(),
            o.getSymbol(),
            o.getType(),
            o.getSide(),
            o.getPrice(),
            o.getAmount(),
            o.getStatus(),
            o.getCreatedAt()
        );
    }
}