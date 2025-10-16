package com.alphintra.auth_service.controller;

import com.alphintra.auth_service.dto.UserProfile;
import com.alphintra.auth_service.dto.UserUpdateRequest;
import com.alphintra.auth_service.entity.User;
import com.alphintra.auth_service.exception.ResourceNotFoundException;
import com.alphintra.auth_service.mapper.UserMapper;
import com.alphintra.auth_service.repository.UserRepository;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/users")
public class UserController {

  private final UserRepository userRepository;

  public UserController(UserRepository userRepository) {
    this.userRepository = userRepository;
  }

  @GetMapping("/me")
  public ResponseEntity<UserProfile> getProfile(@AuthenticationPrincipal UserDetails principal) {
    User user = loadUser(principal);
    return ResponseEntity.ok(UserMapper.toProfile(user));
  }

  @PutMapping("/me")
  public ResponseEntity<UserProfile> updateProfile(
      @AuthenticationPrincipal UserDetails principal,
      @Valid @RequestBody UserUpdateRequest request) {
    User user = loadUser(principal);
    if (request.getFirstName() != null) {
      user.setFirstName(request.getFirstName());
    }
    if (request.getLastName() != null) {
      user.setLastName(request.getLastName());
    }
    if (request.getDateOfBirth() != null) {
      user.setDateOfBirth(request.getDateOfBirth());
    }
    if (request.getPhoneNumber() != null) {
      user.setPhoneNumber(request.getPhoneNumber());
    }
    if (request.getAddress() != null) {
      user.setAddress(request.getAddress());
    }
    User saved = userRepository.save(user);
    return ResponseEntity.ok(UserMapper.toProfile(saved));
  }

  private User loadUser(UserDetails principal) {
    return userRepository
        .findByUsername(principal.getUsername())
        .orElseThrow(() -> new ResourceNotFoundException("Authenticated user not found"));
  }
}
