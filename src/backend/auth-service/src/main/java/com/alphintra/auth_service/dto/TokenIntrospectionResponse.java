package com.alphintra.auth_service.dto;

import java.util.Collections;
import java.util.List;

public class TokenIntrospectionResponse {

  private boolean active;
  private String sub;
  private List<String> roles;
  private Long iat;
  private Long exp;

  public TokenIntrospectionResponse() {}

  public TokenIntrospectionResponse(boolean active, String sub, List<String> roles, Long iat, Long exp) {
    this.active = active;
    this.sub = sub;
    this.roles = roles;
    this.iat = iat;
    this.exp = exp;
  }

  public static TokenIntrospectionResponse inactive() {
    return new TokenIntrospectionResponse(false, null, Collections.emptyList(), null, null);
  }

  public boolean isActive() {
    return active;
  }

  public void setActive(boolean active) {
    this.active = active;
  }

  public String getSub() {
    return sub;
  }

  public void setSub(String sub) {
    this.sub = sub;
  }

  public List<String> getRoles() {
    return roles;
  }

  public void setRoles(List<String> roles) {
    this.roles = roles;
  }

  public Long getIat() {
    return iat;
  }

  public void setIat(Long iat) {
    this.iat = iat;
  }

  public Long getExp() {
    return exp;
  }

  public void setExp(Long exp) {
    this.exp = exp;
  }
}

