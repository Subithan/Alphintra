package com.alphintra.trading_engine.dto;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

/**
 * Mock chart data for UI testing
 */
public record MockChartDataDTO(
    String symbol,
    String interval,
    List<CandleData> candles,
    List<TradeMarker> trades
) {
    public record CandleData(
        LocalDateTime time,
        BigDecimal open,
        BigDecimal high,
        BigDecimal low,
        BigDecimal close,
        BigDecimal volume
    ) {}
    
    public record TradeMarker(
        LocalDateTime time,
        BigDecimal price,
        String type,
        String side
    ) {}
}
