// Path:
// Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/repository/KycDocumentRepository.java
// Purpose: JPA repository for KycDocument entity.

package com.alphintra.auth_service.repository;

import com.alphintra.auth_service.entity.KycDocument;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface KycDocumentRepository extends JpaRepository<KycDocument, Long> {
  List<KycDocument> findByUserId(Long userId);
}
