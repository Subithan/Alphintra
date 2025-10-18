package com.alphintra.auth_service.controller;

import com.alphintra.auth_service.dto.KycDocumentRequest;
import com.alphintra.auth_service.service.KycService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/kyc")
public class KycController {
  private final KycService kycService;

  public KycController(KycService kycService) {
    this.kycService = kycService;
  }

  @PostMapping("/documents")
  public ResponseEntity<String> submitKycDocument(
      @AuthenticationPrincipal UserDetails principal,
      @Valid @RequestBody KycDocumentRequest request) {
    kycService.submitKycDocument(principal.getUsername(), request);
    return ResponseEntity.accepted().body("KYC document submission initiated");
  }

  @GetMapping("/status")
  public ResponseEntity<String> getKycStatus(@AuthenticationPrincipal UserDetails principal) {
    return ResponseEntity.ok(kycService.getKycStatus(principal.getUsername()));
  }
}
