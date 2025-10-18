package com.alphintra.auth_service.mapper;

import com.alphintra.auth_service.dto.UserProfile;
import com.alphintra.auth_service.entity.Role;
import com.alphintra.auth_service.entity.User;
import java.util.Set;
import java.util.stream.Collectors;

public final class UserMapper {

  private UserMapper() {}

  public static UserProfile toProfile(User user) {
    Set<String> roleNames =
        user.getRoles().stream().map(Role::getName).collect(Collectors.toUnmodifiableSet());
    return new UserProfile(
        user.getId(),
        user.getUsername(),
        user.getEmail(),
        user.getFirstName(),
        user.getLastName(),
        user.getKycStatus(),
        roleNames);
  }
}
