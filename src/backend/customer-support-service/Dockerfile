# Multi-stage Docker build for Customer Support Service

# Build stage
FROM maven:3.9-openjdk-17-slim AS builder

WORKDIR /app

# Copy pom.xml first for better caching
COPY pom.xml .

# Download dependencies (this layer will be cached if pom.xml hasn't changed)
RUN mvn dependency:go-offline -B

# Copy source code
COPY src ./src

# Build the application
RUN mvn clean package -DskipTests -B

# Runtime stage
FROM openjdk:17-jdk-slim

# Create non-root user for security
RUN groupadd -r alphintra && useradd --no-log-init -r -g alphintra alphintra

# Set working directory
WORKDIR /app

# Copy the built JAR from builder stage
COPY --from=builder /app/target/customer-support-service-*.jar app.jar

# Change ownership to non-root user
RUN chown alphintra:alphintra app.jar

# Switch to non-root user
USER alphintra

# Expose port
EXPOSE 8085

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8085/api/support/actuator/health || exit 1

# Set JVM options for containerized environment
ENV JAVA_OPTS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0 -XX:+UseG1GC"

# Run the application
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

# Labels for metadata
LABEL org.opencontainers.image.title="Alphintra Customer Support Service"
LABEL org.opencontainers.image.description="Customer Support Service for Alphintra Trading Platform"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.vendor="Alphintra"