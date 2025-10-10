# Path: Alphintra/src/backend/auth-service/Dockerfile
# Purpose: Docker configuration for Spring Boot and Flyway, using gcr.io/distroless/java17-debian12 for consistency.
# Stage 1: Build the Java application
FROM maven:3.9.9-eclipse-temurin-17 AS builder
WORKDIR /app

# Copy pom.xml first and resolve dependencies to cache them
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Now copy source code and build
COPY src ./src
RUN mvn clean package -DskipTests -B

# Stage 2: Create minimal distroless image
FROM gcr.io/distroless/java17-debian12
WORKDIR /app
COPY --from=builder /app/target/auth-service-0.0.1-SNAPSHOT.jar app.jar
COPY --from=builder /app/src/main/resources/db/migration/V1__init_schema.sql init_database.sql

ENV SPRING_PROFILES_ACTIVE=standalone
ENV DATABASE_URL=jdbc:postgresql://alphintra:alphintra123@postgres:5432/alphintra_auth_service
ENV DB_USER=alphintra
ENV DB_PASSWORD=alphintra123

# JWT secret for signing tokens (should match other services)
ENV JWT_SECRET=U29tZVZlcnlTdHJvbmdTZWNyZXRLZXlXaXRoRW5vdWdoQnl0ZXNGb3JFUjUxMkFsZ29yaXRobS0xMjM0NTY3ODkwYWJjZGVmZ2hpams=

ENTRYPOINT ["java", "-jar", "app.jar"]
