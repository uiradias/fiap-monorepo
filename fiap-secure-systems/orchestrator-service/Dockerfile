# syntax=docker/dockerfile:1.7

# Build stage
FROM eclipse-temurin:21-jdk-alpine AS build
WORKDIR /workspace
COPY . .
RUN ./gradlew :orchestrator-service:bootJar --no-daemon

# Runtime stage
FROM eclipse-temurin:21-jre-alpine
ENV JAVA_OPTS=""
WORKDIR /app
COPY --from=build /workspace/orchestrator-service/build/libs/orchestrator-service-0.1.0.jar /app/app.jar

EXPOSE 8081
ENTRYPOINT ["sh", "-c", "exec java $JAVA_OPTS -jar /app/app.jar"]
