#!/usr/bin/env bash
set -euo pipefail

CONTAINERS=(
  fss-postgres
  fss-localstack
  fss-otel-collector
  fss-smart-service
  fss-orchestrator-service
  fss-gateway-service
  fss-frontend
)
DEADLINE=${DEADLINE_SECONDS:-240}

green() { printf "\033[32m%s\033[0m\n" "$*"; }
red()   { printf "\033[31m%s\033[0m\n" "$*"; }

for svc in "${CONTAINERS[@]}"; do
  for i in $(seq 1 "$DEADLINE"); do
    s=$(docker inspect -f '{{.State.Health.Status}}' "$svc" 2>/dev/null || echo none)
    [ "$s" = "healthy" ] && break
    sleep 1
  done
  if [ "$s" = "healthy" ]; then
    green "  → $svc healthy"
  else
    red "  → $svc not healthy (last=$s); dumping last 50 log lines"
    docker logs --tail 50 "$svc" || true
    exit 1
  fi
done
green "✓ all containers healthy"
