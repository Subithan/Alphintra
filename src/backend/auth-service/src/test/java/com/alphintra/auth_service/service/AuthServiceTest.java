package com.alphintra.auth_service.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.alphintra.auth_service.dto.AuthRequest;
import com.alphintra.auth_service.dto.AuthResponse;
import com.alphintra.auth_service.dto.RegisterRequest;
import com.alphintra.auth_service.entity.Role;
import com.alphintra.auth_service.entity.User;
import com.alphintra.auth_service.exception.InvalidCredentialsException;
import com.alphintra.auth_service.exception.UserAlreadyExistsException;
import com.alphintra.auth_service.repository.RoleRepository;
import com.alphintra.auth_service.repository.UserRepository;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

  @Mock private UserRepository userRepository;

  @Mock private RoleRepository roleRepository;

  @Mock private PasswordEncoder passwordEncoder;

  private AuthService authService;

  private static final long EXPIRATION = 3_600_000L;

  @BeforeEach
  void setUp() {
    String rawSecret = "super-secret-signing-key-for-tests-that-is-long-enough-1234567890";
    String encodedSecret =
        Base64.getEncoder().encodeToString(rawSecret.getBytes(StandardCharsets.UTF_8));
    authService =
        new AuthService(userRepository, roleRepository, passwordEncoder, encodedSecret, EXPIRATION);
  }

  @Test
  void registerCreatesUserWithDefaultRoleAndToken() {
    RegisterRequest request = new RegisterRequest();
    request.setUsername("alice");
    request.setEmail("alice@example.com");
    request.setPassword("password123");
    request.setFirstName("Alice");
    request.setLastName("Doe");

    when(userRepository.existsByUsername("alice")).thenReturn(false);
    when(userRepository.existsByEmail("alice@example.com")).thenReturn(false);

    Role role = new Role();
    role.setId(1L);
    role.setName("USER");
    when(roleRepository.findByName("USER")).thenReturn(Optional.of(role));
    when(passwordEncoder.encode("password123")).thenReturn("hashed");
    when(userRepository.save(any(User.class)))
        .thenAnswer(
            invocation -> {
              User user = invocation.getArgument(0);
              user.setId(42L);
              return user;
            });

    AuthResponse response = authService.register(request);

    assertThat(response.getToken()).isNotBlank();
    assertThat(response.getUser().username()).isEqualTo("alice");
    assertThat(response.getUser().roles()).containsExactly("USER");

    verify(passwordEncoder).encode("password123");
    ArgumentCaptor<User> savedCaptor = ArgumentCaptor.forClass(User.class);
    verify(userRepository).save(savedCaptor.capture());
    assertThat(savedCaptor.getValue().getRoles()).extracting(Role::getName).containsExactly("USER");
  }

  @Test
  void registerThrowsWhenUsernameExists() {
    RegisterRequest request = new RegisterRequest();
    request.setUsername("taken");
    request.setEmail("taken@example.com");
    request.setPassword("password123");
    request.setFirstName("Taken");
    request.setLastName("User");

    when(userRepository.existsByUsername("taken")).thenReturn(true);

    assertThatThrownBy(() -> authService.register(request))
        .isInstanceOf(UserAlreadyExistsException.class)
        .hasMessageContaining("Username");
  }

  @Test
  void authenticateReturnsTokenForValidCredentials() {
    Role role = new Role();
    role.setId(1L);
    role.setName("USER");

    User user = new User();
    user.setId(5L);
    user.setUsername("bob");
    user.setEmail("bob@example.com");
    user.setPassword("hashed");
    user.getRoles().add(role);

    AuthRequest request = new AuthRequest();
    request.setEmail("bob@example.com");
    request.setPassword("password123");

    when(userRepository.findByEmail("bob@example.com")).thenReturn(Optional.of(user));
    when(passwordEncoder.matches("password123", "hashed")).thenReturn(true);

    AuthResponse response = authService.authenticate(request);

    assertThat(response.getToken()).isNotBlank();
    assertThat(response.getUser().username()).isEqualTo("bob");
  }

  @Test
  void authenticateThrowsForInvalidPassword() {
    User user = new User();
    user.setEmail("bob@example.com");
    user.setPassword("hashed");

    AuthRequest request = new AuthRequest();
    request.setEmail("bob@example.com");
    request.setPassword("bad");

    when(userRepository.findByEmail("bob@example.com")).thenReturn(Optional.of(user));
    when(passwordEncoder.matches(eq("bad"), eq("hashed"))).thenReturn(false);

    assertThatThrownBy(() -> authService.authenticate(request))
        .isInstanceOf(InvalidCredentialsException.class)
        .hasMessageContaining("Invalid email or password");
  }
}
