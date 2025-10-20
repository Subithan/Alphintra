package com.alphintra.auth_service.controller;

import com.alphintra.auth_service.dto.UserProfile;
import com.alphintra.auth_service.dto.UserUpdateRequest;
import com.alphintra.auth_service.entity.User;
import com.alphintra.auth_service.exception.ResourceNotFoundException;
import com.alphintra.auth_service.mapper.UserMapper;
import com.alphintra.auth_service.repository.UserRepository;
import jakarta.validation.Valid;
import java.util.HashMap;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/users")
public class UserController {

  private static final Logger log = LoggerFactory.getLogger(UserController.class);

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
  public ResponseEntity<UserProfile> updateProfile(@Valid @RequestBody UserUpdateRequest request) {
    try {
      // Get user identifier from request
      if (request.getEmail() == null && request.getUsername() == null) {
        log.error("No user identifier provided in update request");
        throw new ResourceNotFoundException("User email or username is required");
      }

      User user;
      if (request.getEmail() != null) {
        user = userRepository.findByEmail(request.getEmail())
            .orElseThrow(() -> new ResourceNotFoundException("User not found with email: " + request.getEmail()));
      } else {
        user = userRepository.findByUsername(request.getUsername())
            .orElseThrow(() -> new ResourceNotFoundException("User not found with username: " + request.getUsername()));
      }

      log.info("Updating profile for user: {}", user.getUsername());

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
      log.info("Profile updated successfully for user: {}", saved.getUsername());
      return ResponseEntity.ok(UserMapper.toProfile(saved));
    } catch (Exception e) {
      log.error("Error updating profile: {}", e.getMessage(), e);
      throw e;
    }
  }

  @DeleteMapping("/account")
  @Transactional
  public ResponseEntity<Map<String, String>> deleteAccount(@RequestBody Map<String, String> request) {
    try {
      String email = request.get("email");
      String username = request.get("username");

      if (email == null && username == null) {
        log.error("No user identifier provided in delete request");
        throw new ResourceNotFoundException("User email or username is required");
      }

      User user;
      if (email != null) {
        user = userRepository.findByEmail(email)
            .orElseThrow(() -> new ResourceNotFoundException("User not found with email: " + email));
      } else {
        user = userRepository.findByUsername(username)
            .orElseThrow(() -> new ResourceNotFoundException("User not found with username: " + username));
      }

      String userIdentifier = user.getUsername();
      log.info("Attempting to delete account for username: {}", userIdentifier);

      // Clear the roles relationship before deleting
      user.getRoles().clear();
      userRepository.save(user);

      // Delete the user account
      userRepository.delete(user);
      userRepository.flush();

      log.info("User account deleted successfully for username: {}", userIdentifier);

      Map<String, String> response = new HashMap<>();
      response.put("message", "Account deleted successfully");
      response.put("username", userIdentifier);

      return ResponseEntity.ok(response);
    } catch (Exception e) {
      log.error("Error deleting user account: {}", e.getMessage(), e);
      throw new RuntimeException("Failed to delete account: " + e.getMessage());
    }
  }

  private User loadUser(UserDetails principal) {
    return userRepository
        .findByUsername(principal.getUsername())
        .orElseThrow(() -> new ResourceNotFoundException("Authenticated user not found"));
  }
}
