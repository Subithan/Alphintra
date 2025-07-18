# Auth Service Microservice Development Plan

## 1. Overview

This document outlines the comprehensive development plan for creating the `auth-service`, a critical microservice within the Alphintra trading platform. This service will be responsible for user authentication, authorization, and management of user identities. It will be built using Spring Boot and Spring Security, leveraging JWT for stateless authentication.

## 2. Core Responsibilities

*   **User Registration:** Provide a secure endpoint for new users to register on the platform.
*   **User Authentication:** Authenticate users using email/password credentials and issue JWTs upon successful authentication.
*   **JWT Validation:** Provide an endpoint for the API Gateway to validate JWTs on incoming requests.
*   **Role-Based Access Control (RBAC):** Manage user roles and permissions, which will be encoded into the JWTs.
*   **User Profile Management:** Allow users to view and update their profile information.
*   **Secure Credential Storage:** Securely store user passwords using a strong hashing algorithm (e.g., bcrypt).

## 3. Technology Stack

*   **Language:** Java 21+
*   **Framework:** Spring Boot 3.x, Spring Security 6.x
*   **Database:** PostgreSQL
*   **Authentication:** JWT (JSON Web Tokens)
*   **Build Tool:** Maven

## 4. API Endpoints

The `auth-service` will expose the following REST endpoints:

*   `POST /api/auth/register`: Register a new user.
*   `POST /api/auth/login`: Authenticate a user and receive a JWT.
*   `POST /api/auth/validate`: (Internal endpoint for the API Gateway) Validate a JWT.
*   `GET /api/users/me`: Get the current user's profile.
*   `PUT /api/users/me`: Update the current user's profile.

## 5. Data Models

The service will primarily interact with the `users` and `roles` tables in the PostgreSQL database.

### User Model

```java
@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String username;

    @Column(nullable = false, unique = true)
    private String email;

    @Column(nullable = false)
    private String password;

    @ManyToMany(fetch = FetchType.EAGER)
    @JoinTable(
        name = "user_roles",
        joinColumns = @JoinColumn(name = "user_id"),
        inverseJoinColumns = @JoinColumn(name = "role_id")
    )
    private Set<Role> roles = new HashSet<>();

    // Getters and setters
}
```

### Role Model

```java
@Entity
@Table(name = "roles")
public class Role {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Enumerated(EnumType.STRING)
    @Column(length = 20)
    private ERole name;

    // Getters and setters
}
```

## 6. Security Implementation

*   **Password Hashing:** Passwords will be hashed using `BCryptPasswordEncoder`.
*   **JWT Generation:** JWTs will be generated upon successful login, containing user ID, username, and roles as claims.
*   **JWT Validation:** The service will provide a validation endpoint that the API Gateway will call to verify the signature and expiration of JWTs.
*   **Endpoint Security:** Spring Security will be used to secure endpoints, ensuring that only authenticated and authorized users can access protected resources.

## 7. Development Steps

### Step 1: Project Setup and Configuration
- Create Spring Boot project with Maven configuration
- Add dependencies for Spring Security, Spring Web, Spring Data JPA, PostgreSQL, JWT libraries
- Configure Eureka client for service discovery
- Set up application.yml with database and security configurations
- Create Docker configuration for containerization

### Step 2: Database Layer Implementation
- Design and implement User entity with JPA annotations
- Design and implement Role entity with JPA annotations
- Create UserRepository interface extending JpaRepository
- Create RoleRepository interface extending JpaRepository
- Set up database schema and migrations
- Configure PostgreSQL connection and JPA settings

### Step 3: Security Configuration
- Implement JWT utility class for token generation and validation
- Configure BCryptPasswordEncoder for password hashing
- Set up Spring Security configuration with JWT authentication
- Create JWT authentication filter
- Configure CORS settings for frontend communication

### Step 4: Authentication Services
- Implement AuthService for user registration and login logic
- Create UserService for user profile management
- Implement JWT token generation service
- Create JWT validation service for API Gateway
- Add role-based access control (RBAC) logic

### Step 5: REST Controller Implementation
- Create AuthController with registration and login endpoints
- Implement UserController for profile management endpoints
- Add JWT validation endpoint for internal API Gateway use
- Configure request/response DTOs for API contracts
- Add proper error handling and validation

### Step 6: Exception Handling and Validation
- Create custom exception classes for authentication errors
- Implement global exception handler with @ControllerAdvice
- Add input validation for registration and login requests
- Create proper HTTP response codes and error messages

### Step 7: Service Integration
- Configure Eureka client registration
- Set up health check endpoints with Spring Actuator
- Add monitoring and metrics collection
- Configure logging for authentication events

### Step 8: Testing Implementation
- Write unit tests for all service methods
- Create integration tests for REST endpoints
- Add security tests for JWT authentication
- Test database operations and repository methods
- Create test data fixtures and mock configurations

### Step 9: Documentation and API Contracts
- Generate OpenAPI/Swagger documentation
- Create API documentation for all endpoints
- Document authentication flow and JWT structure
- Add code comments and JavaDoc documentation

### Step 10: Deployment Preparation
- Create Dockerfile for containerization
- Set up Kubernetes deployment manifests
- Configure environment-specific properties
- Add database migration scripts
- Set up monitoring and logging configuration

This plan provides a structured approach to developing the auth-service microservice with proper authentication, authorization, and integration capabilities for the Alphintra trading platform.