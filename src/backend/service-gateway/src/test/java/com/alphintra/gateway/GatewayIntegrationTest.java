package com.alphintra.gateway;

import static org.assertj.core.api.Assertions.assertThat;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import javax.crypto.SecretKey;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.reactive.server.WebTestClient;
import org.springframework.web.reactive.function.BodyInserters;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
@Testcontainers
class GatewayIntegrationTest {

  private static final String RAW_SECRET =
      "integration-test-secret-key-value-which-is-definitely-long-enough-0123456789abcdef0123456789abcdef";
  private static final String SECRET_BASE64 =
      java.util.Base64.getEncoder().encodeToString(RAW_SECRET.getBytes(StandardCharsets.UTF_8));

  @Container
  static final GenericContainer<?> REDIS =
      new GenericContainer<>("redis:7-alpine").withExposedPorts(6379);

  static MockWebServer authService;
  static MockWebServer tradingService;

  @Autowired private WebTestClient webTestClient;

  private SecretKey signingKey;

  @DynamicPropertySource
  static void registerProperties(DynamicPropertyRegistry registry) {
    registry.add("AUTH_SERVICE_URI", () -> authService.url("/").toString());
    registry.add("TRADING_ENGINE_URI", () -> tradingService.url("/").toString());
    registry.add("spring.redis.host", () -> REDIS.getHost());
    registry.add("spring.redis.port", () -> REDIS.getMappedPort(6379));
    registry.add("gateway.security.jwt.secret", () -> SECRET_BASE64);
  }

  @BeforeAll
  static void startServers() throws Exception {
    authService = new MockWebServer();
    tradingService = new MockWebServer();
    authService.start();
    tradingService.start();
  }

  @AfterAll
  static void stopServers() throws Exception {
    authService.shutdown();
    tradingService.shutdown();
  }

  @BeforeEach
  void setUp() {
    this.signingKey = Keys.hmacShaKeyFor(Decoders.BASE64.decode(SECRET_BASE64));
  }

  @Test
  void shouldAllowPublicLoginRoute() {
    authService.enqueue(new MockResponse().setResponseCode(200).setBody("{}"));

    webTestClient
        .post()
        .uri("/api/auth/login")
        .contentType(MediaType.APPLICATION_JSON)
        .body(BodyInserters.fromValue(Map.of("email", "user@example.com", "password", "secret")))
        .exchange()
        .expectStatus()
        .isOk();

    try {
      var request = authService.takeRequest(2, TimeUnit.SECONDS);
      assertThat(request).isNotNull();
      assertThat(request.getMethod()).isEqualTo("POST");
      assertThat(request.getPath()).isEqualTo("/api/auth/login");
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      throw new AssertionError("Interrupted while verifying request", e);
    }
  }

  @Test
  void shouldRejectMissingTokenForProtectedRoute() {
    webTestClient.get().uri("/api/trading/orders").exchange().expectStatus().isUnauthorized();
  }

  @Test
  void shouldForwardAuthenticatedRequest() {
    tradingService.enqueue(new MockResponse().setResponseCode(200).setBody("[]"));

    String token =
        Jwts.builder()
            .setSubject("demo-user")
            .signWith(signingKey, SignatureAlgorithm.HS512)
            .compact();

    webTestClient
        .get()
        .uri("/api/trading/orders")
        .header(HttpHeaders.AUTHORIZATION, "Bearer " + token)
        .exchange()
        .expectStatus()
        .isOk()
        .expectHeader()
        .value("X-Correlation-Id", value -> assertThat(value).isNotBlank());

    try {
      var request = tradingService.takeRequest(2, TimeUnit.SECONDS);
      assertThat(request).isNotNull();
      assertThat(request.getPath()).isEqualTo("/api/trading/orders");
      assertThat(request.getHeader("X-User-Id")).isEqualTo("demo-user");
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      throw new AssertionError("Interrupted while verifying trading request", e);
    }
  }
}
