// Path:
// Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/dto/KycDocumentRequest.java
// Purpose: DTO for KYC document submission.

package com.alphintra.auth_service.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class KycDocumentRequest {

  @NotBlank(message = "Document type is required")
  @Size(max = 50, message = "Document type must be at most 50 characters")
  private String documentType;

  public String getDocumentType() {
    return documentType;
  }

  public void setDocumentType(String documentType) {
    this.documentType = documentType;
  }
}
