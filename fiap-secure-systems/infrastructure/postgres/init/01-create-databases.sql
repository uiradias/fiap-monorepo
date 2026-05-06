-- Runs once on a fresh Postgres data directory (mounted at /docker-entrypoint-initdb.d).
-- Creates one logical database per service, all owned by the default postgres user.
-- Service-specific schemas/migrations are managed by Flyway/Alembic in each service.

CREATE DATABASE gateway_db;
CREATE DATABASE orchestrator_db;
CREATE DATABASE smart_db;

-- Enable required extensions on each DB.
\connect gateway_db
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

\connect orchestrator_db
CREATE EXTENSION IF NOT EXISTS pgcrypto;

\connect smart_db
CREATE EXTENSION IF NOT EXISTS pgcrypto;
