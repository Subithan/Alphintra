# Multi-stage Docker build for Customer Support Service with optimized caching

# Build stage with Maven cache optimization
FROM maven:3.9.6-eclipse-temurin-17 AS builder

WORKDIR /app

# Copy pom.xml first for dependency caching
COPY pom.xml .

# Download and cache dependencies in separate layers
RUN mvn dependency:go-offline -B
RUN mvn dependency:resolve -B
RUN mvn dependency:sources -B

# Copy source code last to maximize cache hits on code changes
COPY src ./src

# Build with optimizations - skip clean for faster incremental builds
RUN mvn package -DskipTests -B \
    -Dmaven.javadoc.skip=true \
    -Dmaven.compile.fork=true \
    -Dmaven.compiler.maxmem=1024m

# Extract JAR layers for better Docker layer caching
WORKDIR /app/target/dependency
RUN jar -xf ../*.jar

# Runtime stage using Google's distroless image (minimal and secure)
FROM gcr.io/distroless/java17-debian12:nonroot

# Copy dependencies and classes in separate layers for better caching
COPY --from=builder /app/target/dependency/BOOT-INF/lib /app/lib
COPY --from=builder /app/target/dependency/META-INF /app/META-INF
COPY --from=builder /app/target/dependency/BOOT-INF/classes /app

# Set working directory
WORKDIR /app

# Expose ports
EXPOSE 8010 8085

# Set JVM options optimized for containers and minimal memory usage
ENV JAVA_OPTS="-XX:+UseContainerSupport \
                -XX:MaxRAMPercentage=75.0 \
                -XX:+UseG1GC \
                -XX:+UseStringDeduplication \
                -XX:+OptimizeStringConcat \
                -Xss256k \
                -XX:MetaspaceSize=64m \
                -XX:MaxMetaspaceSize=128m \
                -XX:+TieredCompilation \
                -XX:TieredStopAtLevel=1"

# Run the application using the classpath (more efficient than fat JAR)
ENTRYPOINT ["java", "-cp", "/app:/app/lib/*", "com.alphintra.customersupport.CustomerSupportApplication"]

# Labels for metadata
LABEL org.opencontainers.image.title="Alphintra Customer Support Service"
LABEL org.opencontainers.image.description="Customer Support Service for Alphintra Trading Platform (Distroless)"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.vendor="Alphintra"
LABEL org.opencontainers.image.base.name="gcr.io/distroless/java17-debian12:nonroot"