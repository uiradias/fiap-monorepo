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
// Returns null when git is unavailable or no .git is reachable — e.g. inside the
// Docker build images, which neither install git nor receive a .git directory.
fun gitCommonDir(): File? {
    val out = ByteArrayOutputStream()
    val result = exec {
        commandLine("git", "rev-parse", "--git-common-dir")
        workingDir = rootDir
        standardOutput = out
        errorOutput = ByteArrayOutputStream()
        isIgnoreExitValue = true
    }
    if (result.exitValue != 0) return null
    val raw = out.toString(Charsets.UTF_8).trim()
    if (raw.isEmpty()) return null
    val resolved = if (File(raw).isAbsolute) File(raw) else rootDir.resolve(raw)
    return resolved.canonicalFile
}

val gitHooksDir: File? = runCatching { gitCommonDir() }.getOrNull()

// Copies commit-msg → <git-common-dir>/hooks/commit-msg so Spotless runs on every
// commit (see CONTRIBUTING.md). Auto-runs on first compileJava in any module when
// a git checkout is reachable; silently skipped in Docker / CI build images.
tasks.register<Copy>("installGitHooks") {
    description = "Installs the commit-msg Git hook into the repo's .git/hooks directory."
    group = "git hooks"
    val source = rootProject.file("commit-msg")
    from(source)
    into(layout.dir(provider { gitHooksDir?.resolve("hooks") }))
    fileMode = "755".toInt(8)
    inputs.file(source)
    onlyIf { source.exists() && gitHooksDir != null }
}

subprojects {
    plugins.withId("java") {
        tasks.matching { it.name == "compileJava" }.configureEach {
            if (gitHooksDir != null) {
                dependsOn(rootProject.tasks.named("installGitHooks"))
            }
        }
    }
}
