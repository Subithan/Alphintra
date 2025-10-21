package com.alphintra.trading_engine.service;

import com.alphintra.trading_engine.dto.PositionWithPnLDTO;
import com.alphintra.trading_engine.model.Position;
import com.alphintra.trading_engine.model.PositionStatus;
import com.alphintra.trading_engine.repository.PositionRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class PositionService {

    private final PositionRepository positionRepository;
    private final MarketDataService marketDataService;

    /**
     * Get positions with real-time PNL calculation
     */
    public List<PositionWithPnLDTO> getPositionsWithPnL(Long userId, PositionStatus status) {
        log.info("Fetching positions with PNL for user: {}, status: {}", userId, status);
        
        // Fetch positions from database
        List<Position> positions;
        if (userId != null && status != null) {
            positions = positionRepository.findByUserIdAndStatus(userId, status);
        } else if (userId != null) {
            positions = positionRepository.findByUserId(userId);
        } else if (status != null) {
            positions = positionRepository.findByStatus(status);
        } else {
            positions = positionRepository.findAll();
        }
        
        if (positions.isEmpty()) {
            log.info("No positions found");
            return List.of();
        }
        
        // Extract unique symbols
        List<String> symbols = positions.stream()
                .map(Position::getSymbol)
                .distinct()
                .collect(Collectors.toList());
        
        log.info("Fetching prices for {} unique symbols: {}", symbols.size(), symbols);
        
        // Fetch current market prices
        Map<String, BigDecimal> currentPrices = marketDataService.getCurrentPrices(symbols);
        
        log.info("Got prices for {} symbols", currentPrices.size());
        
        // Convert to DTOs with PNL calculation
        return positions.stream()
                .map(position -> convertToDTO(position, currentPrices.get(position.getSymbol())))
                .collect(Collectors.toList());
    }
    
    /**
     * Convert Position entity to PositionWithPnLDTO with PNL calculation
     */
    private PositionWithPnLDTO convertToDTO(Position position, BigDecimal currentPrice) {
        PositionWithPnLDTO dto = new PositionWithPnLDTO();
        
        // Copy basic fields
        dto.setId(position.getId());
        dto.setUserId(position.getUserId());
        dto.setBotId(position.getBotId());
        dto.setAsset(position.getAsset());
        dto.setSymbol(position.getSymbol());
        dto.setEntryPrice(position.getEntryPrice());
        dto.setQuantity(position.getQuantity());
        dto.setOpenedAt(position.getOpenedAt());
        dto.setClosedAt(position.getClosedAt());
        dto.setExitPrice(position.getExitPrice());
        dto.setStatus(position.getStatus());
        
        // Set current price
        dto.setCurrentPrice(currentPrice);
        
        // Calculate PNL if we have current price
        if (currentPrice != null && position.getEntryPrice() != null && position.getQuantity() != null) {
            BigDecimal calculatedPnl = marketDataService.calculatePnL(
                position.getEntryPrice(), 
                currentPrice, 
                position.getQuantity()
            );
            dto.setCalculatedPnl(calculatedPnl);
            
            BigDecimal pnlPercentage = marketDataService.calculatePnLPercentage(
                position.getEntryPrice(), 
                currentPrice
            );
            dto.setPnlPercentage(pnlPercentage);
            
            log.debug("Position {}: Entry={}, Current={}, Quantity={}, PNL={}, PNL%={}", 
                position.getId(), 
                position.getEntryPrice(), 
                currentPrice, 
                position.getQuantity(),
                calculatedPnl,
                pnlPercentage);
        } else {
            // Use stored PNL if current price not available
            dto.setCalculatedPnl(position.getPnl() != null ? position.getPnl() : BigDecimal.ZERO);
            dto.setPnlPercentage(BigDecimal.ZERO);
            
            log.warn("Could not calculate PNL for position {} - missing data", position.getId());
        }
        
        return dto;
    }
}
