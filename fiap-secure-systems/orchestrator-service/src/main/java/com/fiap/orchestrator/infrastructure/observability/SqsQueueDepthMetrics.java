package com.fiap.orchestrator.infrastructure.observability;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import io.micrometer.core.instrument.Gauge;
import io.micrometer.core.instrument.MeterRegistry;
import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.GetQueueAttributesRequest;
import software.amazon.awssdk.services.sqs.model.QueueAttributeName;

@Component
public class SqsQueueDepthMetrics {

    private static final Logger log = LoggerFactory.getLogger(SqsQueueDepthMetrics.class);

    private final SqsClient sqs;
    private final Map<String, String> queueUrls;
    private final Map<String, AtomicLong> depths = new ConcurrentHashMap<>();

    public SqsQueueDepthMetrics(
            SqsClient sqs,
            @Qualifier("analysisJobsQueueUrl") String analysisJobsUrl,
            @Qualifier("analysisResultsQueueUrl") String analysisResultsUrl,
            @Qualifier("analysisResultsDlqUrl") String analysisResultsDlqUrl,
            MeterRegistry registry) {
        this.sqs = sqs;
        this.queueUrls = new LinkedHashMap<>();
        queueUrls.put("analysis-jobs", analysisJobsUrl);
        queueUrls.put("analysis-results", analysisResultsUrl);
        queueUrls.put("analysis-results-dlq", analysisResultsDlqUrl);
        for (String name : queueUrls.keySet()) {
            AtomicLong depth = new AtomicLong(0L);
            depths.put(name, depth);
            Gauge.builder("fss_sqs_queue_depth", depth, AtomicLong::get)
                    .description("Approximate number of messages on the SQS queue")
                    .tag("queue", name)
                    .register(registry);
        }
    }

    @Scheduled(fixedDelay = 30_000L, initialDelay = 5_000L)
    public void pollDepths() {
        for (var e : queueUrls.entrySet()) {
            try {
                var resp =
                        sqs.getQueueAttributes(
                                GetQueueAttributesRequest.builder()
                                        .queueUrl(e.getValue())
                                        .attributeNames(
                                                QueueAttributeName.APPROXIMATE_NUMBER_OF_MESSAGES)
                                        .build());
                String v = resp.attributes().get(QueueAttributeName.APPROXIMATE_NUMBER_OF_MESSAGES);
                depths.get(e.getKey()).set(v == null ? 0L : Long.parseLong(v));
            } catch (Exception ex) {
                log.debug("queue depth poll failed for {}: {}", e.getKey(), ex.getMessage());
            }
        }
    }
}
