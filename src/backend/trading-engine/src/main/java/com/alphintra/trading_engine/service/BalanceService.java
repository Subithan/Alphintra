package com.alphintra.trading_engine.service;

import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.math.BigDecimal;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class BalanceService {

    private final BinanceTimeService binanceTimeService;

    public Map<String, BigDecimal> getAccountBalance(Long userId) {
        // Use hardcoded testnet credentials for testing
        System.out.println("🔧 Using Binance TESTNET API credentials for balance check.");
        WalletCredentialsDTO credentials = new WalletCredentialsDTO(
            "HCwZWzdNFNVj6jYlunDyqh1tFScpTnxktaPLGDkZDaorhhQRoq5LGFReqQYN8Fbi",
            "1hbOBVTw20W1tOFSdXgn1VZBtQ8DWzrwC4w5p4CnfUDnGH5aRyhP7Ys6KOFuDzoq"
        );
        return fetchAccountBalanceDirectAPI(credentials);
    }

    private Map<String, BigDecimal> fetchAccountBalanceDirectAPI(WalletCredentialsDTO credentials) {
        Map<String, BigDecimal> balances = new HashMap<>();

        try {
            long serverTime = binanceTimeService.getServerTime();
            long recvWindow = 60000;

            String queryString = "timestamp=" + serverTime + "&recvWindow=" + recvWindow;
            String signature = generateSignature(queryString, credentials.secretKey());
            String urlWithParams = "https://testnet.binance.vision/api/v3/account?" + queryString + "&signature=" + signature;

            HttpClient client = HttpClient.newBuilder()
                    .connectTimeout(java.time.Duration.ofSeconds(10))
                    .build();

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(urlWithParams))
                    .header("X-MBX-APIKEY", credentials.apiKey())
                    .GET()
                    .build();

            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() == 200) {
                String responseBody = response.body();
                // Parse the JSON response to extract balances
                // For simplicity, we'll extract all non-zero balances
                balances = parseBalancesFromJson(responseBody);
                System.out.println("✅ Successfully fetched account balances");
            } else {
                System.err.println("❌ Direct API request for balance failed with status: " + response.statusCode() + " | Response: " + response.body());
            }
        } catch (Exception e) {
            System.err.println("❌ Error with direct API call for balance: " + e.getMessage());
            e.printStackTrace();
        }

        return balances;
    }

    private Map<String, BigDecimal> parseBalancesFromJson(String responseBody) {
        Map<String, BigDecimal> balances = new HashMap<>();
        
        try {
            // Simple JSON parsing to extract all balances
            int balancesStart = responseBody.indexOf("\"balances\":[");
            if (balancesStart == -1) return balances;
            
            String balancesSection = responseBody.substring(balancesStart);
            String[] assets = balancesSection.split("\\{\"asset\":\"");
            
            for (String assetData : assets) {
                if (assetData.contains("\"free\":\"")) {
                    int assetEnd = assetData.indexOf("\"", 0);
                    if (assetEnd == -1) continue;
                    
                    String asset = assetData.substring(0, assetEnd);
                    
                    int freeIndex = assetData.indexOf("\"free\":\"");
                    if (freeIndex == -1) continue;
                    
                    int freeStart = freeIndex + 8;
                    int freeEnd = assetData.indexOf("\"", freeStart);
                    if (freeEnd == -1) continue;
                    
                    String freeAmount = assetData.substring(freeStart, freeEnd);
                    BigDecimal amount = new BigDecimal(freeAmount);
                    
                    // Only include non-zero balances
                    if (amount.compareTo(BigDecimal.ZERO) > 0) {
                        balances.put(asset, amount);
                    }
                }
            }
        } catch (Exception e) {
            System.err.println("❌ Error parsing balances from JSON: " + e.getMessage());
        }
        
        return balances;
    }

    private String generateSignature(String data, String secretKey) {
        try {
            Mac sha256_HMAC = Mac.getInstance("HmacSHA256");
            SecretKeySpec secret_key = new SecretKeySpec(secretKey.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
            sha256_HMAC.init(secret_key);
            byte[] hash = sha256_HMAC.doFinal(data.getBytes(StandardCharsets.UTF_8));
            StringBuilder hexString = new StringBuilder();
            for (byte b : hash) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) hexString.append('0');
                hexString.append(hex);
            }
            return hexString.toString();
        } catch (Exception e) {
            throw new RuntimeException("Error generating signature", e);
        }
    }
}
