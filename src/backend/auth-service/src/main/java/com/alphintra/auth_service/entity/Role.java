// Path: Alphintra/src/backend/auth-service/src/main/java/com/alphintra/auth_service/entity/Role.java
// Purpose: JPA entity for the roles table

package com.alphintra.auth_service.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "roles")
public class Role {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String name;

    // Getters and setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
}