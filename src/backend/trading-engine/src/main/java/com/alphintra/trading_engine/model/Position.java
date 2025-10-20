package com.alphintra.trading_engine.model;

import jakarta.persistence.*;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "positions")
@Data
public class Position {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private Long userId;
    private Long botId;
    private String asset;
    private String symbol;
    private BigDecimal entryPrice;
    private BigDecimal quantity;
    private LocalDateTime openedAt;
    private LocalDateTime closedAt;
    
    @Column(name = "exit_price", precision = 18, scale = 8)
    private BigDecimal exitPrice;
    
    @Column(name = "pnl", precision = 18, scale = 8)
    private BigDecimal pnl; // Profit and Loss in quote currency

    @Enumerated(EnumType.STRING)
    private PositionStatus status;
}