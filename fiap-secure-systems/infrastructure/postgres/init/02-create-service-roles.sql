-- Runs once on a fresh Postgres data directory, AFTER 01-create-databases.sql.
-- Creates per-service roles and grants ownership/usage on their respective DBs.
-- Passwords are dev-only — production uses a secret manager (out of scope per spec §11.1).

-- smart-service
CREATE ROLE smart_user WITH LOGIN PASSWORD 'smart_pwd';
ALTER DATABASE smart_db OWNER TO smart_user;

\connect smart_db
GRANT ALL ON SCHEMA public TO smart_user;
ALTER SCHEMA public OWNER TO smart_user;

-- gateway-service and orchestrator-service roles are created in their own sub-plans
-- (sub-plans 3 and 4) so each service's plan is self-contained.
