// Path: Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/repository/KycDocumentRepository.java
// Purpose: JPA repository for KycDocument entity.

package com.alphintra.auth_service.repository;

import com.alphintra.auth_service.entity.KycDocument;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface KycDocumentRepository extends JpaRepository<KycDocument, Long> {
    List<KycDocument> findByUserId(Long userId);
}