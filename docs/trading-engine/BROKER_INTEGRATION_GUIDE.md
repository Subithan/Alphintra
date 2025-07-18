# Broker Integration Guide

## 🎯 Overview

This guide provides detailed instructions for integrating new brokers into the Alphintra Trading Engine. The integration framework is designed to be flexible, extensible, and consistent across all supported brokers.

## 🏗️ Integration Architecture

### Broker Adapter Pattern

```java
// Base interface that all broker adapters must implement
public interface BrokerAdapter {
    // Connection Management
    ConnectionResult connect(BrokerCredentials credentials);
    void disconnect();
    boolean isConnected();
    
    // Account Operations
    AccountInfo getAccountInfo() throws BrokerException;
    List<Position> getPositions() throws BrokerException;
    List<Order> getOrders(OrderFilter filter) throws BrokerException;
    Balance getBalance() throws BrokerException;
    
    // Trading Operations
    OrderResult placeOrder(OrderRequest order) throws BrokerException;
    OrderResult modifyOrder(String orderId, OrderModification modification) throws BrokerException;
    OrderResult cancelOrder(String orderId) throws BrokerException;
    
    // Market Data
    Quote getQuote(String symbol) throws BrokerException;
    List<Candle> getHistoricalData(String symbol, TimeFrame timeFrame, int count) throws BrokerException;
    
    // Real-time Subscriptions
    void subscribeMarketData(List<String> symbols, MarketDataCallback callback) throws BrokerException;
    void subscribeOrderUpdates(OrderUpdateCallback callback) throws BrokerException;
    void subscribePositionUpdates(PositionUpdateCallback callback) throws BrokerException;
    
    // Metadata
    BrokerInfo getBrokerInfo();
    List<String> getSupportedSymbols() throws BrokerException;
    TradingHours getTradingHours(String symbol) throws BrokerException;
}
```

## 📋 Integration Checklist

### Phase 1: Research & Planning
- [ ] **API Documentation Review**
  - Study broker's API documentation
  - Identify authentication methods
  - Understand rate limits
  - Review supported order types
  - Check WebSocket capabilities

- [ ] **Account Setup**
  - Create broker account
  - Generate API keys
  - Set up sandbox/testnet environment
  - Verify API access permissions

- [ ] **Asset Coverage Analysis**
  - Identify supported asset classes
  - Map symbol formats
  - Understand trading pairs
  - Check commission structures

### Phase 2: Adapter Implementation
- [ ] **Basic Adapter Structure**
  - Extend AbstractBrokerAdapter
  - Implement required interface methods
  - Add broker-specific configuration
  - Set up authentication

- [ ] **Core Trading Functions**
  - Implement order placement
  - Add order modification/cancellation
  - Handle order status updates
  - Implement position tracking

- [ ] **Market Data Integration**
  - Add quote retrieval
  - Implement historical data fetching
  - Set up real-time data streams
  - Handle WebSocket connections

### Phase 3: Testing & Validation
- [ ] **Unit Tests**
  - Test all adapter methods
  - Mock external API calls
  - Validate error handling
  - Test rate limiting

- [ ] **Integration Tests**
  - Test with broker sandbox
  - Validate order workflows
  - Test market data accuracy
  - Verify WebSocket stability

- [ ] **Performance Tests**
  - Measure latency
  - Test throughput limits
  - Validate under load
  - Test failover scenarios

## 🔧 Implementation Examples

### 1. Basic Adapter Structure

