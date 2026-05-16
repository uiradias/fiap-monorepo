package com.fiap.orchestrator.adapter.in.rest;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import com.fiap.orchestrator.domain.model.*;
import com.fiap.orchestrator.domain.port.in.CancelSessionUseCase;
import com.fiap.orchestrator.domain.port.in.CreateSessionUseCase;
import com.fiap.orchestrator.domain.port.in.GetSessionUseCase;
import com.fiap.orchestrator.domain.port.in.ListUserSessionsUseCase;

class InternalSessionsControllerTest {

    private final CreateSessionUseCase create = mock(CreateSessionUseCase.class);
    private final CancelSessionUseCase cancel = mock(CancelSessionUseCase.class);
    private final GetSessionUseCase getUseCase = mock(GetSessionUseCase.class);
    private final ListUserSessionsUseCase listUserSessions = mock(ListUserSessionsUseCase.class);

    private MockMvc mvc;

    @BeforeEach
    void setup() {
        InternalSessionsController controller =
                new InternalSessionsController(create, cancel, getUseCase, listUserSessions);
        mvc =
                MockMvcBuilders.standaloneSetup(controller)
                        .setControllerAdvice(new GlobalExceptionHandler())
                        .build();
    }

    @Test
    void post_internal_sessions_creates() throws Exception {
        UUID sid = UUID.randomUUID();
        UUID uid = UUID.randomUUID();
        Session created = Session.newSession(new SessionId(sid), new UserId(uid), 1, Instant.now());
        when(create.create(any(), any(), any())).thenReturn(created);

        String body =
                """
                {"sessionId":"%s","userId":"%s","assetCount":1,
                 "assets":[{"assetId":"%s","s3Key":"k","contentType":"image/png",
                            "filename":"f.png","sizeBytes":100}]}
                """
                        .formatted(sid, uid, UUID.randomUUID());

        mvc.perform(
                        post("/internal/sessions")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(body))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.sessionId").value(sid.toString()))
                .andExpect(jsonPath("$.state").value("ASSETS_UPLOADED"));
    }

    @Test
    void get_internal_sessions_returns_404_when_unknown() throws Exception {
        when(getUseCase.findSession(any())).thenReturn(Optional.empty());
        mvc.perform(get("/internal/sessions/{id}", UUID.randomUUID()))
                .andExpect(status().isNotFound())
                .andExpect(content().contentTypeCompatibleWith("application/problem+json"));
    }

    @Test
    void list_internal_sessions_returns_rows() throws Exception {
        UUID uid = UUID.randomUUID();
        Session s =
                Session.newSession(
                        new SessionId(UUID.randomUUID()), new UserId(uid), 1, Instant.now());
        when(listUserSessions.list(any(), anyInt()))
                .thenReturn(
                        List.of(
                                new SessionListItem(
                                        s, Optional.of(new ReportId(UUID.randomUUID())))));
        mvc.perform(get("/internal/sessions").param("userId", uid.toString()).param("limit", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].sessionId").value(s.id().value().toString()))
                .andExpect(jsonPath("$[0].userId").value(uid.toString()))
                .andExpect(jsonPath("$[0].reportId").exists());
    }

    @Test
    void get_report_returns_409_when_not_ready() throws Exception {
        Session s =
                Session.newSession(
                        new SessionId(UUID.randomUUID()),
                        new UserId(UUID.randomUUID()),
                        1,
                        Instant.now());
        when(getUseCase.findSession(any())).thenReturn(Optional.of(s));
        when(getUseCase.findReport(any())).thenReturn(Optional.empty());
        mvc.perform(get("/internal/sessions/{id}/report", UUID.randomUUID()))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.code").value("REPORT_NOT_READY"));
    }
}
