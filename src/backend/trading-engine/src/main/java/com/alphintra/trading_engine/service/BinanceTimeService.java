package com.alphintra.trading_engine.service;

import org.json.JSONObject;
import org.springframework.stereotype.Service;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

@Service
public class BinanceTimeService {

    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();

    /**
     * Fetches the official server time from the Binance API.
     * This is crucial for synchronizing requests and avoiding timestamp-related errors.
     * @return The server time in milliseconds since epoch.
     */
    public long getServerTime() {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create("https://testnet.binance.vision/api/v3/time"))
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
}

