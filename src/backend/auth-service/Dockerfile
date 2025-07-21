# Path: Alphintra/src/backend/auth-service/Dockerfile
# Purpose: Docker configuration for Spring Boot and Flyway, using gcr.io/distroless/java17-debian12 for consistency.

# Stage 1: Build the Java application
FROM maven:3.9.9-eclipse-temurin-17 AS builder
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

# Stage 2: Create minimal distroless image
FROM gcr.io/distroless/java17-debian12
WORKDIR /app
COPY --from=builder /app/target/auth-service-0.0.1-SNAPSHOT.jar /app/auth-service.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/auth-service.jar"]