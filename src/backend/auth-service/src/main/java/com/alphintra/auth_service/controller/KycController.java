// Path: Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/controller/KycController.java
// Purpose: REST controller for KYC endpoints (/api/kyc/documents, /api/kyc/status).

package com.alphintra.auth_service.controller;

import com.alphintra.auth_service.dto.KycDocumentRequest;
import com.alphintra.auth_service.entity.User;
import com.alphintra.auth_service.service.KycService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/kyc")
public class KycController {
    private final KycService kycService;

    public KycController(KycService kycService) {
        this.kycService = kycService;
    }

    @PostMapping("/documents")
    public ResponseEntity<String> submitKycDocument(@AuthenticationPrincipal User user, @RequestBody KycDocumentRequest request) {
        kycService.submitKycDocument(user.getId(), request);
        return ResponseEntity.ok("KYC document submission initiated");
    }

    @GetMapping("/status")
    public ResponseEntity<String> getKycStatus(@AuthenticationPrincipal User user) {
        return ResponseEntity.ok(kycService.getKycStatus(user.getId()));
    }
}