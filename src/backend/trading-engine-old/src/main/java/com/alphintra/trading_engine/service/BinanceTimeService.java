package com.alphintra.trading_engine.service;

import lombok.RequiredArgsConstructor;
import org.json.JSONObject;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

@Service
@RequiredArgsConstructor
public class BinanceTimeService {

    private final HttpClient httpClient;

    @Value("${binance.api.enabled:true}")
    private boolean binanceApiEnabled;

    @Value("${binance.api.testnet.enabled:true}")
    private boolean binanceTestnetEnabled;

    private String baseUrl() {
        return binanceTestnetEnabled ? "https://testnet.binance.vision" : "https://api.binance.com";
    }

    /**
     * Fetches the official server time from the Binance API.
     * This is crucial for synchronizing requests and avoiding timestamp-related errors.
     * @return The server time in milliseconds since epoch.
     */
    public long getServerTime() {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl() + "/api/v3/time"))
                    .GET()
                    .build();
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() == 200) {
                JSONObject json = new JSONObject(response.body());
                return json.getLong("serverTime");
            }
        } catch (Exception e) {
            System.err.println("⚠️ Could not fetch Binance server time, falling back to local system time. Error: " + e.getMessage());
        }
        // Fallback to local time if the API call fails
        return System.currentTimeMillis();
    }

    /**
     * Strict connectivity check: throws if Binance API is unreachable or returns non-200.
     */
    public void assertConnectivity() {
        if (!binanceApiEnabled) {
            // If disabled, do not enforce connectivity
            return;
        }
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl() + "/api/v3/ping"))
                    .timeout(Duration.ofSeconds(10))
                    .GET()
                    .build();
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() != 200) {
                throw new IllegalStateException("Binance /ping failed with status " + response.statusCode());
            }
        } catch (Exception e) {
            throw new IllegalStateException("Binance connectivity check failed: " + e.getMessage(), e);
        }
    }
}
