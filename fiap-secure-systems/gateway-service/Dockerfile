# syntax=docker/dockerfile:1.7
ARG JAVA_VERSION=21

# Build stage
FROM eclipse-temurin:${JAVA_VERSION}-jdk AS build
WORKDIR /workspace
COPY . .
RUN --mount=type=cache,target=/root/.gradle \
    ./gradlew :gateway-service:bootJar -x test

# Runtime stage
FROM eclipse-temurin:${JAVA_VERSION}-jre
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -r -u 1001 app
WORKDIR /app
COPY --from=build /workspace/gateway-service/build/libs/gateway-service-*.jar app.jar
USER app
EXPOSE 8080
ENV JAVA_OPTS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75"
ENTRYPOINT ["sh", "-c", "exec java $JAVA_OPTS -jar /app/app.jar"]
