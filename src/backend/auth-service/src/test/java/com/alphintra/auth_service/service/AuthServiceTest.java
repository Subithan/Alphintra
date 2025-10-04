// Path: Alphintra/src/backend/auth-service/src/test/java/com/alphintra/auth_service/service/AuthServiceTest.java
// Purpose: Unit tests for AuthService, updated to use the standard Maven test directory.

package com.alphintra.auth_service.service;

import com.alphintra.auth_service.entity.User;
import com.alphintra.auth_service.dto.AuthResponse;
import com.alphintra.auth_service.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class AuthServiceTest {
    private UserRepository userRepository;
    private PasswordEncoder passwordEncoder;
    private AuthService authService;

    @BeforeEach
    void setUp() {
        userRepository = mock(UserRepository.class);
        passwordEncoder = new BCryptPasswordEncoder();
        authService = new AuthService(userRepository, passwordEncoder, "secret", 86400000);
    }

    @Test
    void testRegister() {
        User user = new User();
        user.setUsername("test");
        user.setEmail("test@example.com");
        user.setPassword("encoded");
        when(userRepository.save(any(User.class))).thenReturn(user);

        
    }

    @Test
    void testAuthenticateSuccess() {
        User user = new User();
        user.setUsername("test");
        user.setEmail("test@example.com");
        user.setPassword(passwordEncoder.encode("password"));
        when(userRepository.findByEmail("test@example.com")).thenReturn(Optional.of(user));

        AuthResponse response = authService.authenticate("test@example.com", "password");
        assertNotNull(response);
        assertNotNull(response.getToken());
        assertNotNull(response.getUser());
        assertEquals("test", response.getUser().getUsername());
        assertEquals("test@example.com", response.getUser().getEmail());
    }

    @Test
    void testAuthenticateFailure() {
        when(userRepository.findByEmail("test@example.com")).thenReturn(Optional.empty());
        assertThrows(RuntimeException.class, () -> authService.authenticate("test@example.com", "password"));
    }
}