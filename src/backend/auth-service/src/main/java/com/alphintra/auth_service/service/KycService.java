package com.alphintra.auth_service.service;

import com.alphintra.auth_service.dto.KycDocumentRequest;
import com.alphintra.auth_service.entity.KycDocument;
import com.alphintra.auth_service.entity.User;
import com.alphintra.auth_service.exception.ResourceNotFoundException;
import com.alphintra.auth_service.repository.KycDocumentRepository;
import com.alphintra.auth_service.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class KycService {
  private static final Logger log = LoggerFactory.getLogger(KycService.class);

  private final UserRepository userRepository;
  private final KycDocumentRepository kycDocumentRepository;

  public KycService(UserRepository userRepository, KycDocumentRepository kycDocumentRepository) {
    this.userRepository = userRepository;
    this.kycDocumentRepository = kycDocumentRepository;
  }

  public void submitKycDocument(String username, KycDocumentRequest request) {
    User user =
        userRepository
            .findByUsername(username)
            .orElseThrow(() -> new ResourceNotFoundException("User not found"));
    KycDocument document = new KycDocument();
    document.setUserId(user.getId());
    document.setDocumentType(request.getDocumentType());
    document.setStatus("PENDING");
    kycDocumentRepository.save(document);
    user.setKycStatus("PENDING");
    userRepository.save(user);
    log.info(
        "Enqueued KYC document for userId={} type={}", user.getId(), request.getDocumentType());
  }

  @Transactional(readOnly = true)
  public String getKycStatus(String username) {
    User user =
        userRepository
            .findByUsername(username)
            .orElseThrow(() -> new ResourceNotFoundException("User not found"));
    return user.getKycStatus();
  }
}
