package com.alphintra.auth_service.controller;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.alphintra.auth_service.dto.AuthRequest;
import com.alphintra.auth_service.dto.AuthResponse;
import com.alphintra.auth_service.dto.RegisterRequest;
import com.alphintra.auth_service.dto.TokenValidationRequest;
import com.alphintra.auth_service.dto.UserProfile;
import com.alphintra.auth_service.exception.GlobalExceptionHandler;
import com.alphintra.auth_service.service.AuthService;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(AuthController.class)
@AutoConfigureMockMvc(addFilters = false)
@Import(GlobalExceptionHandler.class)
class AuthControllerTest {

  @Autowired private MockMvc mockMvc;

  @Autowired private ObjectMapper objectMapper;

  @MockBean private AuthService authService;

  @Test
  void registerReturnsCreated() throws Exception {
    RegisterRequest request = new RegisterRequest();
    request.setUsername("alice");
    request.setEmail("alice@example.com");
    request.setPassword("password123");
    request.setFirstName("Alice");
    request.setLastName("Doe");

    AuthResponse response =
        new AuthResponse(
            "token",
            new UserProfile(
                1L, "alice", "alice@example.com", "Alice", "Doe", "NOT_STARTED", Set.of("USER")));
    when(authService.register(any(RegisterRequest.class))).thenReturn(response);

    mockMvc
        .perform(
            post("/api/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
        .andExpect(status().isCreated())
        .andExpect(jsonPath("$.token").value("token"))
        .andExpect(jsonPath("$.user.username").value("alice"));
  }

  @Test
  void registerValidatesRequestBody() throws Exception {
    mockMvc
        .perform(post("/api/auth/register").contentType(MediaType.APPLICATION_JSON).content("{}"))
        .andExpect(status().isBadRequest())
        .andExpect(jsonPath("$.title").value("Validation failure"));
  }

  @Test
  void loginReturnsOk() throws Exception {
    AuthRequest request = new AuthRequest();
    request.setEmail("alice@example.com");
    request.setPassword("password123");

    AuthResponse response =
        new AuthResponse(
            "token",
            new UserProfile(
                1L, "alice", "alice@example.com", "Alice", "Doe", "NOT_STARTED", Set.of("USER")));
    when(authService.authenticate(any(AuthRequest.class))).thenReturn(response);

    mockMvc
        .perform(
            post("/api/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.token").value("token"));
  }

  @Test
  void validateTokenReturnsBool() throws Exception {
    TokenValidationRequest request = new TokenValidationRequest();
    request.setToken("token");
    when(authService.validateToken("token")).thenReturn(true);

    mockMvc
        .perform(
            post("/api/auth/validate")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$").value(true));
  }
}
