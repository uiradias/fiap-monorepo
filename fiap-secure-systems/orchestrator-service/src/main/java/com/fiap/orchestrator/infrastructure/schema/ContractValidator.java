package com.fiap.orchestrator.infrastructure.schema;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.networknt.schema.JsonSchema;
import com.networknt.schema.JsonSchemaFactory;
import com.networknt.schema.SchemaValidatorsConfig;
import com.networknt.schema.SpecVersion;
import com.networknt.schema.ValidationMessage;

import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.util.Set;

public class ContractValidator {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private final JsonSchema analysisJob;
    private final JsonSchema analysisResult;
    private final JsonSchema sessionEvent;

    public ContractValidator(File contractsDir) {
        if (contractsDir == null || !contractsDir.isDirectory()) {
            throw new IllegalStateException(
                    "contracts directory missing or not a dir: " + contractsDir);
        }
        SchemaValidatorsConfig cfg = new SchemaValidatorsConfig();
        cfg.setFailFast(false);
        JsonSchemaFactory factory = JsonSchemaFactory.getInstance(SpecVersion.VersionFlag.V7);
        this.analysisJob    = load(factory, cfg, contractsDir, "analysis-jobs.schema.json");
        this.analysisResult = load(factory, cfg, contractsDir, "analysis-results.schema.json");
        this.sessionEvent   = load(factory, cfg, contractsDir, "session-events.schema.json");
    }

    private static JsonSchema load(
            JsonSchemaFactory factory, SchemaValidatorsConfig cfg,
            File dir, String fileName) {
        File f = new File(dir, fileName);
        if (!f.isFile()) {
            throw new IllegalStateException("schema file missing: " + f);
        }
        try {
            JsonNode node = MAPPER.readTree(f);
            URI base = dir.toURI();
            return factory.getSchema(base, node, cfg);
        } catch (IOException e) {
            throw new IllegalStateException("failed to load " + f, e);
        }
    }

    public void validateAnalysisJob(Object body)    { run(analysisJob, body, "analysis-jobs"); }
    public void validateAnalysisResult(Object body) { run(analysisResult, body, "analysis-results"); }
    public void validateSessionEvent(Object body)   { run(sessionEvent, body, "session-events"); }

    private static void run(JsonSchema schema, Object body, String label) {
        JsonNode node = MAPPER.valueToTree(body);
        Set<ValidationMessage> errors = schema.validate(node);
        if (!errors.isEmpty()) {
            throw new ContractValidationException(
                    "%s schema violations: %s".formatted(label, errors));
        }
    }
}
