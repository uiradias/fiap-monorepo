-- Runs once on a fresh Postgres data directory, AFTER 01-create-databases.sql.
-- Creates per-service roles and grants ownership/usage on their respective DBs.
-- Passwords are dev-only — production uses a secret manager (out of scope per spec §11.1).

-- smart-service
CREATE ROLE smart_user WITH LOGIN PASSWORD 'smart_pwd';
ALTER DATABASE smart_db OWNER TO smart_user;

\connect smart_db
GRANT ALL ON SCHEMA public TO smart_user;
ALTER SCHEMA public OWNER TO smart_user;

-- orchestrator-service
\connect postgres
CREATE ROLE orchestrator_user WITH LOGIN PASSWORD 'orchestrator_pwd';
ALTER DATABASE orchestrator_db OWNER TO orchestrator_user;

\connect orchestrator_db
GRANT ALL ON SCHEMA public TO orchestrator_user;
ALTER SCHEMA public OWNER TO orchestrator_user;

-- gateway-service role (added by sub-plan 4).
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gateway_user') THEN
    CREATE ROLE gateway_user LOGIN PASSWORD 'gateway_pwd';
  END IF;
END
$$;

ALTER DATABASE gateway_db OWNER TO gateway_user;
GRANT ALL PRIVILEGES ON DATABASE gateway_db TO gateway_user;

\connect gateway_db
GRANT ALL ON SCHEMA public TO gateway_user;
ALTER SCHEMA public OWNER TO gateway_user;
