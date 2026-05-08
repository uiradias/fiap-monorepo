-- V1__init.sql — orchestrator-service schema
-- Owned by orchestrator_user (see infrastructure/postgres/init/02-create-service-roles.sql).

CREATE TABLE sessions (
    id              UUID         PRIMARY KEY,
    user_id         UUID         NOT NULL,
    state           TEXT         NOT NULL,
    asset_count     INTEGER      NOT NULL,
    failure_reason  TEXT,
    created_at      TIMESTAMPTZ  NOT NULL,
    updated_at      TIMESTAMPTZ  NOT NULL,
    version         BIGINT       NOT NULL DEFAULT 0,
    CONSTRAINT sessions_state_chk CHECK (state IN (
        'CREATED','ASSETS_UPLOADED','QUEUED_FOR_ANALYSIS','ANALYZING',
        'ANALYSIS_COMPLETED','REPORT_READY','FAILED','CANCELED')),
    CONSTRAINT sessions_asset_count_chk CHECK (asset_count > 0)
);
CREATE INDEX sessions_state_idx ON sessions (state);
CREATE INDEX sessions_user_id_idx ON sessions (user_id);

CREATE TABLE session_events (
    id            UUID         PRIMARY KEY,
    session_id    UUID         NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    from_state    TEXT,
    to_state      TEXT         NOT NULL,
    payload       JSONB        NOT NULL DEFAULT '{}'::jsonb,
    occurred_at   TIMESTAMPTZ  NOT NULL,
    published_at  TIMESTAMPTZ
);
CREATE INDEX session_events_by_session ON session_events (session_id, occurred_at);

CREATE TABLE outbox_messages (
    id            UUID         PRIMARY KEY,
    aggregate_id  UUID         NOT NULL,
    destination   TEXT         NOT NULL,
    event_type    TEXT         NOT NULL,
    payload       JSONB        NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL,
    published_at  TIMESTAMPTZ,
    attempts      INTEGER      NOT NULL DEFAULT 0,
    last_error    TEXT,
    CONSTRAINT outbox_destination_chk CHECK (destination IN (
        'SNS_SESSION_EVENTS','SQS_ANALYSIS_JOBS')),
    CONSTRAINT outbox_event_type_chk CHECK (event_type IN (
        'SessionStateChanged','AnalysisJobRequested'))
);
CREATE INDEX outbox_unpublished ON outbox_messages (created_at)
    WHERE published_at IS NULL;

CREATE TABLE analysis_reports (
    id              UUID         PRIMARY KEY,
    session_id      UUID         NOT NULL UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
    summary         TEXT         NOT NULL,
    confidence      TEXT         NOT NULL,
    payload         JSONB        NOT NULL,
    model_metadata  JSONB        NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL,
    CONSTRAINT analysis_reports_confidence_chk CHECK (confidence IN ('high','medium','low'))
);

-- Spec deviation: composite PK so STARTED + SUCCEEDED for the same jobId both dedup correctly.
-- Spec §6.4 names this 'processed_jobs (job_id PK)' but that fits smart-service, not
-- orchestrator (which receives ≥ 2 messages per jobId).
CREATE TABLE processed_results (
    job_id        UUID         NOT NULL,
    status        TEXT         NOT NULL,
    processed_at  TIMESTAMPTZ  NOT NULL,
    PRIMARY KEY (job_id, status),
    CONSTRAINT processed_results_status_chk CHECK (status IN ('STARTED','SUCCEEDED','FAILED'))
);
