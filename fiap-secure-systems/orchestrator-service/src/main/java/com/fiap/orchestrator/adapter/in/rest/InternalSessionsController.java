package com.fiap.orchestrator.adapter.in.rest;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import com.fiap.orchestrator.adapter.in.rest.dto.CreateSessionRequest;
import com.fiap.orchestrator.adapter.in.rest.dto.ProblemDetailFactory;
import com.fiap.orchestrator.adapter.in.rest.dto.ReportResponse;
import com.fiap.orchestrator.adapter.in.rest.dto.SessionResponse;
import com.fiap.orchestrator.domain.model.*;
import com.fiap.orchestrator.domain.port.in.CancelSessionUseCase;
import com.fiap.orchestrator.domain.port.in.CreateSessionUseCase;
import com.fiap.orchestrator.domain.port.in.GetSessionUseCase;
import com.fiap.orchestrator.domain.port.in.ListUserSessionsUseCase;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/internal/sessions")
public class InternalSessionsController {

    private final CreateSessionUseCase create;
    private final CancelSessionUseCase cancel;
    private final GetSessionUseCase get;
    private final ListUserSessionsUseCase listUserSessions;

    public InternalSessionsController(
            CreateSessionUseCase create,
            CancelSessionUseCase cancel,
            GetSessionUseCase get,
            ListUserSessionsUseCase listUserSessions) {
        this.create = create;
        this.cancel = cancel;
        this.get = get;
        this.listUserSessions = listUserSessions;
    }

    @PostMapping
    public ResponseEntity<SessionResponse> createSession(
            @Valid @RequestBody CreateSessionRequest req) {
        List<AssetRef> assets =
                req.assets().stream()
                        .map(
                                a ->
                                        new AssetRef(
                                                a.assetId(),
                                                a.s3Key(),
                                                a.contentType(),
                                                a.filename(),
                                                a.sizeBytes()))
                        .toList();
        Session s = create.create(new SessionId(req.sessionId()), new UserId(req.userId()), assets);
        return ResponseEntity.status(HttpStatus.CREATED).body(SessionResponse.from(s));
    }

    @GetMapping(params = "userId")
    public List<SessionResponse> listSessions(
            @RequestParam("userId") UUID userId,
            @RequestParam(value = "limit", defaultValue = "50") int limit) {
        return listUserSessions.list(new UserId(userId), limit).stream()
                .map(
                        row ->
                                SessionResponse.from(
                                        row.session(),
                                        row.reportId().map(rid -> rid.value()).orElse(null)))
                .toList();
    }

    @GetMapping("/{id}")
    public ResponseEntity<?> getSession(@PathVariable UUID id) {
        Optional<Session> s = get.findSession(new SessionId(id));
        if (s.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(
                            ProblemDetailFactory.of(
                                    HttpStatus.NOT_FOUND,
                                    "Session not found",
                                    "No session with id " + id,
                                    "SESSION_NOT_FOUND"));
        }
        Session session = s.get();
        UUID reportId = null;
        if (session.state() == SessionState.REPORT_READY) {
            reportId = get.findReport(session.id()).map(r -> r.id().value()).orElse(null);
        }
        return ResponseEntity.ok(SessionResponse.from(session, reportId));
    }

    @PostMapping("/{id}/cancel")
    public ResponseEntity<Void> cancelSession(@PathVariable UUID id) {
        cancel.cancel(new SessionId(id));
        return ResponseEntity.accepted().build();
    }

    @GetMapping("/{id}/report")
    public ResponseEntity<?> getReport(@PathVariable UUID id) {
        Optional<Session> s = get.findSession(new SessionId(id));
        if (s.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(
                            ProblemDetailFactory.of(
                                    HttpStatus.NOT_FOUND,
                                    "Session not found",
                                    "No session with id " + id,
                                    "SESSION_NOT_FOUND"));
        }
        if (s.get().state() != SessionState.REPORT_READY) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(
                            ProblemDetailFactory.of(
                                    HttpStatus.CONFLICT,
                                    "Report not ready",
                                    "Session is in state " + s.get().state(),
                                    "REPORT_NOT_READY"));
        }
        return get.findReport(new SessionId(id))
                .<ResponseEntity<?>>map(r -> ResponseEntity.ok(ReportResponse.from(r)))
                .orElseGet(
                        () ->
                                ResponseEntity.status(HttpStatus.NOT_FOUND)
                                        .body(
                                                ProblemDetailFactory.of(
                                                        HttpStatus.NOT_FOUND,
                                                        "Report missing",
                                                        "Session is REPORT_READY but no report row"
                                                                + " exists",
                                                        "REPORT_MISSING")));
    }
}
