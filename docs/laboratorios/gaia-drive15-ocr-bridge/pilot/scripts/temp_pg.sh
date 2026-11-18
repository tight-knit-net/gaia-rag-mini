#!/usr/bin/env bash
# GAIA OCR pilot: start or discard a per-run PostgreSQL tmpfs container.
# Requires a synthetic/user-approved pilot marker. Never changes Google Drive.
set -euo pipefail
ACTION="${1:-}"
RUN="${2:-}"
COMMIT="${3:-}"
BASE="${GAIA_PILOT_BASE:-/home/ubuntu/gaia-test-lab-homologacao/pilots}"
COMPOSE="$(cd "$(dirname "$0")/.." && pwd)/ocr_postgres_tmpfs.compose.yaml"
[[ "$RUN" =~ ^[a-z0-9][a-z0-9_-]{7,50}$ ]] || { echo INVALID_RUN_ID >&2; exit 12; }
ROOT="$BASE/$RUN"
MARKER="$ROOT/pilot.marker.json"
[[ -f "$MARKER" && ! -L "$MARKER" ]] || { echo PILOT_MARKER_NOT_FOUND >&2; exit 13; }
python3 - "$MARKER" "$RUN" <<'PY'
import json,sys
m=json.load(open(sys.argv[1]))
assert m.get('schema')=='gaia.drive1.pilot-marker.v1'
assert m.get('runId')==sys.argv[2]
assert m.get('driveId')=='0ALBFaLnE8ZPHUk9PVA'
PY
export GAIA_OCR_PG_SECRET_FILE="$ROOT/.pg_password"
PRJ="gaia-ocr-pg-$RUN"
case "$ACTION" in
  start)
    [[ ! -e "$GAIA_OCR_PG_SECRET_FILE" ]] || { echo DATABASE_ALREADY_INITIALIZED >&2; exit 14; }
    umask 077
    openssl rand -hex 32 >"$GAIA_OCR_PG_SECRET_FILE"
    sudo -n chown 70:70 "$GAIA_OCR_PG_SECRET_FILE"
    sudo -n chmod 600 "$GAIA_OCR_PG_SECRET_FILE"
    if ! docker compose -f "$COMPOSE" -p "$PRJ" up -d --wait >&2; then
       docker compose -f "$COMPOSE" -p "$PRJ" down -v --remove-orphans >&2 || :
       rm -f "$GAIA_OCR_PG_SECRET_FILE"
       exit 15
    fi
    echo "TEMP_POSTGRES_READY project=$PRJ network=internal-only volume=none"
    ;;
  stop)
    [[ "$COMMIT" == "--commit" ]] || { echo USE_STOP_WITH_EXPLICIT_COMMIT >&2; exit 16; }
    [[ -f "$ROOT/reports/BOLETIM.md" ]] || { echo REPORT_MUST_EXIST_BEFORE_DATABASE_DISCARD >&2; exit 17; }
    [[ -f "$GAIA_OCR_PG_SECRET_FILE" ]] || { echo DATABASE_SECRET_NOT_PRESENT >&2; exit 18; }
    docker compose -f "$COMPOSE" -p "$PRJ" down -v --remove-orphans >&2
    rm -f "$GAIA_OCR_PG_SECRET_FILE"
    python3 - "$ROOT/reports/PG_TEMPORARY_DB_DISCARDED.json" "$RUN" <<'PY'
import datetime,json,sys
with open(sys.argv[1],'w') as o:
 json.dump({"runId":sys.argv[2],"storage":"POSTGRES_TMPFS",
  "databaseStoppedAndRemoved":True,"driveWrites":0,
  "timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "warning":"Logical removal of temporary storage; physical media erasure is not proven."},o,indent=2)
PY
    echo "TEMP_POSTGRES_REMOVED project=$PRJ Drive1=UNCHANGED"
    ;;
  *)
    echo "USAGE: pilot/scripts/temp_pg.sh start|stop RUN_ID [--commit]" >&2
    exit 11 ;;
esac
