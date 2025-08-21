package com.alphintra.trading_engine;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.OffsetDateTime;

@Entity
@Table(name = "asset_balances", uniqueConstraints = @UniqueConstraint(columnNames = {"account_id", "asset"}))
public class AssetBalance {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long balanceId;

    @ManyToOne
    @JoinColumn(name = "account_id", nullable = false)
    private TradingAccount account;

    @Column(nullable = false)
    private String asset;

    @Column(nullable = false)
    private BigDecimal totalBalance = BigDecimal.ZERO;

    @Column(nullable = false)
    private BigDecimal availableBalance = BigDecimal.ZERO;

    @Column(nullable = false)
    private BigDecimal lockedBalance = BigDecimal.ZERO;

    @Column(nullable = false)
    private OffsetDateTime updatedAt = OffsetDateTime.now();

    // Getters and Setters
    public Long getBalanceId() { return balanceId; }
    public void setBalanceId(Long balanceId) { this.balanceId = balanceId; }
    public TradingAccount getAccount() { return account; }
    public void setAccount(TradingAccount account) { this.account = account; }
    public String getAsset() { return asset; }
    public void setAsset(String asset) { this.asset = asset; }
    public BigDecimal getTotalBalance() { return totalBalance; }
    public void setTotalBalance(BigDecimal totalBalance) { this.totalBalance = totalBalance; }
    public BigDecimal getAvailableBalance() { return availableBalance; }
    public void setAvailableBalance(BigDecimal availableBalance) { this.availableBalance = availableBalance; }
    public BigDecimal getLockedBalance() { return lockedBalance; }
    public void setLockedBalance(BigDecimal lockedBalance) { this.lockedBalance = lockedBalance; }
    public OffsetDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(OffsetDateTime updatedAt) { this.updatedAt = updatedAt; }
}