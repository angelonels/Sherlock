#!/bin/sh
set -eu

root_dir="$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)"
test_dir="$(mktemp -d)"
trap 'rm -rf "$test_dir"' EXIT

mkdir -p "$test_dir/bin" "$test_dir/backups"

cat > "$test_dir/bin/pg_dump" <<'EOF'
#!/bin/sh
while [ "$#" -gt 0 ]; do
  if [ "$1" = "--file" ]; then
    printf 'custom-format-test-dump' > "$2"
    exit 0
  fi
  shift
done
exit 1
EOF

cat > "$test_dir/bin/aws" <<'EOF'
#!/bin/sh
printf '%s\n' "$*" > "$BACKUP_TEST_AWS_LOG"
EOF

chmod +x "$test_dir/bin/pg_dump" "$test_dir/bin/aws"

PATH="$test_dir/bin:$PATH" \
BACKUP_TEST_AWS_LOG="$test_dir/aws.log" \
POSTGRES_USER=sherlock_admin \
POSTGRES_PASSWORD=test-password \
POSTGRES_DB=sherlock_db \
POSTGRES_BACKUP_DIR="$test_dir/backups" \
POSTGRES_BACKUP_RUN_ONCE=true \
POSTGRES_BACKUP_S3_URI=s3://sherlock-backups/production \
POSTGRES_BACKUP_S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com \
POSTGRES_BACKUP_S3_ACCESS_KEY_ID=test-access-key \
POSTGRES_BACKUP_S3_SECRET_ACCESS_KEY=test-secret-key \
POSTGRES_BACKUP_S3_REGION=us-east-1 \
sh "$root_dir/infra/postgres/backup-loop.sh"

test -s "$test_dir/backups/.last-success"
test -s "$test_dir/backups/.last-offsite-success"
test "$(find "$test_dir/backups" -name 'sherlock_*.dump' | wc -l | tr -d ' ')" = "1"
grep -q 's3 cp .* s3://sherlock-backups/production/' "$test_dir/aws.log"
grep -q -- '--endpoint-url https://nyc3.digitaloceanspaces.com' "$test_dir/aws.log"

printf 'BACKUP_LOOP_TEST_OK\n'
