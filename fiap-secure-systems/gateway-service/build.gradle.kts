plugins {
    java
    id("org.springframework.boot") version "3.4.0"
    id("io.spring.dependency-management") version "1.1.6"
    id("com.diffplug.spotless") version "6.25.0"
}

// Override Spring Boot 3.4.0's pinned testcontainers.version (1.20.4) — its bundled
// docker-java fails handshakes against modern Docker Desktop (returns 400 on /info).
extra["testcontainers.version"] = "1.21.3"

spotless {
    format("misc") {
        target("*.gradle.kts", "*.md", ".gitignore")
        trimTrailingWhitespace()
        indentWithSpaces(4)
        endWithNewline()
    }
    java {
        target("src/*/java/**/*.java")
        // googleJavaFormat with AOSP style — 4-space indent, 100-char line limit;
        // matches the existing codebase. The article uses eclipse() but Eclipse's
        // out-of-the-box settings would convert every line to tabs.
        googleJavaFormat("1.22.0").aosp().reflowLongStrings()
        importOrder("java", "javax", "org", "com", "")
        removeUnusedImports()
    }
}

java {
    toolchain {
        languageVersion.set(JavaLanguageVersion.of(21))
    }
}

dependencyManagement {
    imports {
        mavenBom("software.amazon.awssdk:bom:2.28.0")
        mavenBom("io.opentelemetry:opentelemetry-bom:1.42.1")
    }
}

dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.springframework.boot:spring-boot-starter-websocket")
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    implementation("org.springframework.boot:spring-boot-starter-actuator")
    implementation("org.springframework.boot:spring-boot-starter-validation")
    implementation("org.springframework.boot:spring-boot-starter-security")

    runtimeOnly("org.postgresql:postgresql")
    implementation("org.flywaydb:flyway-core")
    runtimeOnly("org.flywaydb:flyway-database-postgresql")

    implementation("software.amazon.awssdk:s3")
    implementation("software.amazon.awssdk:sqs")
    implementation("software.amazon.awssdk:sns")
    implementation("software.amazon.awssdk:url-connection-client")

    implementation("io.github.resilience4j:resilience4j-spring-boot3:2.2.0")
    implementation("com.bucket4j:bucket4j-core:8.10.1")

    implementation("com.auth0:java-jwt:4.4.0")

    implementation("com.networknt:json-schema-validator:1.5.1")

    implementation("io.micrometer:micrometer-tracing-bridge-otel")
    implementation("io.opentelemetry:opentelemetry-exporter-otlp")
    implementation("net.logstash.logback:logstash-logback-encoder:7.4")

    testImplementation("org.springframework.boot:spring-boot-starter-test") {
        exclude(group = "org.mockito", module = "mockito-core")
    }
    testImplementation("org.mockito:mockito-junit-jupiter:5.12.0")
    testImplementation("org.springframework.security:spring-security-test")
    testImplementation("org.assertj:assertj-core")
    testImplementation("org.junit.jupiter:junit-jupiter")
    testImplementation("org.awaitility:awaitility:4.2.2")
    testImplementation("com.squareup.okhttp3:mockwebserver:4.12.0")
}

sourceSets {
    val main by getting
    val test by getting
    @Suppress("unused")
    val integrationTest by creating {
        compileClasspath += main.output + test.output
        runtimeClasspath += main.output + test.output
    }
}

configurations {
    named("integrationTestImplementation") {
        extendsFrom(configurations["testImplementation"])
    }
    named("integrationTestRuntimeOnly") {
        extendsFrom(configurations["testRuntimeOnly"])
    }
}

dependencies {
    "integrationTestImplementation"(platform("org.testcontainers:testcontainers-bom:1.21.3"))
    "integrationTestImplementation"("org.testcontainers:junit-jupiter")
    "integrationTestImplementation"("org.testcontainers:postgresql")
    "integrationTestImplementation"("org.testcontainers:localstack")
}

val integrationTest = tasks.register<Test>("integrationTest") {
    description = "Runs Testcontainers integration tests."
    group = "verification"
    testClassesDirs = sourceSets["integrationTest"].output.classesDirs
    classpath = sourceSets["integrationTest"].runtimeClasspath
    shouldRunAfter("test")
    useJUnitPlatform()
    systemProperty("spring.profiles.active", "test")
    // docker-java's default API version (1.32) is below Docker Desktop's minimum (1.40),
    // and the `/info` probe happens before docker-java would auto-negotiate via `/version`.
    // The `api.version` system property is the documented override docker-java reads.
    // For socket resolution, we rely on Testcontainers' default (DOCKER_HOST env var, else
    // /var/run/docker.sock). Set DOCKER_HOST explicitly if Docker Desktop's socket layout
    // ever makes /var/run/docker.sock unresponsive.
    systemProperty("api.version", "1.43")
}

tasks.named<Test>("test") {
    useJUnitPlatform()
}

tasks.check {
    dependsOn(integrationTest)
}

tasks.named<org.springframework.boot.gradle.tasks.bundling.BootJar>("bootJar") {
    archiveBaseName.set("gateway-service")
}
