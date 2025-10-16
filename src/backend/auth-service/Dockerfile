# syntax=docker/dockerfile:1.7
FROM gcr.io/distroless/java17-debian12:nonroot
WORKDIR /app

# Copy the pre-built JAR file
COPY target/auth-service-0.0.1-SNAPSHOT.jar app.jar

# Copy database initialization script for CloudSQL
COPY src/main/resources/db/migration/V1__init_schema.sql init_database.sql

# JVM options optimized for containerized environments
ENV JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=60.0 -Xms256m -Xmx768m"

# Spring Boot configuration
ENV SPRING_PROFILES_ACTIVE=standalone
ENV DATABASE_URL=
ENV DB_USER=
ENV DB_PASSWORD=

# JWT secret for signing tokens (should match other services)
ENV JWT_SECRET=U29tZVZlcnlTdHJvbmdTZWNyZXRLZXlXaXRoRW5vdWdoQnl0ZXNGb3JFUjUxMkFsZ29yaXRobS0xMjM0NTY3ODkwYWJjZGVmZ2hpams=

# Auth-service runs on port 8009
EXPOSE 8009

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8009/actuator/health || exit 1

# Set user to non-root for security
USER nonroot:nonroot

# Start the application
ENTRYPOINT ["java", "-jar", "/app/app.jar"]