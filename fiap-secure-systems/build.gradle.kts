plugins {
    java
}

allprojects {
    group = "com.fiap"
    version = "0.1.0"
}

subprojects {
    apply(plugin = "java")
    extensions.configure<JavaPluginExtension> {
        toolchain {
            languageVersion.set(JavaLanguageVersion.of(21))
        }
    }
    repositories {
        mavenCentral()
    }
}
