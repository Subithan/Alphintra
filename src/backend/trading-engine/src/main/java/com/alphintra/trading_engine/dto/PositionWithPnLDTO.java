package com.alphintra.trading_engine.dto;

import com.alphintra.trading_engine.model.PositionStatus;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class PositionWithPnLDTO {
    private Long id;
    private Long userId;
    private Long botId;
    private String asset;
    private String symbol;
    private BigDecimal entryPrice;
    private BigDecimal quantity;
    private LocalDateTime openedAt;
    private LocalDateTime closedAt;
    private BigDecimal exitPrice;
    private PositionStatus status;
    
    // Real-time calculated fields
    private BigDecimal currentPrice;
    private BigDecimal calculatedPnl;
    private BigDecimal pnlPercentage;
}
