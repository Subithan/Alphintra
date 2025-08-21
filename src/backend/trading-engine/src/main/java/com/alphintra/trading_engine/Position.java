package com.alphintra.trading_engine;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.OffsetDateTime;

@Entity
@Table(name = "positions", uniqueConstraints = @UniqueConstraint(columnNames = {"user_id", "account_id", "symbol"}))
public class Position {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long positionId;

    @ManyToOne
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne
    @JoinColumn(name = "account_id", nullable = false)
    private TradingAccount account;

    @Column(nullable = false)
    private String symbol;

    @Column(nullable = false)
    private BigDecimal quantity = BigDecimal.ZERO;

    private BigDecimal averagePrice;

    private BigDecimal marketValue;

    @Column(nullable = false)
    private BigDecimal unrealizedPnl = BigDecimal.ZERO;

    @Column(nullable = false)
    private BigDecimal realizedPnl = BigDecimal.ZERO;

    @Column(nullable = false)
    private OffsetDateTime updatedAt = OffsetDateTime.now();

    // Getters and Setters
    public Long getPositionId() { return positionId; }
    public void setPositionId(Long positionId) { this.positionId = positionId; }
    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }
    public TradingAccount getAccount() { return account; }
    public void setAccount(TradingAccount account) { this.account = account; }
    public String getSymbol() { return symbol; }
    public void setSymbol(String symbol) { this.symbol = symbol; }
    public BigDecimal getQuantity() { return quantity; }
    public void setQuantity(BigDecimal quantity) { this.quantity = quantity; }
    public BigDecimal getAveragePrice() { return averagePrice; }
    public void setAveragePrice(BigDecimal averagePrice) { this.averagePrice = averagePrice; }
    public BigDecimal getMarketValue() { return marketValue; }
    public void setMarketValue(BigDecimal marketValue) { this.marketValue = marketValue; }
    public BigDecimal getUnrealizedPnl() { return unrealizedPnl; }
    public void setUnrealizedPnl(BigDecimal unrealizedPnl) { this.unrealizedPnl = unrealizedPnl; }
    public BigDecimal getRealizedPnl() { return realizedPnl; }
    public void setRealizedPnl(BigDecimal realizedPnl) { this.realizedPnl = realizedPnl; }
    public OffsetDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(OffsetDateTime updatedAt) { this.updatedAt = updatedAt; }
}