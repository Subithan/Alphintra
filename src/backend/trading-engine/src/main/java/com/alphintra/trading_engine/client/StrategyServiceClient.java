package com.alphintra.trading_engine.client;

import com.alphintra.trading_engine.dto.StrategyDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@Component
@RequiredArgsConstructor
public class StrategyServiceClient {
    
    private final RestTemplate restTemplate;

    @Value("${services.strategy.url}")
    private String strategyServiceUrl;

    public StrategyDTO getStrategy(Long strategyId) {
        String url = strategyServiceUrl + "/api/strategies/" + strategyId;

        try {
            // Uncomment when the strategy service endpoint is ready.
            // return restTemplate.getForObject(url, StrategyDTO.class);
            
            // --- TEMPORARY WORKAROUND for development ---
            System.out.println("⚠️ WARN: Using placeholder strategy data.");
            return new StrategyDTO(strategyId, "Simple RSI", "BTC/USDT",
                    Map.of("rsiPeriod", "14", "buyThreshold", "30", "sellThreshold", "70"));
            // --- END OF TEMPORARY WORKAROUND ---

        } catch (Exception e) {
            throw new RuntimeException("Failed to fetch strategy from strategy service at " + url, e);
        }
    }
}