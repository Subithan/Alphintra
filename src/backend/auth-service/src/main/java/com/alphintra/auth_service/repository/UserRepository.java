// Path:
// Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/repository/UserRepository.java
// Purpose: JPA repository for User entity, supporting authentication and profile queries.

package com.alphintra.auth_service.repository;

import com.alphintra.auth_service.entity.User;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserRepository extends JpaRepository<User, Long> {
  Optional<User> findByUsername(String username);

  Optional<User> findByEmail(String email);

  boolean existsByUsername(String username);

  boolean existsByEmail(String email);
}
