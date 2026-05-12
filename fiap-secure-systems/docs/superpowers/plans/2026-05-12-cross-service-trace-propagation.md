# Cross-service trace propagation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every `make front-round-trip` produce one continuous Tempo trace spanning `gateway-service` → `orchestrator-service` → `smart-service`, so the session-lifecycle Grafana dashboard correlates per-session activity end to end.

**Architecture:** Smart-service (Python) already runs `BotocoreInstrumentor().instrument()` in `smart_service/infrastructure/observability.py:58`, which auto-injects `traceparent` into SQS `MessageAttributes`. The two Java services (gateway, orchestrator) build their `SqsClient` / `SnsClient` / `S3Client` beans without an OTel `ExecutionInterceptor`, so they neither inject nor extract `traceparent`. The fix is to add the OTel Java instrumentation library for AWS SDK v2 and wire `AwsSdkTelemetry`'s `ExecutionInterceptor` into the existing client builders. Spring Boot's Micrometer Tracing already exposes an `OpenTelemetry` bean (from the `micrometer-tracing-bridge-otel` we already use), so the interceptor wires onto the same SDK that's currently exporting OTLP traces.

**Tech Stack:** OpenTelemetry Java instrumentation `2.8.0-alpha` (matches our `opentelemetry-bom:1.42.1`), Spring Boot 3.4 Micrometer Tracing, AWS SDK v2 (BOM 2.28.0). No changes to Python, schemas, business logic, HMAC signing, or LocalStack bootstrap (SNS subscription already has `RawMessageDelivery=true`).

**Working directory:** `/Users/uiradias/Repository/fiap-monorepo/fiap-secure-systems`. All work is on `main`; no worktree needed.

---

## File map

```
fiap-secure-systems/
├── orchestrator-service/
│   ├── build.gradle.kts                                                 (Task 2)
│   └── src/main/java/com/fiap/orchestrator/infrastructure/config/
│       └── AwsSdkConfig.java                                            (Task 3)
├── gateway-service/
│   ├── build.gradle.kts                                                 (Task 2)
│   └── src/main/java/com/fiap/gateway/infrastructure/config/
│       └── AwsSdkConfig.java                                            (Task 4)
└── docs/superpowers/plans/
    └── 2026-05-12-cross-service-trace-propagation.md                    (this file)
```

---

## Task 1: Verify HTTP hop already propagates (no code change expected)

The spec says gateway → orchestrator HTTP via Spring `RestClient` should already propagate `traceparent` because Micrometer Tracing instruments Spring's HTTP clients automatically. Confirm before touching code so we know whether to scope-expand.

**Files:** none modified.

- [ ] **Step 1: Re-run the round trip to ensure fresh data in Tempo.**

Run: `make front-round-trip`
Expected: ends with `✓ front round-trip OK` and prints `sessionId=<uuid>`. Note the uuid.

- [ ] **Step 2: Query Tempo for the gateway's POST /sessions/.../finalize span.**

Run (replace `<sessionId>` with the value from Step 1):
```bash
curl -sS "http://localhost:3200/api/search?tags=service.name%3Dgateway-service&limit=20&start=$(date -v -2M +%s)&end=$(date +%s)" \
  | python3 -m json.tool | grep -E '"traceID"|"rootTraceName"' | head -30
```

Expected: a list of recent gateway traces. Pick one whose `rootTraceName` looks like a real request handler (e.g., `POST /sessions/{id}/finalize`, `POST /sessions`, `POST /auth/login`) — NOT `/actuator/health` and NOT `/`.

- [ ] **Step 3: Fetch that trace and count the distinct `service.name` values.**

Run (replace `<traceID>` with the id from Step 2):
```bash
curl -sS "http://localhost:3200/api/traces/<traceID>" \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
svcs=set()
for b in d.get('batches',[]):
    for a in b.get('resource',{}).get('attributes',[]):
        if a.get('key')=='service.name':
            svcs.add(a.get('value',{}).get('stringValue'))
print('services in this trace:', sorted(svcs))
"
```

