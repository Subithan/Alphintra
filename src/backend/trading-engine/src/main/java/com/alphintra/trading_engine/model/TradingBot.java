package com.alphintra.trading_engine.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Entity
@Table(name = "trading_bots")
@Data
@NoArgsConstructor
public class TradingBot {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private Long userId;

    @Column(nullable = false)
    private Long strategyId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private BotStatus status;

    @Column(nullable = false)
    private String symbol; // e.g., "BTC/USDT"

    private LocalDateTime startedAt;

    private LocalDateTime stoppedAt;
}