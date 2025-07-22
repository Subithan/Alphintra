// Path: Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/dto/KycDocumentRequest.java
// Purpose: DTO for KYC document submission.

package com.alphintra.auth_service.dto;

public class KycDocumentRequest {
    private String documentType;

    public String getDocumentType() { return documentType; }
    public void setDocumentType(String documentType) { this.documentType = documentType; }
}