Expected outcome — record which case applies:
- **Case A:** output shows `['gateway-service', 'orchestrator-service']` (or includes both). HTTP hop works. No HTTP-related change needed; continue to Task 2.
- **Case B:** output shows only `['gateway-service']`. HTTP hop does NOT propagate. **Stop and tell the human partner** — the design needs amending (likely a missing `ObservationRegistry` on `RestClient.Builder`). Do not proceed to Task 2 until this is resolved.

- [ ] **Step 4: No commit — this is a read-only verification.**

---

## Task 1.5: Fix gateway → orchestrator HTTP hop (added 2026-05-12 after Task 1 verification)

Task 1 verified Case B: the gateway's `OrchestratorClientPort` bean is built from `RestClient.builder()` — a static factory that returns an uninstrumented builder — instead of the Spring Boot–auto-configured `RestClient.Builder` bean (which carries the `ObservationRegistry` from Micrometer Tracing). Trace context is therefore not propagated on the outbound HTTP request to the orchestrator. Fix in one config method.

**Files:**
- Modify: `gateway-service/src/main/java/com/fiap/gateway/infrastructure/config/CompositionConfig.java:80-88` (one method: `orchestratorClient`)

- [ ] **Step 1: Edit `CompositionConfig.java`.**

Replace the existing `orchestratorClient` bean method (currently lines 80-88) with this version. The change is: add a `RestClient.Builder restClientBuilder` parameter (Spring injects the auto-configured bean) and use it instead of `RestClient.builder()`:

```java
    @Bean
    public OrchestratorClientPort orchestratorClient(
            @Value("${gateway.orchestrator.base-url}") String baseUrl,
            InternalHmacRequestSigner signer,
            Clock clock,
            @Value("${gateway.orchestrator.hmac-secret}") String secret,
            RestClient.Builder restClientBuilder) {
        return new OrchestratorRestClient(
                restClientBuilder.baseUrl(baseUrl).build(), signer, clock, secret);
    }
```

