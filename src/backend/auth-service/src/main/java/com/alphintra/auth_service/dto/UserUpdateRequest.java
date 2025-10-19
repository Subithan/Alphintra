// Path:
// Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/dto/UserUpdateRequest.java
// Purpose: DTO for updating user profile with KYC fields.

package com.alphintra.auth_service.dto;

import jakarta.validation.constraints.Past;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;

public class UserUpdateRequest {

  // User identifier (one of these is required)
  private String email;
  private String username;

  @Size(max = 50, message = "First name must be at most 50 characters")
  private String firstName;

  @Size(max = 50, message = "Last name must be at most 50 characters")
  private String lastName;

  @Past(message = "Date of birth must be in the past")
  private LocalDate dateOfBirth;

  @Pattern(
      regexp = "^$|^[+0-9\\- )(/]{7,20}$",
      message = "Phone number contains invalid characters")
  private String phoneNumber;

  @Size(max = 255, message = "Address must be at most 255 characters")
  private String address;

  public String getFirstName() {
    return firstName;
  }

  public void setFirstName(String firstName) {
    this.firstName = firstName;
  }

  public String getLastName() {
    return lastName;
  }

  public void setLastName(String lastName) {
    this.lastName = lastName;
  }

  public LocalDate getDateOfBirth() {
    return dateOfBirth;
  }

  public void setDateOfBirth(LocalDate dateOfBirth) {
    this.dateOfBirth = dateOfBirth;
  }

  public String getPhoneNumber() {
    return phoneNumber;
  }

  public void setPhoneNumber(String phoneNumber) {
    this.phoneNumber = phoneNumber;
  }

  public String getAddress() {
    return address;
  }

  public void setAddress(String address) {
    this.address = address;
  }

  public String getEmail() {
    return email;
  }

  public void setEmail(String email) {
    this.email = email;
  }

  public String getUsername() {
    return username;
  }

  public void setUsername(String username) {
    this.username = username;
  }
}
