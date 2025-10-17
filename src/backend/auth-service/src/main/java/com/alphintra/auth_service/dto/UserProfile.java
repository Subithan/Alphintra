package com.alphintra.auth_service.dto;

import java.util.Set;

public record UserProfile(
    Long id,
    String username,
    String email,
    String firstName,
    String lastName,
    String kycStatus,
    Set<String> roles) {}
