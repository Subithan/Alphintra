# Multi-stage Dockerfile for Code Validation Service

# Stage 1: Build stage
FROM maven:3.9.5-openjdk-11-slim AS build

# Set working directory
WORKDIR /app

# Copy pom.xml first for better Docker layer caching
COPY pom.xml .

# Download dependencies
RUN mvn dependency:go-offline -B

# Copy source code
COPY src ./src

# Build the application
RUN mvn clean package -DskipTests -B

# Stage 2: Runtime stage
FROM openjdk:11-jre-slim

# Install Python for code validation
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install py_compile ast && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create application user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/logs /app/temp && \
    chown -R appuser:appuser /app

# Copy the built JAR from build stage
COPY --from=build /app/target/*.jar app.jar

# Change ownership of the JAR file
RUN chown appuser:appuser app.jar

# Switch to non-root user
USER appuser

# Expose the port
EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8005/actuator/health || exit 1

# Set JVM options for containerized environment
ENV JAVA_OPTS="-Xms256m -Xmx512m -XX:+UseG1GC -XX:G1HeapRegionSize=16m -XX:+UseStringDeduplication"

# Run the application
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -Djava.security.egd=file:/dev/./urandom -jar app.jar"]

# Labels for container metadata
LABEL maintainer="Alphintra Team"
LABEL version="1.0.0"
LABEL description="Code Validation and Security Scanning Service"
LABEL service="code-validation-service"