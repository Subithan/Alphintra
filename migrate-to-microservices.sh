#!/bin/bash
# migrate-to-microservices.sh
# Script to migrate Alphintra monolith to microservices architecture

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
BASE_DIR="$(pwd)"
SERVICES_DIR="$BASE_DIR/services"
INFRASTRUCTURE_DIR="$BASE_DIR/infrastructure"
SHARED_DIR="$BASE_DIR/shared"
BACKUP_DIR="$BASE_DIR/backup-$(date +%Y%m%d-%H%M%S)"

# Create backup
create_backup() {
    print_status "Creating backup of current codebase..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup existing directories
    if [ -d "src" ]; then
        cp -r src "$BACKUP_DIR/"
    fi
    
    if [ -d "backend" ]; then
        cp -r backend "$BACKUP_DIR/"
    fi
    
    if [ -d "frontend" ]; then
        cp -r frontend "$BACKUP_DIR/"
    fi
    
    # Backup configuration files
    for file in pom.xml build.gradle package.json requirements.txt go.mod; do
        if [ -f "$file" ]; then
            cp "$file" "$BACKUP_DIR/"
        fi
    done
    
    print_success "Backup created at $BACKUP_DIR"
}

# Create microservices directory structure
create_directory_structure() {
    print_status "Creating microservices directory structure..."
    
    # Main services directory
    mkdir -p "$SERVICES_DIR"
    
    # Individual microservices
    mkdir -p "$SERVICES_DIR/api-gateway"
    mkdir -p "$SERVICES_DIR/eureka-server"
    mkdir -p "$SERVICES_DIR/user-service"
    mkdir -p "$SERVICES_DIR/trading-service"
    mkdir -p "$SERVICES_DIR/strategy-service"
    mkdir -p "$SERVICES_DIR/no-code-service"
    mkdir -p "$SERVICES_DIR/audit-service"
    mkdir -p "$SERVICES_DIR/notification-service"
    
    # Infrastructure directory
    mkdir -p "$INFRASTRUCTURE_DIR/config-server"
    mkdir -p "$INFRASTRUCTURE_DIR/monitoring"
    mkdir -p "$INFRASTRUCTURE_DIR/logging"
    mkdir -p "$INFRASTRUCTURE_DIR/security"
    
    # Shared libraries
    mkdir -p "$SHARED_DIR/common"
    mkdir -p "$SHARED_DIR/security"
    mkdir -p "$SHARED_DIR/database"
    mkdir -p "$SHARED_DIR/messaging"
    mkdir -p "$SHARED_DIR/monitoring"
    
    # Create subdirectories for each service
    for service in api-gateway eureka-server user-service trading-service strategy-service no-code-service audit-service notification-service; do
        mkdir -p "$SERVICES_DIR/$service/src/main/java/com/alphintra/$service"
        mkdir -p "$SERVICES_DIR/$service/src/main/resources"
        mkdir -p "$SERVICES_DIR/$service/src/test/java/com/alphintra/$service"
        mkdir -p "$SERVICES_DIR/$service/docker"
        mkdir -p "$SERVICES_DIR/$service/k8s"
    done
    
    print_success "Directory structure created successfully."
}

