import java.io.ByteArrayOutputStream

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

// Resolves the repo's main .git directory (handles worktrees and the case where
// fiap-secure-systems lives inside a parent monorepo whose .git is one level up).
fun gitCommonDir(): File {
    val out = ByteArrayOutputStream()
    exec {
        commandLine("git", "rev-parse", "--git-common-dir")
        workingDir = rootDir
        standardOutput = out
    }
    val raw = out.toString(Charsets.UTF_8).trim()
    val resolved = if (File(raw).isAbsolute) File(raw) else rootDir.resolve(raw)
    return resolved.canonicalFile
}

// Copies commit-msg → <git-common-dir>/hooks/commit-msg so Spotless runs on every
// commit (see CONTRIBUTING.md). Auto-runs on first compileJava in any module.
tasks.register<Copy>("installGitHooks") {
    description = "Installs the commit-msg Git hook into the repo's .git/hooks directory."
    group = "git hooks"
    val source = rootProject.file("commit-msg")
    from(source)
    into(layout.dir(provider { File(gitCommonDir(), "hooks") }))
    fileMode = "755".toInt(8)
    inputs.file(source)
    onlyIf { source.exists() }
}

subprojects {
    plugins.withId("java") {
        tasks.matching { it.name == "compileJava" }.configureEach {
            dependsOn(rootProject.tasks.named("installGitHooks"))
        }
    }
}
