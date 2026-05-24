#!/usr/bin/with-contenv bashio
set -e

bashio::log.info "Starting SiapJalan..."

export ANTHROPIC_API_KEY=$(bashio::config 'anthropic_api_key')
export LOG_LEVEL=$(bashio::config 'log_level')
export DATABASE_URL="sqlite+aiosqlite:////data/siapjalan.db"

bashio::log.info "Database: /data/siapjalan.db"
bashio::log.info "Log level: ${LOG_LEVEL}"

cd /app
exec python3 -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8099 \
  --log-level "${LOG_LEVEL}"