```java
@Component("exampleBrokerAdapter")
@Profile("!test")
public class ExampleBrokerAdapter extends AbstractBrokerAdapter {
    
    private static final String BASE_URL = "https://api.examplebroker.com";
    private static final RateLimiter RATE_LIMITER = RateLimiter.create(10.0); // 10 requests per second
    
    private final RestTemplate restTemplate;
    private final WebSocketStompClient webSocketClient;
    private ExampleBrokerConfig config;
    private String accessToken;
    
    public ExampleBrokerAdapter(RestTemplate restTemplate, WebSocketStompClient webSocketClient) {
        this.restTemplate = restTemplate;
        this.webSocketClient = webSocketClient;
    }
    
    @Override
    public ConnectionResult connect(BrokerCredentials credentials) {
        try {
            this.config = new ExampleBrokerConfig(credentials);
            this.accessToken = authenticate(credentials);
            
            // Test connection
            AccountInfo account = getAccountInfo();
            
            return ConnectionResult.success("Connected to Example Broker", account.getAccountId());
        } catch (Exception e) {
            return ConnectionResult.failure("Connection failed: " + e.getMessage());
        }
    }
    
    private String authenticate(BrokerCredentials credentials) throws AuthenticationException {
        // Implement broker-specific authentication
        AuthRequest request = AuthRequest.builder()
            .apiKey(credentials.getApiKey())
            .secretKey(credentials.getSecretKey())
            .timestamp(System.currentTimeMillis())
            .build();
            
        // Add signature if required
        String signature = generateSignature(request, credentials.getSecretKey());
        request.setSignature(signature);
        
        AuthResponse response = restTemplate.postForObject(
            BASE_URL + "/auth/token", 
            request, 
            AuthResponse.class
        );
        
        if (response == null || !response.isSuccess()) {
            throw new AuthenticationException("Authentication failed");
        }
        
        return response.getAccessToken();
    }
    
    @Override
    public OrderResult placeOrder(OrderRequest order) throws BrokerException {
        validateOrder(order);
        RATE_LIMITER.acquire();
        
        try {
            // Convert to broker-specific format
            ExampleOrderRequest brokerOrder = convertToBrokerOrder(order);
            
            // Add authentication headers
            HttpHeaders headers = createAuthHeaders();
            HttpEntity<ExampleOrderRequest> entity = new HttpEntity<>(brokerOrder, headers);
            
            // Place order
            ResponseEntity<ExampleOrderResponse> response = restTemplate.postForEntity(
                BASE_URL + "/orders", 
                entity, 
                ExampleOrderResponse.class
            );
            
            if (!response.getStatusCode().is2xxSuccessful()) {
                throw new BrokerException("Order placement failed: " + response.getStatusCode());
            }
            
            return convertToOrderResult(response.getBody());
            
        } catch (Exception e) {
            return OrderResult.failure(order.getClientOrderId(), "Order failed: " + e.getMessage());
        }
    }
    
    // Helper methods
    private HttpHeaders createAuthHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.setBearerAuth(accessToken);
        headers.set("X-API-KEY", config.getApiKey());
        return headers;
    }
    
    private ExampleOrderRequest convertToBrokerOrder(OrderRequest order) {
        return ExampleOrderRequest.builder()
            .symbol(mapSymbol(order.getSymbol()))
            .side(order.getSide().toString().toLowerCase())
            .type(mapOrderType(order.getType()))
            .quantity(order.getQuantity().toString())
            .price(order.getPrice() != null ? order.getPrice().toString() : null)
            .timeInForce(mapTimeInForce(order.getTimeInForce()))
            .clientOrderId(order.getClientOrderId())
            .build();
    }
}
```

### 2. WebSocket Integration

```java
@Component
public class ExampleWebSocketHandler implements StompSessionHandler {
    
    private final OrderUpdateCallback orderCallback;
    private final MarketDataCallback marketDataCallback;
    private StompSession session;
    
    public void subscribeToOrderUpdates(String accountId) {
        if (session != null && session.isConnected()) {
            session.subscribe("/user/" + accountId + "/orders", new StompFrameHandler() {
                @Override
                public Type getPayloadType(StompHeaders headers) {
                    return ExampleOrderUpdate.class;
                }
                
                @Override
                public void handleFrame(StompHeaders headers, Object payload) {
                    ExampleOrderUpdate update = (ExampleOrderUpdate) payload;
                    OrderUpdate standardUpdate = convertToStandardUpdate(update);
                    orderCallback.onOrderUpdate(standardUpdate);
                }
            });
        }
    }
    
    public void subscribeToMarketData(List<String> symbols) {
        for (String symbol : symbols) {
            String brokerSymbol = mapSymbol(symbol);
            session.subscribe("/market/" + brokerSymbol, new StompFrameHandler() {
                @Override
                public Type getPayloadType(StompHeaders headers) {
                    return ExampleMarketData.class;
                }
                
                @Override
                public void handleFrame(StompHeaders headers, Object payload) {
                    ExampleMarketData data = (ExampleMarketData) payload;
                    MarketDataUpdate update = convertToStandardMarketData(data);
                    marketDataCallback.onMarketData(update);
                }
            });
        }
    }
}
```

### 3. Error Handling & Retry Logic

