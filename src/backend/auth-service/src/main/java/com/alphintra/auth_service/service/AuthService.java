package com.alphintra.auth_service.service;

import com.alphintra.auth_service.dto.AuthRequest;
import com.alphintra.auth_service.dto.AuthResponse;
import com.alphintra.auth_service.dto.RegisterRequest;
import com.alphintra.auth_service.entity.Role;
import com.alphintra.auth_service.entity.User;
import com.alphintra.auth_service.exception.InvalidCredentialsException;
import com.alphintra.auth_service.exception.ResourceNotFoundException;
import com.alphintra.auth_service.exception.UserAlreadyExistsException;
import com.alphintra.auth_service.mapper.UserMapper;
import com.alphintra.auth_service.repository.RoleRepository;
import com.alphintra.auth_service.repository.UserRepository;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import java.time.Instant;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import javax.crypto.SecretKey;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class AuthService {

  private static final Logger log = LoggerFactory.getLogger(AuthService.class);

  private final UserRepository userRepository;
  private final RoleRepository roleRepository;
  private final PasswordEncoder passwordEncoder;
  private final SecretKey signingKey;
  private final long jwtExpiration;

  public AuthService(
      UserRepository userRepository,
      RoleRepository roleRepository,
      PasswordEncoder passwordEncoder,
      @Value("${jwt.secret}") String jwtSecret,
      @Value("${jwt.expiration}") long jwtExpiration) {
    this.userRepository = userRepository;
    this.roleRepository = roleRepository;
    this.passwordEncoder = passwordEncoder;
    this.signingKey = Keys.hmacShaKeyFor(Decoders.BASE64.decode(jwtSecret));
    this.jwtExpiration = jwtExpiration;
  }

  @Transactional
  public AuthResponse register(RegisterRequest request) {
    if (userRepository.existsByUsername(request.getUsername())) {
      throw new UserAlreadyExistsException("Username already in use");
    }
    if (userRepository.existsByEmail(request.getEmail())) {
      throw new UserAlreadyExistsException("Email already in use");
    }

    User user = new User();
    user.setUsername(request.getUsername());
    user.setEmail(request.getEmail());
    user.setPassword(passwordEncoder.encode(request.getPassword()));
    user.setFirstName(request.getFirstName());
    user.setLastName(request.getLastName());
    user.setKycStatus("NOT_STARTED");

    Role defaultRole =
        roleRepository
            .findByName("USER")
            .orElseThrow(() -> new ResourceNotFoundException("Default role USER is missing"));
    user.getRoles().add(defaultRole);

    User saved = userRepository.save(user);
    String token = buildToken(saved.getUsername(), saved.getRoles(), saved.getId());
    log.info("Registered new user with username={}", saved.getUsername());
    return new AuthResponse(token, UserMapper.toProfile(saved));
  }

  public AuthResponse authenticate(AuthRequest request) {
    User user =
        userRepository
            .findByEmail(request.getEmail())
            .orElseThrow(() -> new InvalidCredentialsException("Invalid email or password"));
    if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
      throw new InvalidCredentialsException("Invalid email or password");
    }
    String token = buildToken(user.getUsername(), user.getRoles(), user.getId());
    return new AuthResponse(token, UserMapper.toProfile(user));
  }

  // All JWT validation (validate/introspect) removed; only issuing tokens remains.

  private String buildToken(String subject, Set<Role> roles, Long userId) {
    Map<String, Object> claims = new HashMap<>();
    claims.put("roles", roles.stream().map(Role::getName).toList());
    claims.put("user_id", userId); // Add user ID as a claim

    Instant now = Instant.now();
    return Jwts.builder()
        .setClaims(claims)
        .setSubject(subject)
        .setIssuedAt(Date.from(now))
        .setExpiration(Date.from(now.plusMillis(jwtExpiration)))
        .signWith(signingKey, SignatureAlgorithm.HS512)
        .compact();
  }
}
