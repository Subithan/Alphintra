package com.alphintra.trading_engine.client;

import com.alphintra.trading_engine.dto.CoinbaseBalanceDTO;
import com.alphintra.trading_engine.dto.CoinbaseBalancesResponse;
import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Component
@RequiredArgsConstructor
public class WalletServiceClient {

    private final RestTemplate restTemplate;

    @Value("${services.wallet.url}")
    private String walletServiceUrl;

    public WalletCredentialsDTO getCredentials(Long userId) {
        String url = walletServiceUrl + "/coinbase/credentials?userId=" + userId;

        System.out.println("🔐 Requesting Coinbase credentials from wallet-service at: " + url);

        try {
            WalletCredentialsDTO credentials = restTemplate.getForObject(url, WalletCredentialsDTO.class);

            if (credentials == null || credentials.apiKey() == null || credentials.secretKey() == null) {
                throw new RuntimeException("Received null or incomplete Coinbase credentials from wallet service.");
            }

            String apiKey = credentials.apiKey();
            System.out.println("✅ Successfully fetched Coinbase credentials for userId " + userId);
            System.out.println("   API Key prefix: " + apiKey.substring(0, Math.min(apiKey.length(), 5)) + "...");

            return credentials;

        } catch (Exception e) {
            System.err.println("❌ ERROR: Failed to fetch Coinbase credentials for userId " + userId);
            throw new RuntimeException("Could not fetch Coinbase credentials from wallet service.", e);
        }
    }

    public Map<String, BigDecimal> getCoinbaseBalances(Long userId) {
        String url = walletServiceUrl + "/coinbase/balances?userId=" + userId;
        System.out.println("💳 Requesting Coinbase balances from wallet-service at: " + url);

        try {
            CoinbaseBalancesResponse response = restTemplate.getForObject(url, CoinbaseBalancesResponse.class);
            if (response == null) {
                throw new RuntimeException("Wallet service returned null response while fetching balances.");
            }

            List<CoinbaseBalanceDTO> balances = response.balances();
            Map<String, BigDecimal> parsedBalances = new HashMap<>();

            if (balances != null) {
                for (CoinbaseBalanceDTO balance : balances) {
                    if (balance == null || balance.asset() == null) {
                        continue;
                    }

                    try {
                        String freeValue = balance.free();
                        if (freeValue == null || freeValue.isBlank()) {
                            parsedBalances.put(balance.asset().toUpperCase(), BigDecimal.ZERO);
                        } else {
                            BigDecimal freeAmount = new BigDecimal(freeValue);
                            parsedBalances.put(balance.asset().toUpperCase(), freeAmount);
                        }
                    } catch (Exception numberFormatException) {
                        System.err.println("⚠️ Unable to parse balance for asset " + balance.asset() + ": " + numberFormatException.getMessage());
                    }
                }
            }

            return parsedBalances;
        } catch (Exception e) {
            System.err.println("❌ ERROR: Failed to fetch Coinbase balances for userId " + userId + ": " + e.getMessage());
            throw new RuntimeException("Could not fetch Coinbase balances from wallet service.", e);
        }
    }
}