# Move user management code
migrate_user_service() {
    print_status "Migrating User Service..."
    
    local service_dir="$SERVICES_DIR/user-service"
    
    # Look for existing user-related code
    if [ -d "src/main/java" ]; then
        # Java Spring Boot project
        find src/main/java -name "*User*" -type f -exec cp {} "$service_dir/src/main/java/com/alphintra/user/" \;
        find src/main/java -name "*Auth*" -type f -exec cp {} "$service_dir/src/main/java/com/alphintra/user/" \;
        find src/main/java -name "*Profile*" -type f -exec cp {} "$service_dir/src/main/java/com/alphintra/user/" \;
    fi
    
    # Create basic User Service structure
    cat > "$service_dir/src/main/java/com/alphintra/user/UserServiceApplication.java" << 'EOF'
package com.alphintra.user;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.netflix.eureka.EnableEurekaClient;

@SpringBootApplication
@EnableEurekaClient
public class UserServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(UserServiceApplication.class, args);
    }
}
EOF
    
    # Create pom.xml for User Service
    cat > "$service_dir/pom.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>
    
    <groupId>com.alphintra</groupId>
    <artifactId>user-service</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <name>Alphintra User Service</name>
    <description>User Management Microservice for Alphintra Platform</description>
    
    <properties>
        <java.version>17</java.version>
        <spring-cloud.version>2023.0.0</spring-cloud.version>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-netflix-eureka-client</artifactId>
        </dependency>
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>
    </dependencies>
    
    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>org.springframework.cloud</groupId>
                <artifactId>spring-cloud-dependencies</artifactId>
                <version>${spring-cloud.version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
EOF
    
    # Create application.yml
    cat > "$service_dir/src/main/resources/application.yml" << 'EOF'
server:
  port: 8081

spring:
  application:
    name: user-service
  profiles:
    active: k3d
  datasource:
    url: jdbc:postgresql://postgresql:5432/alphintra_users
    username: user_service
    password: ${DB_PASSWORD:user_service_password}
    driver-class-name: org.postgresql.Driver
  jpa:
    hibernate:
      ddl-auto: validate
    show-sql: false
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
        format_sql: true

eureka:
  client:
    service-url:
      defaultZone: http://eureka-server:8761/eureka/
    register-with-eureka: true
    fetch-registry: true
  instance:
    prefer-ip-address: true
    lease-renewal-interval-in-seconds: 30
    lease-expiration-duration-in-seconds: 90

management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
  endpoint:
    health:
      show-details: always
  metrics:
    export:
      prometheus:
        enabled: true

logging:
  level:
    com.alphintra: DEBUG
    org.springframework.security: DEBUG
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss} - %msg%n"
EOF
    
    print_success "User Service migration completed."
}

# Move trading engine code
migrate_trading_service() {
    print_status "Migrating Trading Service..."
    
    local service_dir="$SERVICES_DIR/trading-service"
    
    # Look for existing trading-related code
    if [ -d "src/main/java" ]; then
        find src/main/java -name "*Trading*" -type f -exec cp {} "$service_dir/src/main/java/com/alphintra/trading/" \;
        find src/main/java -name "*Order*" -type f -exec cp {} "$service_dir/src/main/java/com/alphintra/trading/" \;
        find src/main/java -name "*Portfolio*" -type f -exec cp {} "$service_dir/src/main/java/com/alphintra/trading/" \;
        find src/main/java -name "*Position*" -type f -exec cp {} "$service_dir/src/main/java/com/alphintra/trading/" \;
    fi
    
    # Create basic Trading Service structure
    cat > "$service_dir/src/main/java/com/alphintra/trading/TradingServiceApplication.java" << 'EOF'
package com.alphintra.trading;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.netflix.eureka.EnableEurekaClient;

@SpringBootApplication
@EnableEurekaClient
public class TradingServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(TradingServiceApplication.class, args);
    }
}
EOF
    
    # Create pom.xml for Trading Service
    cat > "$service_dir/pom.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>
    
    <groupId>com.alphintra</groupId>
    <artifactId>trading-service</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <name>Alphintra Trading Service</name>
    <description>Trading Engine Microservice for Alphintra Platform</description>
    
    <properties>
        <java.version>17</java.version>
        <spring-cloud.version>2023.0.0</spring-cloud.version>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-netflix-eureka-client</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.kafka</groupId>
            <artifactId>spring-kafka</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-redis</artifactId>
        </dependency>
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>
    </dependencies>
    
    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>org.springframework.cloud</groupId>
                <artifactId>spring-cloud-dependencies</artifactId>
                <version>${spring-cloud.version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
EOF
    
    print_success "Trading Service migration completed."
}

# Move strategy engine code
migrate_strategy_service() {
    print_status "Migrating Strategy Service..."
    
    local service_dir="$SERVICES_DIR/strategy-service"
    
    # Look for existing strategy-related code
    if [ -d "src/main/java" ]; then
        find src/main/java -name "*Strategy*" -type f -exec cp {} "$service_dir/src/main/java/com/alphintra/strategy/" \;
        find src/main/java -name "*Algorithm*" -type f -exec cp {} "$service_dir/src/main/java/com/alphintra/strategy/" \;
        find src/main/java -name "*Backtest*" -type f -exec cp {} "$service_dir/src/main/java/com/alphintra/strategy/" \;
    fi
    
    # Create basic Strategy Service structure
    cat > "$service_dir/src/main/java/com/alphintra/strategy/StrategyServiceApplication.java" << 'EOF'
package com.alphintra.strategy;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.netflix.eureka.EnableEurekaClient;

@SpringBootApplication
@EnableEurekaClient
public class StrategyServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(StrategyServiceApplication.class, args);
    }
}
EOF
    
    print_success "Strategy Service migration completed."
}

