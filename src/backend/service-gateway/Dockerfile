# syntax=docker/dockerfile:1.7
FROM gcr.io/distroless/java17-debian12:nonroot
WORKDIR /app
COPY target/service-gateway-0.0.1-SNAPSHOT.jar app.jar
ENV JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=60.0 -Xms256m -Xmx768m"
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]