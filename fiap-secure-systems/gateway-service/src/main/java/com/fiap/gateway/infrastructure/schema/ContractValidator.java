package com.fiap.gateway.infrastructure.schema;

import java.io.File;
import java.io.IOException;
import java.util.Set;
import java.util.stream.Collectors;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.networknt.schema.JsonSchema;
import com.networknt.schema.JsonSchemaFactory;
import com.networknt.schema.SpecVersion;
import com.networknt.schema.ValidationMessage;

public class ContractValidator {

    private final ObjectMapper mapper = new ObjectMapper();
    private final JsonSchema sessionEventSchema;

    public ContractValidator(File contractsDir) {
        try {
            JsonSchemaFactory factory = JsonSchemaFactory.getInstance(SpecVersion.VersionFlag.V7);
            this.sessionEventSchema =
                    factory.getSchema(new File(contractsDir, "session-events.schema.json").toURI());
        } catch (Exception e) {
            throw new IllegalStateException(
                    "failed to load contract schemas from " + contractsDir, e);
        }
    }

    public void validateSessionEvent(Object payload) {
        validate(sessionEventSchema, payload, "session-events");
    }

    private void validate(JsonSchema schema, Object payload, String label) {
        try {
            JsonNode node = mapper.valueToTree(payload);
            Set<ValidationMessage> errors = schema.validate(node);
            if (!errors.isEmpty()) {
                String joined =
                        errors.stream()
                                .map(ValidationMessage::getMessage)
                                .collect(Collectors.joining("; "));
                throw new InvalidPayloadException(label + " validation failed: " + joined);
            }
        } catch (InvalidPayloadException ipe) {
            throw ipe;
        } catch (Exception other) {
            try {
                mapper.writeValueAsString(payload);
            } catch (IOException ignored) {
            }
            throw new InvalidPayloadException(label + " validation error: " + other.getMessage());
        }
    }
}
