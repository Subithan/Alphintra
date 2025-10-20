package com.alphintra.trading_engine.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "trade_orders")
@Data
@NoArgsConstructor
public class TradeOrder {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long botId;

    private String exchangeOrderId;

    @Column(nullable = false)
    private String symbol;

    @Column(nullable = false)
    private String type; // e.g., "LIMIT", "MARKET"

    @Column(nullable = false)
    private String side; // e.g., "BUY", "SELL"

    @Column(precision = 19, scale = 8)
    private BigDecimal price;

    @Column(precision = 19, scale = 8)
    private BigDecimal amount;

    private String status; // e.g., "OPEN", "FILLED", "CANCELED"

    @Column(name = "pending_order_id")
    private Long pendingOrderId; // Reference to pending order if this was a triggered exit

    @Column(name = "exit_reason")
    private String exitReason; // "TAKE_PROFIT", "STOP_LOSS", "MANUAL"

    @Column(nullable = false)
    private LocalDateTime createdAt;
}