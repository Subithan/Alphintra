package com.alphintra.trading_engine.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.math.BigDecimal;

@Entity
@Table(name = "positions")
@Data
@NoArgsConstructor
public class Position {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private Long userId;

    @Column(nullable = false)
    private String asset; // e.g., "BTC"

    @Column(nullable = false, precision = 19, scale = 8)
    private BigDecimal quantity;

    @Column(precision = 19, scale = 8)
    private BigDecimal averageEntryPrice;
}