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

    @Enumerated(EnumType.STRING)
    private PositionStatus status;
}