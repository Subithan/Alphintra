package com.alphintra.trading_engine.client;

import com.alphintra.trading_engine.dto.CoinbaseBalanceDTO;
import com.alphintra.trading_engine.dto.CoinbaseBalancesResponse;
import com.alphintra.trading_engine.dto.CoinbaseMarketOrderResponseDTO;
import com.alphintra.trading_engine.dto.CoinbaseOrderDTO;
import com.alphintra.trading_engine.dto.CoinbasePositionDTO;
import com.alphintra.trading_engine.dto.CoinbaseTickerDTO;
import com.alphintra.trading_engine.dto.CoinbaseTradeDTO;
import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
import com.alphintra.trading_engine.exception.WalletServiceException;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.math.BigDecimal;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Component
@RequiredArgsConstructor
public class WalletServiceClient {

    private final RestTemplate restTemplate;

    @Value("${services.wallet.url}")
    private String walletServiceUrl;

    private static final ParameterizedTypeReference<List<CoinbaseOrderDTO>> OPEN_ORDERS_TYPE =
            new ParameterizedTypeReference<>() {};

    private static final ParameterizedTypeReference<List<CoinbasePositionDTO>> POSITIONS_TYPE =
            new ParameterizedTypeReference<>() {};

    private static final ParameterizedTypeReference<List<CoinbaseTradeDTO>> TRADES_TYPE =
            new ParameterizedTypeReference<>() {};

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
            System.err.println("❌ Exception type: " + e.getClass().getSimpleName());
            System.err.println("❌ Exception message: " + e.getMessage());
            e.printStackTrace();
            throw new WalletServiceException("Could not fetch Coinbase credentials from wallet service.", e);
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

    public BigDecimal getCoinbaseSpotPrice(String symbol) {
        String normalizedSymbol = normalizeSymbol(symbol);
        String url = walletServiceUrl + "/coinbase/market/ticker?productId=" + encode(normalizedSymbol);
        System.out.println("📡 Requesting Coinbase ticker from wallet-service at: " + url);

        try {
            CoinbaseTickerDTO tickerDTO = restTemplate.getForObject(url, CoinbaseTickerDTO.class);
            if (tickerDTO == null || tickerDTO.price() == null) {
                throw new RuntimeException("Wallet service returned null ticker response.");
            }
            return new BigDecimal(tickerDTO.price());
        } catch (Exception e) {
            System.err.println("❌ ERROR: Failed to fetch Coinbase ticker for symbol " + symbol + ": " + e.getMessage());
            throw new RuntimeException("Could not fetch Coinbase ticker from wallet service.", e);
        }
    }

    public CoinbaseMarketOrderResponseDTO placeCoinbaseMarketBuy(Long userId, String symbol, BigDecimal quantity) {
        return placeCoinbaseMarketOrder(userId, symbol, "BUY", quantity);
    }

    public CoinbaseMarketOrderResponseDTO placeCoinbaseMarketSell(Long userId, String symbol, BigDecimal quantity) {
        return placeCoinbaseMarketOrder(userId, symbol, "SELL", quantity);
    }

    private CoinbaseMarketOrderResponseDTO placeCoinbaseMarketOrder(Long userId, String symbol, String side, BigDecimal quantity) {
        String normalizedSymbol = normalizeSymbol(symbol);
        String url = walletServiceUrl + "/coinbase/orders/market";

        Map<String, Object> request = new HashMap<>();
        request.put("userId", userId);
        request.put("productId", normalizedSymbol);
        request.put("side", side);
        request.put("size", quantity.toPlainString());

        System.out.println("🛒 Placing Coinbase market order via wallet-service: " + request);

        try {
            return restTemplate.postForObject(url, request, CoinbaseMarketOrderResponseDTO.class);
        } catch (Exception e) {
            System.err.println("❌ ERROR: Failed to place Coinbase market order via wallet service: " + e.getMessage());
            throw new RuntimeException("Could not place Coinbase market order via wallet service.", e);
        }
    }

    public List<CoinbaseOrderDTO> getCoinbaseOpenOrders(Long userId) {
        String url = walletServiceUrl + "/coinbase/orders/open?userId=" + userId;
        System.out.println("📄 Requesting Coinbase open orders from wallet-service at: " + url);
        try {
            ResponseEntity<List<CoinbaseOrderDTO>> response = restTemplate.exchange(
                    url,
                    HttpMethod.GET,
                    HttpEntity.EMPTY,
                    OPEN_ORDERS_TYPE
            );
            return Optional.ofNullable(response.getBody()).orElseGet(List::of);
        } catch (Exception e) {
            System.err.println("❌ ERROR: Failed to fetch Coinbase open orders for userId " + userId + ": " + e.getMessage());
            throw new RuntimeException("Could not fetch Coinbase open orders from wallet service.", e);
        }
    }

    public List<CoinbasePositionDTO> getCoinbasePositions(Long userId) {
        String url = walletServiceUrl + "/coinbase/positions?userId=" + userId;
        System.out.println("📊 Requesting Coinbase positions from wallet-service at: " + url);
        try {
            ResponseEntity<List<CoinbasePositionDTO>> response = restTemplate.exchange(
                    url,
                    HttpMethod.GET,
                    HttpEntity.EMPTY,
                    POSITIONS_TYPE
            );
            return Optional.ofNullable(response.getBody()).orElseGet(List::of);
        } catch (Exception e) {
            System.err.println("❌ ERROR: Failed to fetch Coinbase positions for userId " + userId + ": " + e.getMessage());
            throw new RuntimeException("Could not fetch Coinbase positions from wallet service.", e);
        }
    }

    public List<CoinbaseTradeDTO> getCoinbaseTradeHistory(Long userId, String symbol, Integer limit) {
        StringBuilder urlBuilder = new StringBuilder(walletServiceUrl)
                .append("/coinbase/trades?userId=")
                .append(userId);
        if (symbol != null && !symbol.isBlank()) {
            urlBuilder.append("&productId=").append(encode(normalizeSymbol(symbol)));
        }
        if (limit != null) {
            urlBuilder.append("&limit=").append(limit);
        }
        String url = urlBuilder.toString();
        System.out.println("📜 Requesting Coinbase trade history from wallet-service at: " + url);
        try {
            ResponseEntity<List<CoinbaseTradeDTO>> response = restTemplate.exchange(
                    url,
                    HttpMethod.GET,
                    HttpEntity.EMPTY,
                    TRADES_TYPE
            );
            return Optional.ofNullable(response.getBody()).orElseGet(List::of);
        } catch (Exception e) {
            System.err.println("❌ ERROR: Failed to fetch Coinbase trade history for userId " + userId + ": " + e.getMessage());
            throw new RuntimeException("Could not fetch Coinbase trade history from wallet service.", e);
        }
    }

    private String normalizeSymbol(String symbol) {
        if (symbol == null) {
            return null;
        }
        return symbol.replace("/", "-").toUpperCase();
    }

    private String encode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }
}