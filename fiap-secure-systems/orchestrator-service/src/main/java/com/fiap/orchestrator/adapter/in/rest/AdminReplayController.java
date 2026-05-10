package com.fiap.orchestrator.adapter.in.rest;

import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.*;

@RestController
@RequestMapping("/admin/replay")
public class AdminReplayController {

    private static final Logger log = LoggerFactory.getLogger(AdminReplayController.class);

    private final SqsClient sqs;
    private final String dlqUrl;
    private final String mainUrl;

    public AdminReplayController(
            SqsClient sqs,
            @Qualifier("analysisResultsDlqUrl") String dlqUrl,
            @Qualifier("analysisResultsQueueUrl") String mainUrl) {
        this.sqs = sqs;
        this.dlqUrl = dlqUrl;
        this.mainUrl = mainUrl;
    }

    @PostMapping("/analysis-results-dlq")
    public ResponseEntity<Map<String, Object>> replayDlq() {
        int replayed = 0;
        while (true) {
            ReceiveMessageResponse resp =
                    sqs.receiveMessage(
                            ReceiveMessageRequest.builder()
                                    .queueUrl(dlqUrl)
                                    .maxNumberOfMessages(10)
                                    .waitTimeSeconds(1)
                                    .build());
            List<Message> msgs = resp.messages();
            if (msgs.isEmpty()) break;
            for (Message m : msgs) {
                sqs.sendMessage(
                        SendMessageRequest.builder()
                                .queueUrl(mainUrl)
                                .messageBody(m.body())
                                .build());
                sqs.deleteMessage(
                        DeleteMessageRequest.builder()
                                .queueUrl(dlqUrl)
                                .receiptHandle(m.receiptHandle())
                                .build());
                replayed++;
            }
        }
        log.info("DLQ replay complete: {} messages re-sent to {}", replayed, mainUrl);
        return ResponseEntity.ok(Map.of("replayed", replayed));
    }
}
