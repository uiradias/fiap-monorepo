package com.fiap.orchestrator.adapter.in.rest;

import org.junit.jupiter.api.Test;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.Message;
import software.amazon.awssdk.services.sqs.model.ReceiveMessageRequest;
import software.amazon.awssdk.services.sqs.model.ReceiveMessageResponse;
import software.amazon.awssdk.services.sqs.model.SendMessageResponse;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class AdminReplayControllerTest {

    @Test
    void replays_two_messages_then_stops_on_empty() throws Exception {
        SqsClient sqs = mock(SqsClient.class);
        when(sqs.receiveMessage(any(ReceiveMessageRequest.class)))
                .thenReturn(ReceiveMessageResponse.builder()
                        .messages(
                                Message.builder().body("a").receiptHandle("ra").build(),
                                Message.builder().body("b").receiptHandle("rb").build())
                        .build())
                .thenReturn(ReceiveMessageResponse.builder().build());
        when(sqs.sendMessage(any(software.amazon.awssdk.services.sqs.model.SendMessageRequest.class)))
                .thenReturn(SendMessageResponse.builder().messageId("ok").build());

        AdminReplayController controller = new AdminReplayController(sqs, "dlq-url", "main-url");
        MockMvc mvc = MockMvcBuilders.standaloneSetup(controller).build();

        mvc.perform(post("/admin/replay/analysis-results-dlq"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.replayed").value(2));
    }
}
