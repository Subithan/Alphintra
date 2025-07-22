// Path: Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/controller/UserController.java
// Purpose: REST controller for user profile management (/api/users/me).

package com.alphintra.auth_service.controller;

import com.alphintra.auth_service.dto.UserUpdateRequest;
import com.alphintra.auth_service.entity.User;
import com.alphintra.auth_service.repository.UserRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
public class UserController {
    private final UserRepository userRepository;

    public UserController(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @GetMapping("/me")
    public ResponseEntity<User> getProfile(@AuthenticationPrincipal User user) {
        return ResponseEntity.ok(user);
    }

    @PutMapping("/me")
    public ResponseEntity<User> updateProfile(@AuthenticationPrincipal User user, @RequestBody UserUpdateRequest request) {
        user.setFirstName(request.getFirstName());
        user.setLastName(request.getLastName());
        user.setDateOfBirth(request.getDateOfBirth());
        user.setPhoneNumber(request.getPhoneNumber());
        user.setAddress(request.getAddress());
        user.setUpdatedAt(java.time.LocalDateTime.now());
        return ResponseEntity.ok(userRepository.save(user));
    }
}