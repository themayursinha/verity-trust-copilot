#!/usr/bin/env bash
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=${BACKUP_DIR:-./backups}
mkdir -p "$BACKUP_DIR"

docker compose exec -T postgres pg_dump -U postgres verity | gzip > "$BACKUP_DIR/verity_$TIMESTAMP.sql.gz"
echo "Backup saved to $BACKUP_DIR/verity_$TIMESTAMP.sql.gz"