# Create API Gateway
create_api_gateway() {
    print_status "Creating API Gateway..."
    
    local service_dir="$SERVICES_DIR/api-gateway"
    
    # Create API Gateway application
    cat > "$service_dir/src/main/java/com/alphintra/gateway/ApiGatewayApplication.java" << 'EOF'
package com.alphintra.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.netflix.eureka.EnableEurekaClient;

@SpringBootApplication
@EnableEurekaClient
public class ApiGatewayApplication {
    public static void main(String[] args) {
        SpringApplication.run(ApiGatewayApplication.class, args);
    }
}
EOF
    
    # Create pom.xml for API Gateway
    cat > "$service_dir/pom.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>
    
    <groupId>com.alphintra</groupId>
    <artifactId>api-gateway</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <name>Alphintra API Gateway</name>
    <description>API Gateway for Alphintra Platform</description>
    
    <properties>
        <java.version>17</java.version>
        <spring-cloud.version>2023.0.0</spring-cloud.version>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-gateway</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-netflix-eureka-client</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-redis-reactive</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>
    </dependencies>
    
    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>org.springframework.cloud</groupId>
                <artifactId>spring-cloud-dependencies</artifactId>
                <version>${spring-cloud.version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
EOF
    
    print_success "API Gateway created successfully."
}

# Create Eureka Server
create_eureka_server() {
    print_status "Creating Eureka Server..."
    
    local service_dir="$SERVICES_DIR/eureka-server"
    
    # Create Eureka Server application
    cat > "$service_dir/src/main/java/com/alphintra/eureka/EurekaServerApplication.java" << 'EOF'
package com.alphintra.eureka;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.netflix.eureka.server.EnableEurekaServer;

@SpringBootApplication
@EnableEurekaServer
public class EurekaServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(EurekaServerApplication.class, args);
    }
}
EOF
    
    # Create pom.xml for Eureka Server
    cat > "$service_dir/pom.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>
    
    <groupId>com.alphintra</groupId>
    <artifactId>eureka-server</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <name>Alphintra Eureka Server</name>
    <description>Service Discovery Server for Alphintra Platform</description>
    
    <properties>
        <java.version>17</java.version>
        <spring-cloud.version>2023.0.0</spring-cloud.version>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-netflix-eureka-server</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>
    </dependencies>
    
    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>org.springframework.cloud</groupId>
                <artifactId>spring-cloud-dependencies</artifactId>
                <version>${spring-cloud.version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
EOF
    
    print_success "Eureka Server created successfully."
}

# Create shared libraries
create_shared_libraries() {
    print_status "Creating shared libraries..."
    
    # Common library
    mkdir -p "$SHARED_DIR/common/src/main/java/com/alphintra/common"
    
    cat > "$SHARED_DIR/common/pom.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.alphintra</groupId>
    <artifactId>alphintra-common</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <name>Alphintra Common Library</name>
    <description>Common utilities and models for Alphintra Platform</description>
    
    <properties>
        <java.version>17</java.version>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter</artifactId>
            <version>3.2.0</version>
        </dependency>
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-annotations</artifactId>
            <version>2.15.2</version>
        </dependency>
    </dependencies>
</project>
EOF
    
    # Security library
    mkdir -p "$SHARED_DIR/security/src/main/java/com/alphintra/security"
    
    cat > "$SHARED_DIR/security/pom.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.alphintra</groupId>
    <artifactId>alphintra-security</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <name>Alphintra Security Library</name>
    <description>Security utilities for Alphintra Platform</description>
    
    <properties>
        <java.version>17</java.version>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
            <version>3.2.0</version>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-api</artifactId>
            <version>0.11.5</version>
        </dependency>
    </dependencies>
</project>
EOF
    
    print_success "Shared libraries created successfully."
}