```java
@Component
public class BrokerErrorHandler {
    
    private static final int MAX_RETRIES = 3;
    private static final Duration RETRY_DELAY = Duration.ofSeconds(1);
    
    public <T> T executeWithRetry(Supplier<T> operation, String operationName) throws BrokerException {
        int attempt = 0;
        Exception lastException = null;
        
        while (attempt < MAX_RETRIES) {
            try {
                return operation.get();
            } catch (RateLimitException e) {
                // Wait for rate limit reset
                sleepForRateLimit(e.getRetryAfter());
                attempt++;
                lastException = e;
            } catch (TemporaryException e) {
                // Retry for temporary issues
                sleep(RETRY_DELAY.multipliedBy(attempt + 1));
                attempt++;
                lastException = e;
            } catch (PermanentException e) {
                // Don't retry for permanent failures
                throw new BrokerException("Permanent failure in " + operationName, e);
            }
        }
        
        throw new BrokerException("Max retries exceeded for " + operationName, lastException);
    }
    
    private void sleepForRateLimit(Duration retryAfter) {
        try {
            Thread.sleep(retryAfter.toMillis());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException("Interrupted while waiting for rate limit", e);
        }
    }
}
```

## 🔒 Security Considerations

### API Key Management
```java
@Service
public class BrokerCredentialService {
    
    @Autowired
    private EncryptionService encryptionService;
    
    public void storeBrokerCredentials(UUID userId, String brokerId, BrokerApiKeys keys) {
        // Encrypt sensitive data
        String encryptedApiKey = encryptionService.encrypt(keys.getApiKey());
        String encryptedSecret = encryptionService.encrypt(keys.getSecretKey());
        
        BrokerCredentials credentials = BrokerCredentials.builder()
            .userId(userId)
            .brokerId(brokerId)
            .apiKey(encryptedApiKey)
            .secretKey(encryptedSecret)
            .isTestnet(keys.isTestnet())
            .permissions(keys.getPermissions())
            .expiresAt(keys.getExpiresAt())
            .build();
            
        credentialsRepository.save(credentials);
        
        // Audit log
        auditLogger.logCredentialStorage(userId, brokerId);
    }
    
    public BrokerCredentials getBrokerCredentials(UUID userId, String brokerId) {
        BrokerCredentials credentials = credentialsRepository
            .findByUserIdAndBrokerId(userId, brokerId)
            .orElseThrow(() -> new CredentialsNotFoundException("Credentials not found"));
            
        // Decrypt sensitive data
        credentials.setApiKey(encryptionService.decrypt(credentials.getApiKey()));
        credentials.setSecretKey(encryptionService.decrypt(credentials.getSecretKey()));
        
        return credentials;
    }
}
```

### Request Signing
```java
public class SignatureGenerator {
    
    public static String generateHmacSha256(String data, String secretKey) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            SecretKeySpec keySpec = new SecretKeySpec(secretKey.getBytes(), "HmacSHA256");
            mac.init(keySpec);
            byte[] hash = mac.doFinal(data.getBytes());
            return Hex.encodeHexString(hash);
        } catch (Exception e) {
            throw new RuntimeException("Failed to generate signature", e);
        }
    }
    
    public static String createQueryString(Map<String, String> params) {
        return params.entrySet().stream()
            .sorted(Map.Entry.comparingByKey())
            .map(entry -> entry.getKey() + "=" + entry.getValue())
            .collect(Collectors.joining("&"));
    }
}
```

## 📊 Testing Framework

### Unit Tests
```java
@ExtendWith(MockitoExtension.class)
class ExampleBrokerAdapterTest {
    
    @Mock
    private RestTemplate restTemplate;
    
    @Mock
    private WebSocketStompClient webSocketClient;
    
    @InjectMocks
    private ExampleBrokerAdapter adapter;
    
    @Test
    void shouldPlaceOrderSuccessfully() {
        // Given
        OrderRequest order = createTestOrder();
        ExampleOrderResponse mockResponse = createMockResponse();
        
        when(restTemplate.postForEntity(any(String.class), any(HttpEntity.class), eq(ExampleOrderResponse.class)))
            .thenReturn(ResponseEntity.ok(mockResponse));
        
        // When
        OrderResult result = adapter.placeOrder(order);
        
        // Then
        assertThat(result.isSuccess()).isTrue();
        assertThat(result.getBrokerOrderId()).isEqualTo(mockResponse.getOrderId());
        verify(restTemplate).postForEntity(any(String.class), any(HttpEntity.class), eq(ExampleOrderResponse.class));
    }
    
    @Test
    void shouldHandleOrderRejection() {
        // Given
        OrderRequest order = createTestOrder();
        
        when(restTemplate.postForEntity(any(String.class), any(HttpEntity.class), eq(ExampleOrderResponse.class)))
            .thenThrow(new HttpClientErrorException(HttpStatus.BAD_REQUEST, "Insufficient funds"));
        
        // When
        OrderResult result = adapter.placeOrder(order);
        
        // Then
        assertThat(result.isSuccess()).isFalse();
        assertThat(result.getErrorMessage()).contains("Insufficient funds");
    }
}
```

