#!/bin/bash
echo "🚀 Starting Code Validation Service..."

# Check if Java is installed
if ! command -v java &> /dev/null; then
    echo "❌ Java is not installed. Please install Java 17 or higher."
    exit 1
fi

# Check if Maven is installed
if ! command -v mvn &> /dev/null; then
    echo "❌ Maven is not installed. Please install Maven."
    exit 1
fi

echo "✅ Java version: $(java -version 2>&1 | head -1)"
echo "✅ Maven version: $(mvn -version | head -1)"

# Change to service directory
cd "$(dirname "$0")"

echo "📦 Building the service..."
echo "⏳ This may take a few minutes to download dependencies..."

# Build the service (skip tests for faster build)
if mvn clean compile -DskipTests -q; then
    echo "✅ Build successful!"
    
    echo "🎯 Starting the Spring Boot application..."
    echo "🌐 Service will be available at: http://localhost:8005"
    echo "📊 Health check: http://localhost:8005/actuator/health"
    echo "📖 API docs: http://localhost:8005/swagger-ui.html"
    echo ""
    echo "Press Ctrl+C to stop the service"
    echo ""
    
    # Run the Spring Boot application
    mvn spring-boot:run -Dspring.profiles.active=development
else
    echo "❌ Build failed. Please check the Maven configuration."
    echo ""
    echo "💡 Troubleshooting tips:"
    echo "1. Make sure you have Java 17+ installed"
    echo "2. Check your internet connection for downloading dependencies"
    echo "3. Try running 'mvn clean' first"
    exit 1
fi