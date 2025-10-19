package com.alphintra.trading_engine.config;

import com.alphintra.trading_engine.service.BinanceTimeService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@RequiredArgsConstructor
public class BinanceStartupValidator {

    private final BinanceTimeService binanceTimeService;

    @Value("${binance.api.enabled:true}")
    private boolean binanceApiEnabled;

    @Bean
    ApplicationRunner binanceConnectivityGuard() {
        return args -> {
            if (!binanceApiEnabled) {
                System.out.println("⏭️ Binance API disabled; skipping connectivity check.");
                return;
            }
            System.out.println("🔎 Verifying Binance connectivity at startup...");
            binanceTimeService.assertConnectivity();
            System.out.println("✅ Binance connectivity verified.");
        };
    }
}