### Integration Tests
```java
@SpringBootTest
@TestPropertySource(properties = {
    "broker.example.enabled=true",
    "broker.example.testnet=true"
})
class ExampleBrokerIntegrationTest {
    
    @Autowired
    private ExampleBrokerAdapter adapter;
    
    @Test
    void shouldConnectToTestnet() {
        // Given
        BrokerCredentials testCredentials = createTestCredentials();
        
        // When
        ConnectionResult result = adapter.connect(testCredentials);
        
        // Then
        assertThat(result.isSuccess()).isTrue();
        assertThat(adapter.isConnected()).isTrue();
    }
    
    @Test
    void shouldRetrieveAccountInfo() {
        // Given
        adapter.connect(createTestCredentials());
        
        // When
        AccountInfo accountInfo = adapter.getAccountInfo();
        
        // Then
        assertThat(accountInfo).isNotNull();
        assertThat(accountInfo.getAccountId()).isNotBlank();
        assertThat(accountInfo.getBalance()).isNotNull();
    }
}
```

## 🚀 Deployment & Configuration

### Broker Configuration
```yaml
# application.yml
brokers:
  example:
    enabled: true
    base-url: "https://api.examplebroker.com"
    websocket-url: "wss://stream.examplebroker.com"
    rate-limit: 10  # requests per second
    timeout: 30s
    retry:
      max-attempts: 3
      delay: 1s
    supported-assets:
      - CRYPTO
      - FOREX
    features:
      - SPOT_TRADING
      - MARGIN_TRADING
      - FUTURES_TRADING
```

### Spring Configuration
```java
@Configuration
@ConditionalOnProperty(name = "brokers.example.enabled", havingValue = "true")
public class ExampleBrokerConfig {
    
    @Bean
    @ConfigurationProperties(prefix = "brokers.example")
    public ExampleBrokerProperties exampleBrokerProperties() {
        return new ExampleBrokerProperties();
    }
    
    @Bean
    public ExampleBrokerAdapter exampleBrokerAdapter(
            RestTemplate restTemplate,
            WebSocketStompClient webSocketClient,
            ExampleBrokerProperties properties) {
        return new ExampleBrokerAdapter(restTemplate, webSocketClient, properties);
    }
}
```

## 📖 Documentation Requirements

### Broker Documentation Template
```markdown
# [Broker Name] Integration

## Overview
- **Broker**: [Broker Name]
- **Asset Classes**: [List supported asset classes]
- **API Type**: REST + WebSocket
- **Authentication**: [Auth method]
- **Rate Limits**: [Rate limit details]

## Supported Features
- [x] Spot Trading
- [x] Margin Trading
- [ ] Futures Trading
- [x] Market Data
- [x] Real-time Updates

## Order Types Supported
- [x] Market Orders
- [x] Limit Orders
- [x] Stop Orders
- [ ] Stop Limit Orders

## Configuration
[Configuration examples]

## Error Codes
[List of broker-specific error codes and meanings]

## Testing
[Testing instructions and test account setup]
```

## 🔄 Continuous Integration

### Integration Pipeline
```yaml
# .github/workflows/broker-integration.yml
name: Broker Integration Tests

on:
  push:
    paths:
      - 'src/main/java/com/alphintra/trading/brokers/**'
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  test-brokers:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        broker: [binance, alpaca, oanda, example]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up JDK 17
      uses: actions/setup-java@v3
      with:
        java-version: '17'
        
    - name: Run broker integration tests
      run: |
        mvn test -Dtest=**/*${{ matrix.broker }}*IntegrationTest
      env:
        BROKER_${{ matrix.broker | upper }}_API_KEY: ${{ secrets[format('BROKER_{0}_API_KEY', matrix.broker | upper)] }}
        BROKER_${{ matrix.broker | upper }}_SECRET_KEY: ${{ secrets[format('BROKER_{0}_SECRET_KEY', matrix.broker | upper)] }}
```

This comprehensive guide provides everything needed to integrate new brokers into the Alphintra Trading Engine, ensuring consistency, quality, and maintainability across all integrations.