# Create root pom.xml for multi-module project
create_root_pom() {
    print_status "Creating root pom.xml..."
    
    cat > "pom.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.alphintra</groupId>
    <artifactId>alphintra-platform</artifactId>
    <version>1.0.0</version>
    <packaging>pom</packaging>
    
    <name>Alphintra Financial Platform</name>
    <description>Microservices-based Financial Trading Platform</description>
    
    <properties>
        <java.version>17</java.version>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <spring-boot.version>3.2.0</spring-boot.version>
        <spring-cloud.version>2023.0.0</spring-cloud.version>
    </properties>
    
    <modules>
        <!-- Shared Libraries -->
        <module>shared/common</module>
        <module>shared/security</module>
        
        <!-- Infrastructure Services -->
        <module>services/eureka-server</module>
        <module>services/api-gateway</module>
        
        <!-- Business Services -->
        <module>services/user-service</module>
        <module>services/trading-service</module>
        <module>services/strategy-service</module>
        <module>services/no-code-service</module>
        <module>services/audit-service</module>
        <module>services/notification-service</module>
    </modules>
    
    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-dependencies</artifactId>
                <version>${spring-boot.version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
            <dependency>
                <groupId>org.springframework.cloud</groupId>
                <artifactId>spring-cloud-dependencies</artifactId>
                <version>${spring-cloud.version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <version>${spring-boot.version}</version>
            </plugin>
        </plugins>
    </build>
</project>
EOF
    
    print_success "Root pom.xml created successfully."
}

# Create Docker files for each service
create_docker_files() {
    print_status "Creating Docker files..."
    
    for service in api-gateway eureka-server user-service trading-service strategy-service no-code-service audit-service notification-service; do
        cat > "$SERVICES_DIR/$service/Dockerfile" << EOF
FROM openjdk:17-jdk-slim

VOLUME /tmp

ARG JAR_FILE=target/*.jar
COPY \${JAR_FILE} app.jar

EXPOSE 8080

ENTRYPOINT ["java","-jar","/app.jar"]
EOF
    done
    
    print_success "Docker files created successfully."
}

# Create README files
create_documentation() {
    print_status "Creating documentation..."
    
    cat > "README.md" << 'EOF'
# Alphintra Financial Platform

A microservices-based financial trading platform built with Spring Boot and Spring Cloud.

## Architecture

The platform consists of the following microservices:

### Infrastructure Services
- **Eureka Server**: Service discovery and registration
- **API Gateway**: Single entry point for all client requests

### Business Services
- **User Service**: User management and authentication
- **Trading Service**: Order management and execution
- **Strategy Service**: Trading strategy management and backtesting
- **No-Code Service**: Visual strategy builder
- **Audit Service**: Audit logging and compliance
- **Notification Service**: Real-time notifications

## Getting Started

### Prerequisites
- Java 17+
- Maven 3.8+
- Docker
- K3D (for Kubernetes deployment)

### Local Development

1. Build all services:
   ```bash
   mvn clean install
   ```

2. Start infrastructure services:
   ```bash
   # Start Eureka Server
   cd services/eureka-server
   mvn spring-boot:run
   
   # Start API Gateway
   cd services/api-gateway
   mvn spring-boot:run
   ```

3. Start business services as needed

### Kubernetes Deployment

1. Setup K3D cluster:
   ```bash
   ./setup-k3d-cluster.sh
   ```

2. Deploy the platform:
   ```bash
   ./deploy-alphintra.sh
   ```

## Service Ports

- Eureka Server: 8761
- API Gateway: 8080
- User Service: 8081
- Trading Service: 8082
- Strategy Service: 8083
- No-Code Service: 8084
- Audit Service: 8085
- Notification Service: 8086

## Monitoring

- Prometheus: http://prometheus.alphintra.local
- Grafana: http://grafana.alphintra.local

## API Documentation

Once the services are running, API documentation is available at:
- http://api.alphintra.local/swagger-ui.html
EOF
    
    print_success "Documentation created successfully."
}

# Main migration function
main() {
    echo "=== Alphintra Microservices Migration ==="
    echo "This script will migrate your monolith to microservices architecture."
    echo ""
    
    # Parse command line arguments
    case "$1" in
        "--help")
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --help      Show this help message"
            echo "  --dry-run   Show what would be done without making changes"
            echo ""
            exit 0
            ;;
        "--dry-run")
            print_warning "DRY RUN MODE - No changes will be made"
            exit 0
            ;;
    esac
    
    # Confirm before proceeding
    read -p "This will modify your current codebase. Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Migration cancelled."
        exit 0
    fi
    
    # Execute migration steps
    create_backup
    create_directory_structure
    migrate_user_service
    migrate_trading_service
    migrate_strategy_service
    create_api_gateway
    create_eureka_server
    create_shared_libraries
    create_root_pom
    create_docker_files
    create_documentation
    
    print_success "Microservices migration completed successfully!"
    print_status "Backup created at: $BACKUP_DIR"
    print_status "Next steps:"
    echo "  1. Review the generated code and configurations"
    echo "  2. Update database connections and configurations"
    echo "  3. Build and test individual services"
    echo "  4. Deploy using ./deploy-alphintra.sh"
}

# Run main function with all arguments
main "$@"