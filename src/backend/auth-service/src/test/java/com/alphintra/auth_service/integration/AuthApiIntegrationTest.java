package com.alphintra.auth_service.integration;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.alphintra.auth_service.dto.RegisterRequest;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.ImportAutoConfiguration;
import org.springframework.boot.autoconfigure.security.oauth2.client.servlet.OAuth2ClientAutoConfiguration;
import org.springframework.boot.autoconfigure.security.oauth2.resource.servlet.OAuth2ResourceServerAutoConfiguration;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@SpringBootTest
@AutoConfigureMockMvc(addFilters = false)
@ActiveProfiles("test")
@Testcontainers
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
@ImportAutoConfiguration(
    exclude = {OAuth2ClientAutoConfiguration.class, OAuth2ResourceServerAutoConfiguration.class})
class AuthApiIntegrationTest {

  @Container
  static final PostgreSQLContainer<?> POSTGRES =
      new PostgreSQLContainer<>("postgres:15-alpine")
          .withDatabaseName("auth_test")
          .withUsername("auth")
          .withPassword("auth");

  private static final String RAW_SECRET =
      "integration-test-secret-key-value-which-is-definitely-long-enough-0123456789abcdef0123456789abcdef";

  @DynamicPropertySource
  static void registerProperties(DynamicPropertyRegistry registry) {
    registry.add(
        "spring.datasource.url",
        () -> {
          if (!POSTGRES.isRunning()) {
            POSTGRES.start();
          }
          return POSTGRES.getJdbcUrl();
        });
    registry.add("spring.datasource.username", POSTGRES::getUsername);
    registry.add("spring.datasource.password", POSTGRES::getPassword);
    registry.add("spring.datasource.driver-class-name", POSTGRES::getDriverClassName);
    registry.add(
        "jwt.secret",
        () -> Base64.getEncoder().encodeToString(RAW_SECRET.getBytes(StandardCharsets.UTF_8)));
    registry.add("jwt.expiration", () -> 3_600_000);
  }

  @Autowired private MockMvc mockMvc;

  @Autowired private ObjectMapper objectMapper;

  @Test
  void registerAndLoginFlow() throws Exception {
    RegisterRequest register = new RegisterRequest();
    register.setUsername("integration");
    register.setEmail("integration@example.com");
    register.setPassword("password123");
    register.setFirstName("Integration");
    register.setLastName("Test");

    mockMvc
        .perform(
            post("/api/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(register)))
        .andExpect(status().isCreated())
        .andExpect(jsonPath("$.token").isNotEmpty());

    mockMvc
        .perform(
            post("/api/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(
                    "{"
                        + "\"email\":\"integration@example.com\","
                        + "\"password\":\"password123\"}"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.token").isNotEmpty())
        .andExpect(jsonPath("$.user.roles[0]").value("USER"));
  }
}