No other change. The existing `import org.springframework.web.client.RestClient;` at the top of the file already covers `RestClient.Builder` (it's a nested type).

- [ ] **Step 2: Compile-only check.**

```bash
cd gateway-service && ./gradlew :gateway-service:compileJava
```

Expected: `BUILD SUCCESSFUL`.

- [ ] **Step 3: Rebuild + restart gateway, then re-run Task 1's verification.**

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d --build gateway-service
until [ "$(docker inspect -f '{{.State.Health.Status}}' fss-gateway-service)" = "healthy" ]; do sleep 3; done
echo gateway HEALTHY
make front-round-trip || make front-round-trip
```

Capture the new `sessionId`. Then re-do Task 1 Step 2 (find a real-handler gateway trace) and Step 3 (fetch trace, count services).

Expected: Case A — `services in this trace: ['gateway-service', 'orchestrator-service']`. If it's still Case B, stop and escalate.

- [ ] **Step 4: Commit just this file.**

```bash
git add gateway-service/src/main/java/com/fiap/gateway/infrastructure/config/CompositionConfig.java
git commit -m "fix(gateway): inject RestClient.Builder so traceparent propagates to orchestrator"
```

---

## Task 2: Add OTel AWS SDK instrumentation BOM and library to both Java services

**Files:**
- Modify: `orchestrator-service/build.gradle.kts:36-41` and `:54-56` (BOM imports + new implementation line)
- Modify: `gateway-service/build.gradle.kts:36-41` and `:54-56` (same shape)

- [ ] **Step 1: Edit `orchestrator-service/build.gradle.kts`.**

In the `dependencyManagement.imports` block (currently lines 36-41), add the instrumentation BOM so it sits next to the existing two:

```kotlin
dependencyManagement {
    imports {
        mavenBom("software.amazon.awssdk:bom:2.28.0")
        mavenBom("io.opentelemetry:opentelemetry-bom:1.42.1")
        mavenBom("io.opentelemetry.instrumentation:opentelemetry-instrumentation-bom-alpha:2.8.0-alpha")
    }
}
```

Then in the `dependencies` block, immediately after the existing `software.amazon.awssdk:sns` line (currently line 55), add:

```kotlin
    implementation("io.opentelemetry.instrumentation:opentelemetry-aws-sdk-2.2")
```

- [ ] **Step 2: Make the identical edit in `gateway-service/build.gradle.kts`.**

Same BOM addition in `dependencyManagement.imports`. The `implementation` line goes right after the existing AWS SDK lines (gateway has `s3` and `sqs`, not `sns`).

- [ ] **Step 3: Verify both build files resolve the new artifact.**

Run from repo root:
```bash
cd orchestrator-service && ./gradlew :orchestrator-service:dependencies --configuration runtimeClasspath 2>&1 | grep "opentelemetry-aws-sdk-2.2" | head -3
```

Expected: at least one line like `+--- io.opentelemetry.instrumentation:opentelemetry-aws-sdk-2.2 -> 2.8.0-alpha` (the `-> 2.8.0-alpha` resolution coming from the BOM).

Then:
```bash
cd ../gateway-service && ./gradlew :gateway-service:dependencies --configuration runtimeClasspath 2>&1 | grep "opentelemetry-aws-sdk-2.2" | head -3
```
Same expectation.

If either fails (artifact not found): check the BOM version is exactly `2.8.0-alpha` — the alpha suffix is required for instrumentation modules. Do NOT remove the `-alpha`.

- [ ] **Step 4: Commit the build-file changes only.**

```bash
git add orchestrator-service/build.gradle.kts gateway-service/build.gradle.kts
git commit -m "build(java-services): add opentelemetry-aws-sdk-2.2 instrumentation"
```

---

## Task 3: Wire `AwsSdkTelemetry` interceptor in orchestrator's `AwsSdkConfig`

**Files:**
- Modify: `orchestrator-service/src/main/java/com/fiap/orchestrator/infrastructure/config/AwsSdkConfig.java` (entire file rewritten — small file, clean diff)

- [ ] **Step 1: Replace the file contents.**

Write `orchestrator-service/src/main/java/com/fiap/orchestrator/infrastructure/config/AwsSdkConfig.java` with this exact content:

```java
package com.fiap.orchestrator.infrastructure.config;

import java.net.URI;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.instrumentation.awssdk.v2_2.AwsSdkTelemetry;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.core.interceptor.ExecutionInterceptor;
import software.amazon.awssdk.http.urlconnection.UrlConnectionHttpClient;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.sns.SnsClient;
import software.amazon.awssdk.services.sqs.SqsClient;

@Configuration
public class AwsSdkConfig {

    @Bean
    public ExecutionInterceptor awsSdkOtelInterceptor(OpenTelemetry openTelemetry) {
        return AwsSdkTelemetry.builder(openTelemetry)
                .setCaptureExperimentalSpanAttributes(true)
                .setMessagingReceiveInstrumentationEnabled(true)
                .build()
                .newExecutionInterceptor();
    }

    @Bean
    public SqsClient sqsClient(
            @Value("${orchestrator.aws.endpoint-url}") String endpoint,
            @Value("${orchestrator.aws.region}") String region,
            @Value("${orchestrator.aws.access-key}") String accessKey,
            @Value("${orchestrator.aws.secret-key}") String secretKey,
            ExecutionInterceptor awsSdkOtelInterceptor) {
        return SqsClient.builder()
                .endpointOverride(URI.create(endpoint))
                .region(Region.of(region))
                .credentialsProvider(
                        StaticCredentialsProvider.create(
                                AwsBasicCredentials.create(accessKey, secretKey)))
                .httpClient(UrlConnectionHttpClient.create())
                .overrideConfiguration(c -> c.addExecutionInterceptor(awsSdkOtelInterceptor))
                .build();
    }

    @Bean
    public SnsClient snsClient(
            @Value("${orchestrator.aws.endpoint-url}") String endpoint,
            @Value("${orchestrator.aws.region}") String region,
            @Value("${orchestrator.aws.access-key}") String accessKey,
            @Value("${orchestrator.aws.secret-key}") String secretKey,
            ExecutionInterceptor awsSdkOtelInterceptor) {
        return SnsClient.builder()
                .endpointOverride(URI.create(endpoint))
                .region(Region.of(region))
                .credentialsProvider(
                        StaticCredentialsProvider.create(
                                AwsBasicCredentials.create(accessKey, secretKey)))
                .httpClient(UrlConnectionHttpClient.create())
                .overrideConfiguration(c -> c.addExecutionInterceptor(awsSdkOtelInterceptor))
                .build();
    }

    @Bean
    @Qualifier("analysisJobsQueueUrl")
    public String analysisJobsQueueUrl(@Value("${orchestrator.sqs.analysis-jobs-url}") String url) {
        return url;
    }

    @Bean
    @Qualifier("analysisResultsQueueUrl")
    public String analysisResultsQueueUrl(
            @Value("${orchestrator.sqs.analysis-results-url}") String url) {
        return url;
    }

    @Bean
    @Qualifier("analysisResultsDlqUrl")
    public String analysisResultsDlqUrl(
            @Value("${orchestrator.sqs.analysis-results-dlq-url}") String url) {
        return url;
    }

    @Bean
    @Qualifier("sessionEventsTopicArn")
    public String sessionEventsTopicArn(
            @Value("${orchestrator.sns.session-events-topic-arn}") String arn) {
        return arn;
    }
}
```

The changes are: one new `@Bean ExecutionInterceptor awsSdkOtelInterceptor(...)`, plus an extra `ExecutionInterceptor` parameter and `.overrideConfiguration(...)` line on each of `sqsClient` and `snsClient`. Everything else is byte-identical to the existing file.

Notes for the engineer:
- `setMessagingReceiveInstrumentationEnabled(true)` is required to get a span when the consumer calls `receiveMessage` — without it, no consumer-side span is created and `traceparent` extraction never happens.
- The lambda-style `overrideConfiguration` (AWS SDK v2 builder customization) is preferred over building a full `ClientOverrideConfiguration` because we don't have any other overrides to merge.

- [ ] **Step 2: Compile-only check.**

Run from repo root:
```bash
cd orchestrator-service && ./gradlew :orchestrator-service:compileJava
```

Expected: `BUILD SUCCESSFUL`. If you see `cannot find symbol: class AwsSdkTelemetry`, Task 2 wasn't completed correctly — go back and re-check the BOM + implementation lines.

- [ ] **Step 3: Commit just this file.**

```bash
git add orchestrator-service/src/main/java/com/fiap/orchestrator/infrastructure/config/AwsSdkConfig.java
git commit -m "feat(orchestrator): wire AwsSdkTelemetry interceptor for SQS/SNS context propagation"
```

---

## Task 4: Wire `AwsSdkTelemetry` interceptor in gateway's `AwsSdkConfig`

**Files:**
- Modify: `gateway-service/src/main/java/com/fiap/gateway/infrastructure/config/AwsSdkConfig.java` (entire file rewritten)

Gateway has SQS + S3 (no SNS). Apply the same interceptor to both clients so S3 spans also benefit from auto-instrumentation (the Python side already produces nicer S3 spans for free, so this brings parity).

- [ ] **Step 1: Replace the file contents.**

Write `gateway-service/src/main/java/com/fiap/gateway/infrastructure/config/AwsSdkConfig.java` with this exact content:

```java
package com.fiap.gateway.infrastructure.config;

import java.net.URI;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.instrumentation.awssdk.v2_2.AwsSdkTelemetry;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.core.interceptor.ExecutionInterceptor;
import software.amazon.awssdk.http.urlconnection.UrlConnectionHttpClient;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.sqs.SqsClient;

@Configuration
public class AwsSdkConfig {

    @Bean
    public ExecutionInterceptor awsSdkOtelInterceptor(OpenTelemetry openTelemetry) {
        return AwsSdkTelemetry.builder(openTelemetry)
                .setCaptureExperimentalSpanAttributes(true)
                .setMessagingReceiveInstrumentationEnabled(true)
                .build()
                .newExecutionInterceptor();
    }

    @Bean
    public S3Client s3Client(
            @Value("${gateway.aws.endpoint-url}") String endpoint,
            @Value("${gateway.aws.region}") String region,
            @Value("${gateway.aws.access-key}") String accessKey,
            @Value("${gateway.aws.secret-key}") String secretKey,
            ExecutionInterceptor awsSdkOtelInterceptor) {
        return S3Client.builder()
                .endpointOverride(URI.create(endpoint))
                .region(Region.of(region))
                .credentialsProvider(
                        StaticCredentialsProvider.create(
                                AwsBasicCredentials.create(accessKey, secretKey)))
                .forcePathStyle(true)
                .httpClient(UrlConnectionHttpClient.create())
                .overrideConfiguration(c -> c.addExecutionInterceptor(awsSdkOtelInterceptor))
                .build();
    }

    @Bean
    public SqsClient sqsClient(
            @Value("${gateway.aws.endpoint-url}") String endpoint,
            @Value("${gateway.aws.region}") String region,
            @Value("${gateway.aws.access-key}") String accessKey,
            @Value("${gateway.aws.secret-key}") String secretKey,
            ExecutionInterceptor awsSdkOtelInterceptor) {
        return SqsClient.builder()
                .endpointOverride(URI.create(endpoint))
                .region(Region.of(region))
                .credentialsProvider(
                        StaticCredentialsProvider.create(
                                AwsBasicCredentials.create(accessKey, secretKey)))
                .httpClient(UrlConnectionHttpClient.create())
                .overrideConfiguration(c -> c.addExecutionInterceptor(awsSdkOtelInterceptor))
                .build();
    }

    @Bean
    @Qualifier("sessionEventsQueueUrl")
    public String sessionEventsQueueUrl(@Value("${gateway.sqs.session-events-url}") String url) {
        return url;
    }
}
```

- [ ] **Step 2: Compile-only check.**

```bash
cd gateway-service && ./gradlew :gateway-service:compileJava
```

Expected: `BUILD SUCCESSFUL`.

- [ ] **Step 3: Commit just this file.**

```bash
git add gateway-service/src/main/java/com/fiap/gateway/infrastructure/config/AwsSdkConfig.java
git commit -m "feat(gateway): wire AwsSdkTelemetry interceptor for SQS/S3 context propagation"
```

---

## Task 5: Rebuild containers, restart, and verify end-to-end propagation

**Files:** none modified. Verification only.

- [ ] **Step 1: Rebuild + restart both Java services.**

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d --build orchestrator-service gateway-service
```

Expected: both containers transition to `healthy`. The build takes 2-4 min the first time.

- [ ] **Step 2: Wait for both to be healthy.**

```bash
until [ "$(docker inspect -f '{{.State.Health.Status}}' fss-orchestrator-service)" = "healthy" ] \
   && [ "$(docker inspect -f '{{.State.Health.Status}}' fss-gateway-service)" = "healthy" ]; do
  sleep 3
done
echo BOTH_HEALTHY
```

Expected: prints `BOTH_HEALTHY` within ~30s of compose finishing.

- [ ] **Step 3: Confirm neither service logged an OTel wiring error on startup.**

```bash
docker logs fss-orchestrator-service 2>&1 | grep -iE "AwsSdkTelemetry|ExecutionInterceptor|opentelemetry.*ERROR" | head
docker logs fss-gateway-service 2>&1     | grep -iE "AwsSdkTelemetry|ExecutionInterceptor|opentelemetry.*ERROR" | head
```

Expected: no output (silent success). If you see `BeanCreationException` or `NoClassDefFoundError`, Task 2's BOM line is wrong or wasn't committed.

- [ ] **Step 4: Run the round trip TWICE.**

First run may fail with `did not reach REPORT_READY (last=ANALYSIS_COMPLETED)` due to cold-start JIT warmup (already observed). Second run should succeed.

```bash
make front-round-trip || make front-round-trip
```

Expected: ends with `✓ front round-trip OK` and prints `sessionId=<uuid>`. Record the uuid as `<SID>`.

- [ ] **Step 5: Confirm `traceparent` is present in SQS message attributes (collector-side evidence).**

```bash
docker logs fss-otel-collector --tail 200 2>&1 | grep -iE "messaging\.|aws\.queue|sns" | head -10
```

Expected: lines mentioning `messaging.system: aws.sqs` and `messaging.destination` confirming producer spans are flowing. Absence here means the interceptor isn't firing — re-check Task 3 and Task 4.

- [ ] **Step 6: Verify cross-service trace in Tempo by session id.**

```bash
SID=<paste sessionId from Step 4>
curl -sS "http://localhost:3200/api/search?tags=session.id%3D${SID}&limit=5" | python3 -m json.tool
```

If `tags=session.id` returns empty (because the Java services don't tag spans with `session.id`), fall back to searching by the gateway request and chasing the trace id:

```bash
TID=$(curl -sS "http://localhost:3200/api/search?tags=service.name%3Dgateway-service&limit=20&start=$(date -v -2M +%s)&end=$(date +%s)" \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
for t in d.get('traces',[]):
    r=t.get('rootTraceName','')
    if 'finalize' in r or 'sessions' in r:
        print(t['traceID']); break
")
echo "trace id: $TID"
curl -sS "http://localhost:3200/api/traces/$TID" | python3 -c "
import sys,json
d=json.load(sys.stdin)
svcs=set()
total=0
for b in d.get('batches',[]):
    sname='?'
    for a in b.get('resource',{}).get('attributes',[]):
        if a.get('key')=='service.name':
            sname=a.get('value',{}).get('stringValue','?')
    for ss in b.get('scopeSpans',[]):
        total+=len(ss.get('spans',[]))
    svcs.add(sname)
print('services in trace:', sorted(svcs))
print('total spans:', total)
"
```

Expected: `services in trace: ['gateway-service', 'orchestrator-service', 'smart-service']` and `total spans` ≥ 15. Anything fewer than three services means propagation broke somewhere; check which boundary by running the per-service trace search at each hop.

- [ ] **Step 7: Spot-check the session-lifecycle Grafana dashboard.**

Open `http://localhost:3000` → fiap-secure-systems folder → session-lifecycle dashboard. Trace-derived panels (request rates, latency by service) should now show data tied to the recent flow. Don't worry about metrics/logs panels — those are out of scope for this plan.

- [ ] **Step 8: No commit — verification only.**

If everything passes, the work is done. If Step 6 shows only one or two services, file a follow-up rather than landing further fixes blindly; the spec's "Risks" section lists the most likely culprits.

---

## Task 6: Extract `traceparent` from SQS message attributes in smart-service consumer (added 2026-05-12 after Task 5 verification)

Task 5 verification revealed that the orchestrator → smart-service SQS hop is not stitched: Java's `AwsSdkTelemetry` correctly injects `traceparent` into outbound SQS message attributes, but Python's `BotocoreInstrumentor` only auto-instruments the `ReceiveMessage` API call itself — it does NOT extract per-message `traceparent` from individual message attributes and propagate it into the application's processing context. The fix is to extract the W3C context manually in the consumer's `_handle()` method and attach it before invoking the application service.

**Files:**
- Modify: `smart-service/smart_service/adapter/inbound/sqs_consumer.py:98-129` (one method: `_handle`)

- [ ] **Step 1: Edit `_handle()` to extract and attach the parent context.**

Add these imports at the top of the file (near the existing imports — group as alphabetical/standard-style):

```python
from opentelemetry import context as otel_context, trace
from opentelemetry.propagate import extract
```

Then replace the existing `_handle` method (lines 98-129) with this version. Two changes: (a) build a W3C carrier dict from `MessageAttributes` and extract+attach the parent context; (b) wrap `_svc.run(job)` in a `process`-kind span so the message-processing work is a child of the producer's send span. Everything else (JSON parsing, validation, error handling, receipt deletion) is byte-identical.

```python
    def _handle(self, msg: dict[str, Any]) -> None:
        body = msg.get("Body", "")
        receipt = msg["ReceiptHandle"]
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            log.error("dropping non-JSON message body_head=%r", body[:200])
            self._delete(receipt)
            return

        try:
            validate_analysis_job(payload, self._contracts_dir)
        except SchemaValidationError as e:
            log.error("dropping invalid analysis-job message error=%s", e)
            self._delete(receipt)
            return

        try:
            job = _payload_to_job(payload)
        except (ValueError, KeyError, TypeError) as e:
            # Defense in depth: even after schema validation, a bad UUID or
            # datetime would only surface here. Drop the message instead of
            # letting it loop on redelivery until DLQ.
            log.error("dropping unparseable analysis-job message error=%s", e)
            self._delete(receipt)
            return

        carrier = {
            name: attr.get("StringValue", "")
            for name, attr in msg.get("MessageAttributes", {}).items()
        }
        parent_ctx = extract(carrier)
        token = otel_context.attach(parent_ctx)
        try:
            tracer = trace.get_tracer("smart-service.sqs-consumer")
            with tracer.start_as_current_span(
                "analysis-jobs process",
                kind=trace.SpanKind.CONSUMER,
            ):
                self._svc.run(job)
                self._delete(receipt)
        except Exception:
            log.exception("processing failed; leaving message for redelivery")
        finally:
            otel_context.detach(token)
```

Notes:
- The `MessageAttributes` carrier maps attribute name → `StringValue`. AWS SDK delivers user-defined attributes (including `traceparent` injected by Java's `AwsSdkTelemetry`) in this shape.
- `SpanKind.CONSUMER` follows OTel semantic conventions for message-broker consumers; without it Tempo's service map renders the link as a synchronous client call instead of an asynchronous message hop.
- The span wraps `_svc.run(job)` AND the receipt delete so any failure during processing properly records as failure on the consumer span. The existing redelivery semantics are preserved by leaving `_delete` inside the same `try`.

- [ ] **Step 2: Quick smoke check that imports resolve.**

```bash
cd smart-service && uv run python -c "from smart_service.adapter.inbound import sqs_consumer; print('OK')"
```

Expected: prints `OK`. If `ModuleNotFoundError: opentelemetry.propagate`, the `opentelemetry-api` package isn't installed; check `pyproject.toml` (it should already be there from prior smart-service work).

- [ ] **Step 3: Run the unit tests for the consumer if any exist; otherwise skip.**

```bash
cd smart-service && uv run pytest tests/adapter/inbound -v -k sqs_consumer 2>&1 | tail -20
```

Expected: any existing tests still pass. If a test mocks `msg` without `MessageAttributes`, our new code uses `msg.get("MessageAttributes", {})` so it's defensive — should still pass.

- [ ] **Step 4: Commit the one file.**

```bash
git add smart-service/smart_service/adapter/inbound/sqs_consumer.py
git commit -m "fix(smart-service): extract traceparent from SQS message attributes to link producer context"
```

- [ ] **Step 5: Rebuild + restart smart-service.**

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d --build smart-service
until [ "$(docker inspect -f '{{.State.Health.Status}}' fss-smart-service)" = "healthy" ]; do sleep 3; done
echo SMART_HEALTHY
```

- [ ] **Step 6: Run the round trip and re-verify Tempo shows all 3 services in one trace.**

```bash
make front-round-trip || make front-round-trip
```

Then repeat Task 5 Step 6 — search for the gateway request trace, fetch it, and confirm `services in trace: ['gateway-service', 'orchestrator-service', 'smart-service']` and total spans ≥ 20 (the additional jump means more spans).

Expected: all three services now appear in a single trace.

- [ ] **Step 7: No commit beyond Step 4 — Step 6 is verification only.**

If Tempo STILL shows smart-service in a separate trace, dump one analysis-jobs message's attributes inside the consumer to confirm `traceparent` is actually arriving:

```python
log.info("DEBUG msg attrs: %s", dict(msg.get("MessageAttributes", {})))
```

(Then revert that debug line.) If `traceparent` is missing from the attributes, the break is upstream — `AwsSdkTelemetry` isn't injecting on the orchestrator's `SendMessage`, and the fix needs to go there instead.
