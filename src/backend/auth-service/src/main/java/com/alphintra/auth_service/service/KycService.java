// Path: Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/service/KycService.java
// Purpose: Handles KYC document submission and status retrieval, as a placeholder for provider integration

package com.alphintra.auth_service.service;

import com.alphintra.auth_service.dto.KycDocumentRequest;
import com.alphintra.auth_service.entity.KycDocument;
import com.alphintra.auth_service.entity.User;
import com.alphintra.auth_service.repository.KycDocumentRepository;
import com.alphintra.auth_service.repository.UserRepository;
import org.springframework.stereotype.Service;

@Service
public class KycService {
    private final UserRepository userRepository;
    private final KycDocumentRepository kycDocumentRepository;

    public KycService(UserRepository userRepository, KycDocumentRepository kycDocumentRepository) {
        this.userRepository = userRepository;
        this.kycDocumentRepository = kycDocumentRepository;
    }

    public void submitKycDocument(Long userId, KycDocumentRequest request) {
        User user = userRepository.findById(userId)
            .orElseThrow(() -> new RuntimeException("User not found"));
        KycDocument document = new KycDocument();
        document.setUserId(userId);
        document.setDocumentType(request.getDocumentType());
        document.setStatus("PENDING");
        kycDocumentRepository.save(document);
        user.setKycStatus("PENDING");
        userRepository.save(user);
    }

    public String getKycStatus(Long userId) {
        User user = userRepository.findById(userId)
            .orElseThrow(() -> new RuntimeException("User not found"));
        return user.getKycStatus();
    }
}