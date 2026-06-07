#!/bin/sh
set -eu

: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"

backup_dir="${POSTGRES_BACKUP_DIR:-/backups}"
interval_seconds="${POSTGRES_BACKUP_INTERVAL_SECONDS:-86400}"
retention_days="${POSTGRES_BACKUP_RETENTION_DAYS:-14}"
offsite_uri="${POSTGRES_BACKUP_S3_URI:-}"
offsite_endpoint_url="${POSTGRES_BACKUP_S3_ENDPOINT_URL:-}"
run_once="${POSTGRES_BACKUP_RUN_ONCE:-false}"

export PGPASSWORD="$POSTGRES_PASSWORD"
mkdir -p "$backup_dir"

upload_offsite() {
  backup_path="$1"
  if [ -z "$offsite_uri" ]; then
    return
  fi

  : "${POSTGRES_BACKUP_S3_ACCESS_KEY_ID:?POSTGRES_BACKUP_S3_ACCESS_KEY_ID is required}"
  : "${POSTGRES_BACKUP_S3_SECRET_ACCESS_KEY:?POSTGRES_BACKUP_S3_SECRET_ACCESS_KEY is required}"
  : "${POSTGRES_BACKUP_S3_REGION:?POSTGRES_BACKUP_S3_REGION is required}"

  export AWS_ACCESS_KEY_ID="$POSTGRES_BACKUP_S3_ACCESS_KEY_ID"
  export AWS_SECRET_ACCESS_KEY="$POSTGRES_BACKUP_S3_SECRET_ACCESS_KEY"
  export AWS_DEFAULT_REGION="$POSTGRES_BACKUP_S3_REGION"

  destination="${offsite_uri%/}/$(basename "$backup_path")"
  if [ -n "$offsite_endpoint_url" ]; then
    aws s3 cp "$backup_path" "$destination" --endpoint-url "$offsite_endpoint_url"
  else
    aws s3 cp "$backup_path" "$destination"
  fi
  date -u +%Y-%m-%dT%H:%M:%SZ > "$backup_dir/.last-offsite-success"
}

while true; do
  timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
  backup_path="$backup_dir/sherlock_${timestamp}.dump"
  temporary_path="${backup_path}.tmp"

  pg_dump \
    --host postgres \
    --username "$POSTGRES_USER" \
    --dbname "$POSTGRES_DB" \
    --format custom \
    --file "$temporary_path"

  mv "$temporary_path" "$backup_path"
  upload_offsite "$backup_path"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$backup_dir/.last-success"
  find "$backup_dir" -type f -name 'sherlock_*.dump' -mtime "+$retention_days" -delete
  if [ "$run_once" = "true" ]; then
    exit 0
  fi
  sleep "$interval_seconds"
done
