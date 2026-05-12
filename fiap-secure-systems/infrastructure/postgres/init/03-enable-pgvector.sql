-- Runs as the `postgres` superuser at first-container-boot.
\c smart_db
CREATE EXTENSION IF NOT EXISTS vector;
