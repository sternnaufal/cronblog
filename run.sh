#!/usr/bin/env bash
# Wrapper cron untuk cronblog: mencegah dua proses berjalan bersamaan.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p logs
exec flock -n /tmp/cronblog.lock ./venv/bin/python -m src.main "$@"
