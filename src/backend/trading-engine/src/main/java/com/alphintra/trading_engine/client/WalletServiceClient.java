// package com.alphintra.trading_engine.client;

// import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
// import lombok.RequiredArgsConstructor;
// import org.springframework.beans.factory.annotation.Value;
// import org.springframework.stereotype.Component;
// import org.springframework.web.client.RestTemplate;

// @Component
// @RequiredArgsConstructor
// public class WalletServiceClient {

//     private final RestTemplate restTemplate;

//     // The URL will be injected from application.properties
//     @Value("${services.wallet.url}")
//     private String walletServiceUrl;

//     public WalletCredentialsDTO getCredentials(Long userId) {
//         // IMPORTANT: The Python wallet service currently does not have an endpoint to GET keys.
//         // You must add an endpoint like GET /binance/credentials to fetch keys for a user.
//         // The code below assumes such an endpoint exists.
        
//         String url = walletServiceUrl + "/binance/credentials?userId=" + userId; // Example URL
        
//         try {
//             // Uncomment the following line when the wallet service endpoint is ready.
//             // return restTemplate.getForObject(url, WalletCredentialsDTO.class);

//             // --- TEMPORARY WORKAROUND for development ---
//             // This allows you to test without the live endpoint by using environment variables.
//             System.out.println("⚠️ WARN: Using placeholder API keys from environment variables.");
//             String apiKey = System.getenv("BINANCE_API_KEY");
//             String secretKey = System.getenv("BINANCE_SECRET_KEY");
//             if (apiKey == null || secretKey == null || apiKey.isBlank() || secretKey.isBlank()) {
//                 throw new IllegalStateException("Missing BINANCE_API_KEY or BINANCE_SECRET_KEY environment variables for testing.");
//             }
//             return new WalletCredentialsDTO(apiKey, secretKey);
//             // --- END OF TEMPORARY WORKAROUND ---

//         } catch (Exception e) {
//             throw new RuntimeException("Failed to fetch credentials from wallet service at " + url, e);
//         }
//     }
// }


package com.alphintra.trading_engine.client;

import com.alphintra.trading_engine.dto.WalletCredentialsDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

@Component
@RequiredArgsConstructor
public class WalletServiceClient {

    private final RestTemplate restTemplate;

    @Value("${services.wallet.url}")
    private String walletServiceUrl;

    public WalletCredentialsDTO getCredentials(Long userId) {
        // Append the userId as a query parameter to the URL
        String url = walletServiceUrl + "/binance/credentials?userId=" + userId;

        System.out.println("Attempting to fetch credentials from wallet-service at: " + url);
        
        try {
            WalletCredentialsDTO credentials = restTemplate.getForObject(url, WalletCredentialsDTO.class);
            
            if (credentials == null || credentials.apiKey() == null || credentials.secretKey() == null) {
                 throw new RuntimeException("Received null or incomplete credentials from wallet service.");
            }
            
            String apiKey = credentials.apiKey();
            System.out.println("✅ Successfully fetched credentials for userId " + userId);
            System.out.println("   Received API Key starts with: " + apiKey.substring(0, 5) + "...");

            return credentials;

        } catch (Exception e) {
            System.err.println("❌ ERROR: Failed to fetch credentials for userId " + userId);
            throw new RuntimeException("Could not fetch credentials from wallet service.", e);
        }
    }
}