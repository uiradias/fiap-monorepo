package com.fiap.orchestrator.application.service;

import java.time.Instant;
import java.util.*;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fiap.orchestrator.domain.model.*;
import com.fiap.orchestrator.domain.port.in.CreateSessionUseCase;
import com.fiap.orchestrator.domain.port.out.OutboxPort;
import com.fiap.orchestrator.domain.port.out.SessionRepositoryPort;

@Service
public class CreateSessionService implements CreateSessionUseCase {

    private final SessionRepositoryPort sessions;
    private final OutboxPort outbox;
    private final Clock clock;

    public CreateSessionService(SessionRepositoryPort sessions, OutboxPort outbox, Clock clock) {
        this.sessions = sessions;
        this.outbox = outbox;
        this.clock = clock;
    }

    @Override
    @Transactional
    public Session create(SessionId sessionId, UserId userId, List<AssetRef> assets) {
        Optional<Session> existing = sessions.findById(sessionId);
        if (existing.isPresent()) return existing.get();

        Instant now = clock.now();
        Session created = Session.newSession(sessionId, userId, assets.size(), now);
        sessions.insertIfAbsent(created);

        EventId evId = new EventId(UUID.randomUUID());
        SessionEvent ev =
                SessionEvent.initial(
                        evId,
                        sessionId,
                        SessionState.ASSETS_UPLOADED,
                        Map.of("assetCount", assets.size()),
                        now);
        sessions.appendEvent(ev);

        outbox.append(
                sessionId,
                OutboxPort.Destination.SNS_SESSION_EVENTS,
                "SessionStateChanged",
                sessionEventPayload(ev, userId),
                now);

        outbox.append(
                sessionId,
                OutboxPort.Destination.SQS_ANALYSIS_JOBS,
                "AnalysisJobRequested",
                analysisJobPayload(sessionId, userId, assets, now),
                now);

        return created;
    }

    public static Map<String, Object> sessionEventPayload(SessionEvent ev, UserId userId) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("schemaVersion", 1);
        body.put("eventId", ev.id().toString());
        body.put("sessionId", ev.sessionId().toString());
        body.put("userId", userId.toString());
        body.put("fromState", ev.fromState() == null ? null : ev.fromState().name());
        body.put("toState", ev.toState().name());
        body.put("payload", ev.payload());
        body.put("occurredAt", ev.occurredAt().toString());
        return body;
    }

    private static Map<String, Object> analysisJobPayload(
            SessionId sid, UserId uid, List<AssetRef> assets, Instant now) {
        List<Map<String, Object>> assetMaps =
                assets.stream()
                        .map(
                                a ->
                                        Map.<String, Object>of(
                                                "assetId", a.assetId().toString(),
                                                "s3Key", a.s3Key(),
                                                "contentType", a.contentType(),
                                                "filename", a.filename(),
                                                "sizeBytes", a.sizeBytes()))
                        .toList();
        return Map.of(
                "schemaVersion", 1,
                "jobId", UUID.randomUUID().toString(),
                "sessionId", sid.toString(),
                "userId", uid.toString(),
                "assets", assetMaps,
                "promptVersion", "v1",
                "submittedAt", now.toString());
    }
}
