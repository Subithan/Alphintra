package com.alphintra.trading_engine.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "user_balances")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserBalance {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "user_id", nullable = false)
    private Long userId;
    
    @Column(nullable = false, length = 20)
    private String asset;
    
    @Column(nullable = false, precision = 20, scale = 8)
    private BigDecimal free = BigDecimal.ZERO;
    
    @Column(nullable = false, precision = 20, scale = 8)
    private BigDecimal locked = BigDecimal.ZERO;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }
    
    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
    
    // Computed field for total balance
    @Transient
    public BigDecimal getTotal() {
        return free.add(locked);
    }
}
