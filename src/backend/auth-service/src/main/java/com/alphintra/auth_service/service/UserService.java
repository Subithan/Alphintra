package com.alphintra.auth_service.service;

import com.alphintra.auth_service.dto.UpdateProfileRequest;
import com.alphintra.auth_service.entity.User;
import com.alphintra.auth_service.exception.InvalidCredentialsException;
import com.alphintra.auth_service.exception.ResourceNotFoundException;
import com.alphintra.auth_service.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class UserService {

  private static final Logger log = LoggerFactory.getLogger(UserService.class);

  private final UserRepository userRepository;
  private final PasswordEncoder passwordEncoder;

  public UserService(UserRepository userRepository, PasswordEncoder passwordEncoder) {
    this.userRepository = userRepository;
    this.passwordEncoder = passwordEncoder;
  }


  public User getUserByUsername(String username) {
    return userRepository
        .findByUsername(username)
        .orElseThrow(() -> new ResourceNotFoundException("User not found: " + username));
  }

  /**
   * Update user profile
   */
  @Transactional
  public User updateProfile(String username, UpdateProfileRequest request) {
    User user = getUserByUsername(username);

    if (request.getFirstName() != null) {
      user.setFirstName(request.getFirstName());
    }
    if (request.getLastName() != null) {
      user.setLastName(request.getLastName());
    }
    if (request.getPhoneNumber() != null) {
      user.setPhoneNumber(request.getPhoneNumber());
    }
    if (request.getAddress() != null) {
      user.setAddress(request.getAddress());
    }

    User updatedUser = userRepository.save(user);
    log.info("User profile updated successfully for username: {}", username);
    return updatedUser;
  }

  /**
   * Delete user account - requires password confirmation
   */
  @Transactional
  public void deleteAccount(String username, String password) {
    User user = getUserByUsername(username);

    // Verify password before deletion
    if (!passwordEncoder.matches(password, user.getPassword())) {
      log.warn("Failed account deletion attempt for user: {} - Invalid password", username);
      throw new InvalidCredentialsException("Invalid password provided");
    }

    // Delete the user
    userRepository.delete(user);
    log.info("User account deleted successfully for username: {}", username);
  }

  /**
   * Check if user exists by username
   */
  public boolean existsByUsername(String username) {
    return userRepository.existsByUsername(username);
  }

  /**
   * Check if user exists by email
   */
  public boolean existsByEmail(String email) {
    return userRepository.existsByEmail(email);
  }
}
