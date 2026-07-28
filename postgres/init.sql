-- Postgres initialisation script
-- Runs once on first container start (via docker-entrypoint-initdb.d).
-- Flask-Migrate (Alembic) manages schema after this point.

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- fast LIKE search on URLs

-- Read-only role for monitoring (Grafana postgres datasource)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'readonly') THEN
    CREATE ROLE readonly WITH LOGIN PASSWORD 'readonly';
  END IF;
END
$$;

GRANT CONNECT ON DATABASE urlshortener TO readonly;
GRANT USAGE ON SCHEMA public TO readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly;
