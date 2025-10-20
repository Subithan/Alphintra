package com.alphintra.trading_engine.model;

import jakarta.persistence.*;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "pending_orders")
@Data
public class PendingOrder {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "position_id", nullable = false)
    private Long positionId;

    @Column(name = "take_profit_price", precision = 18, scale = 8)
    private BigDecimal takeProfitPrice;

    @Column(name = "stop_loss_price", precision = 18, scale = 8)
    private BigDecimal stopLossPrice;

    @Column(name = "quantity", nullable = false, precision = 18, scale = 8)
    private BigDecimal quantity;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private PendingOrderStatus status;

    @Column(name = "symbol", nullable = false)
    private String symbol;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "triggered_at")
    private LocalDateTime triggeredAt;

    @Column(name = "triggered_type")
    private String triggeredType; // "TAKE_PROFIT" or "STOP_LOSS"

    @Column(name = "cancelled_at")
    private LocalDateTime cancelledAt;

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = LocalDateTime.now();
        }
        if (status == null) {
            status = PendingOrderStatus.PENDING;
        }
    }
}
