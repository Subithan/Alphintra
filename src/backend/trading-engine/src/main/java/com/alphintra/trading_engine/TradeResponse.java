package com.alphintra.trading_engine;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.UUID;

public class TradeResponse {
    private Long tradeId;
    private UUID tradeUuid;
    private Long orderId;
    private Long userId;
    private Long accountId;
    private String symbol;
    private String side;
    private BigDecimal quantity;
    private BigDecimal price;
    private BigDecimal fee;
    private String exchange;
    private String tradeType;
    private OffsetDateTime timestamp;

    // Getters and Setters
    public Long getTradeId() { return tradeId; }
    public void setTradeId(Long tradeId) { this.tradeId = tradeId; }
    public UUID getTradeUuid() { return tradeUuid; }
    public void setTradeUuid(UUID tradeUuid) { this.tradeUuid = tradeUuid; }
    public Long getOrderId() { return orderId; }
    public void setOrderId(Long orderId) { this.orderId = orderId; }
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public Long getAccountId() { return accountId; }
    public void setAccountId(Long accountId) { this.accountId = accountId; }
    public String getSymbol() { return symbol; }
    public void setSymbol(String symbol) { this.symbol = symbol; }
    public String getSide() { return side; }
    public void setSide(String side) { this.side = side; }
    public BigDecimal getQuantity() { return quantity; }
    public void setQuantity(BigDecimal quantity) { this.quantity = quantity; }
    public BigDecimal getPrice() { return price; }
    public void setPrice(BigDecimal price) { this.price = price; }
    public BigDecimal getFee() { return fee; }
    public void setFee(BigDecimal fee) { this.fee = fee; }
    public String getExchange() { return exchange; }
    public void setExchange(String exchange) { this.exchange = exchange; }
    public String getTradeType() { return tradeType; }
    public void setTradeType(String tradeType) { this.tradeType = tradeType; }
    public OffsetDateTime getTimestamp() { return timestamp; }
    public void setTimestamp(OffsetDateTime timestamp) { this.timestamp = timestamp; }
}