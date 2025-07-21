# Path: Alphintra/src/backend/auth-service/Dockerfile
# Purpose: Docker configuration for Spring Boot and Flyway, using gcr.io/distroless/java17-debian12 for consistency.

# Stage 1: Build the Java application
FROM maven:3.9.9-eclipse-temurin-17 AS builder
WORKDIR /app
COPY pom.xml .
COPY src ./src
# Ensure Maven build is clean and packages the application, skipping tests for speed
RUN mvn clean package -DskipTests

# Stage 2: Create minimal distroless image for the application runtime
FROM gcr.io/distroless/java17-debian12
WORKDIR /app

# Copy application files from the builder stage
# Corrected: Copy the generated JAR and rename it to auth-service.jar
COPY --from=builder /app/target/auth-service-0.0.1-SNAPSHOT.jar /app/auth-service.jar

# Expose the port your Spring Boot application listens on, matching application.yml and docker-compose
EXPOSE 8009

# Set environment variables with defaults. These can be overridden by docker-compose.
ENV SPRING_PROFILES_ACTIVE=prod
ENV DATABASE_URL=postgresql://alphintra:alphintra123@postgres:5432/alphintra-auth-service
ENV REDIS_URL=redis://:redis123@redis:6379
ENV KAFKA_BOOTSTRAP_SERVERS=kafka:29092
ENV JWT_SECRET=your_strong_default_jwt_secret 
# IMPORTANT: Use a truly random secret in production

# Run Spring Boot executable JAR
# Corrected: Reference the JAR file by its actual copied name
ENTRYPOINT ["java", "-jar", "auth-service.jar"]




# # Path: Alphintra/src/backend/auth-service/Dockerfile
# # Purpose: Docker configuration for Spring Boot and Flyway, using gcr.io/distroless/java17-debian12 for consistency.

# # Stage 1: Build the Java application
# FROM maven:3.9.9-eclipse-temurin-17 AS builder
# WORKDIR /app
# COPY pom.xml .
# COPY src ./src
# RUN mvn clean package -DskipTests

# # Stage 2: Create minimal distroless image
# FROM gcr.io/distroless/java17-debian12
# WORKDIR /app
# COPY --from=builder /app/target/auth-service-0.0.1-SNAPSHOT.jar /app/auth-service.jar
# EXPOSE 8080
# # ENTRYPOINT ["java", "-jar", "/app/auth-service.jar"]
# ENTRYPOINT ["java", "-jar", "app.jar"]


