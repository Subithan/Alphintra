package com.alphintra.trading_engine.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class MarketDataService {

    private final RestTemplate restTemplate = new RestTemplate();
    
    /**
     * Fetch current market price from Binance API
     * @param symbol Trading pair symbol (e.g., "BTC/USDT")
     * @return Current market price
     */
    public BigDecimal getCurrentPrice(String symbol) {
        try {
            // Convert symbol format: BTC/USDT -> BTCUSDT
            String binanceSymbol = symbol.replace("/", "");
            
            String url = "https://api.binance.com/api/v3/ticker/price?symbol=" + binanceSymbol;
            log.debug("Fetching price for {} from Binance: {}", symbol, url);
            
            BinancePriceResponse response = restTemplate.getForObject(url, BinancePriceResponse.class);
            
            if (response != null && response.getPrice() != null) {
                BigDecimal price = new BigDecimal(response.getPrice());
                log.debug("Got price for {}: {}", symbol, price);
                return price;
            }
            
            log.warn("No price data returned for symbol: {}", symbol);
            return null;
            
        } catch (Exception e) {
            log.error("Error fetching price for symbol {}: {}", symbol, e.getMessage());
            return null;
        }
    }
    
    /**
     * Fetch current market prices for multiple symbols
     * @param symbols List of trading pair symbols
     * @return Map of symbol to current price
     */
    public Map<String, BigDecimal> getCurrentPrices(List<String> symbols) {
        Map<String, BigDecimal> prices = new HashMap<>();
        
        for (String symbol : symbols) {
            BigDecimal price = getCurrentPrice(symbol);
            if (price != null) {
                prices.put(symbol, price);
            }
        }
        
        log.info("Fetched prices for {} symbols", prices.size());
        return prices;
    }
    
    /**
     * Calculate PNL for a position based on current market price
     * @param entryPrice Entry price of the position
     * @param currentPrice Current market price
     * @param quantity Quantity held
     * @return Calculated PNL
     */
    public BigDecimal calculatePnL(BigDecimal entryPrice, BigDecimal currentPrice, BigDecimal quantity) {
        if (entryPrice == null || currentPrice == null || quantity == null) {
            return BigDecimal.ZERO;
        }
        
        // PNL = (Current Price - Entry Price) * Quantity
        BigDecimal priceDiff = currentPrice.subtract(entryPrice);
        return priceDiff.multiply(quantity);
    }
    
    /**
     * Calculate PNL percentage
     * @param entryPrice Entry price of the position
     * @param currentPrice Current market price
     * @return PNL percentage
     */
    public BigDecimal calculatePnLPercentage(BigDecimal entryPrice, BigDecimal currentPrice) {
        if (entryPrice == null || currentPrice == null || entryPrice.compareTo(BigDecimal.ZERO) == 0) {
            return BigDecimal.ZERO;
        }
        
        // PNL % = ((Current Price - Entry Price) / Entry Price) * 100
        BigDecimal priceDiff = currentPrice.subtract(entryPrice);
        return priceDiff.divide(entryPrice, 4, RoundingMode.HALF_UP)
                        .multiply(new BigDecimal("100"));
    }
    
    /**
     * Inner class to map Binance API response
     */
    private static class BinancePriceResponse {
        private String symbol;
        private String price;
        
        public String getSymbol() {
            return symbol;
        }
        
        public void setSymbol(String symbol) {
            this.symbol = symbol;
        }
        
        public String getPrice() {
            return price;
        }
        
        public void setPrice(String price) {
            this.price = price;
        }
    }
}
