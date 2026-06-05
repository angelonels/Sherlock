#!/bin/sh
set -eu

: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_READONLY_PASSWORD:?POSTGRES_READONLY_PASSWORD is required}"
postgres_host="${POSTGRES_HOST:-postgres}"

export PGPASSWORD="$POSTGRES_PASSWORD"

psql \
  --host "$postgres_host" \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --set ON_ERROR_STOP=1 \
  --set admin_user="$POSTGRES_USER" \
  --set readonly_password="$POSTGRES_READONLY_PASSWORD" <<'SQL'
SELECT format(
  'CREATE ROLE sherlock_readonly LOGIN PASSWORD %L',
  :'readonly_password'
)
WHERE NOT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = 'sherlock_readonly'
)\gexec

ALTER ROLE sherlock_readonly PASSWORD :'readonly_password';
CREATE SCHEMA IF NOT EXISTS user_data;
REVOKE CREATE ON SCHEMA user_data FROM PUBLIC;
GRANT USAGE ON SCHEMA user_data TO sherlock_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA user_data TO sherlock_readonly;
ALTER DEFAULT PRIVILEGES FOR ROLE :"admin_user" IN SCHEMA user_data
  GRANT SELECT ON TABLES TO sherlock_readonly;
SQL
