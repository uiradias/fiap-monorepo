-- gateway-service / V1__init.sql
-- Creates: users, refresh_tokens, asset_bundles, assets, session_projections, session_event_log

CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE users (
    id UUID PRIMARY KEY,
    email CITEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX refresh_tokens_active_by_user
    ON refresh_tokens (user_id) WHERE revoked_at IS NULL;

CREATE TABLE asset_bundles (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    status TEXT NOT NULL,
    asset_count INT NOT NULL DEFAULT 0,
    total_bytes BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX asset_bundles_by_user ON asset_bundles (user_id, created_at DESC);

CREATE TABLE assets (
    id UUID PRIMARY KEY,
    bundle_id UUID NOT NULL REFERENCES asset_bundles(id) ON DELETE CASCADE,
    s3_key TEXT NOT NULL,
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    size_bytes BIGINT NOT NULL,
    checksum_sha256 TEXT NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL,
    UNIQUE (bundle_id, s3_key)
);

CREATE TABLE session_projections (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    state TEXT NOT NULL,
    last_event_at TIMESTAMPTZ NOT NULL,
    failure_reason TEXT,
    report_id UUID
);

CREATE TABLE session_event_log (
    event_id UUID PRIMARY KEY,
    session_id UUID NOT NULL,
    user_id UUID NOT NULL,
    from_state TEXT,
    to_state TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX session_event_log_by_session
    ON session_event_log (session_id, occurred_at);
