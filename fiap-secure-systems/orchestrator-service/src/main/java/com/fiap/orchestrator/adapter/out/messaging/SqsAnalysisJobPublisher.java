package com.fiap.orchestrator.adapter.out.messaging;

import java.util.LinkedHashMap;
import java.util.Map;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.orchestrator.domain.model.AnalysisJob;
import com.fiap.orchestrator.domain.port.out.AnalysisJobPublisherPort;
import com.fiap.orchestrator.infrastructure.schema.ContractValidator;

import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.MessageAttributeValue;
import software.amazon.awssdk.services.sqs.model.SendMessageRequest;

public class SqsAnalysisJobPublisher implements AnalysisJobPublisherPort {

    private final SqsClient sqs;
    private final String queueUrl;
    private final ContractValidator validator;
    private final ObjectMapper mapper;

    public SqsAnalysisJobPublisher(
            SqsClient sqs, String queueUrl, ContractValidator validator, ObjectMapper mapper) {
        this.sqs = sqs;
        this.queueUrl = queueUrl;
        this.validator = validator;
        this.mapper = mapper;
    }

    @Override
    public void publish(AnalysisJob job) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("schemaVersion", 1);
        body.put("jobId", job.jobId().toString());
        body.put("sessionId", job.sessionId().toString());
        body.put("userId", job.userId().toString());
        body.put(
                "assets",
                job.assets().stream()
                        .map(
                                a ->
                                        Map.<String, Object>of(
                                                "assetId", a.assetId().toString(),
                                                "s3Key", a.s3Key(),
                                                "contentType", a.contentType(),
                                                "filename", a.filename(),
                                                "sizeBytes", a.sizeBytes()))
                        .toList());
        body.put("promptVersion", job.promptVersion());
        body.put("submittedAt", job.submittedAt().toString());
        publishPreSerialized(body, job.sessionId().toString());
    }

    /** Used by the OutboxRelay (which has the payload already serialized). */
    public void publishPreSerialized(Map<String, Object> body, String sessionIdAttr) {
        validator.validateAnalysisJob(body);
        try {
            sqs.sendMessage(
                    SendMessageRequest.builder()
                            .queueUrl(queueUrl)
                            .messageBody(mapper.writeValueAsString(body))
                            .messageAttributes(
                                    Map.of(
                                            "sessionId",
                                            MessageAttributeValue.builder()
                                                    .dataType("String")
                                                    .stringValue(sessionIdAttr)
                                                    .build()))
                            .build());
        } catch (Exception e) {
            throw new RuntimeException("failed to publish analysis-job", e);
        }
    }
}
