package com.fiap.orchestrator.adapter.out.persistence;

import com.fiap.orchestrator.domain.model.AnalysisReport;
import com.fiap.orchestrator.domain.model.ReportId;
import com.fiap.orchestrator.domain.model.SessionId;
import jakarta.persistence.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

@Entity
@Table(name = "analysis_reports")
public class AnalysisReportEntity {

    @Id
    private UUID id;

    @Column(name = "session_id", nullable = false, unique = true)
    private UUID sessionId;

    @Column(nullable = false)
    private String summary;

    @Column(nullable = false)
    private String confidence;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(nullable = false, columnDefinition = "jsonb")
    private Map<String, Object> payload;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "model_metadata", nullable = false, columnDefinition = "jsonb")
    private Map<String, Object> modelMetadata;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    public AnalysisReportEntity() {}

    public static AnalysisReportEntity from(AnalysisReport r) {
        AnalysisReportEntity x = new AnalysisReportEntity();
        x.id = r.id().value();
        x.sessionId = r.sessionId().value();
        x.summary = r.summary();
        x.confidence = r.confidence();
        x.payload = r.payload();
        x.modelMetadata = r.modelMetadata();
        x.createdAt = r.createdAt();
        return x;
    }

    public AnalysisReport toDomain() {
        return new AnalysisReport(
                new ReportId(id), new SessionId(sessionId),
                summary, confidence, payload, modelMetadata, createdAt);
    }
}
