// Path: Alphintra/src/backend/auth-service/src/test/java/com/alphintra/auth_service/service/KycServiceTest.java
// Purpose: Unit tests for KycService, updated to use the standard Maven test directory.

package com.alphintra.auth_service.service;

import com.alphintra.auth_service.dto.KycDocumentRequest;
import com.alphintra.auth_service.entity.User;
import com.alphintra.auth_service.repository.KycDocumentRepository;
import com.alphintra.auth_service.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class KycServiceTest {
    private UserRepository userRepository;
    private KycDocumentRepository kycDocumentRepository;
    private KycService kycService;

    @BeforeEach
    void setUp() {
        userRepository = mock(UserRepository.class);
        kycDocumentRepository = mock(KycDocumentRepository.class);
        kycService = new KycService(userRepository, kycDocumentRepository);
    }

    @Test
    void testSubmitKycDocument() {
        User user = new User();
        user.setId(1L);
        when(userRepository.findById(1L)).thenReturn(Optional.of(user));
        KycDocumentRequest request = new KycDocumentRequest();
        request.setDocumentType("PASSPORT");

        kycService.submitKycDocument(1L, request);
        verify(kycDocumentRepository).save(any());
        verify(userRepository).save(user);
        assertEquals("PENDING", user.getKycStatus());
    }

    @Test
    void testGetKycStatus() {
        User user = new User();
        user.setId(1L);
        user.setKycStatus("PENDING");
        when(userRepository.findById(1L)).thenReturn(Optional.of(user));

        String status = kycService.getKycStatus(1L);
        assertEquals("PENDING", status);
    }
}