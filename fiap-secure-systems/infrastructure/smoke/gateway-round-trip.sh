#!/usr/bin/env bash
# End-to-end gateway round-trip:
# - register a fresh user
# - login → access + refresh tokens
# - create asset bundle
# - upload sample-architecture.png via multipart
# - finalize → orchestrator session created (== bundleId)
# - poll GET /sessions/{id} until REPORT_READY (deadline 60s)
# - GET /sessions/{id}/report
#
# Requires: docker, jq, uuidgen, curl. Stack must be up:
#   make up && make smart-up && make orch-up && make gw-up

set -euo pipefail

GATEWAY="${GATEWAY:-http://localhost:8080}"
DEADLINE_SECONDS="${DEADLINE_SECONDS:-60}"
FIXTURE="smart-service/tests/fixtures/sample-architecture.png"

green() { printf "\033[32m%s\033[0m\n" "$*"; }
red()   { printf "\033[31m%s\033[0m\n" "$*"; }

for cmd in docker jq uuidgen curl; do
  command -v "$cmd" >/dev/null 2>&1 || { red "missing: $cmd"; exit 2; }
done
[ -f "$FIXTURE" ] || { red "fixture not found: $FIXTURE (run from project root)"; exit 2; }
docker inspect fss-gateway-service >/dev/null 2>&1 || { red "fss-gateway-service not running — try: make gw-up"; exit 2; }

EMAIL="rt-$(uuidgen | tr '[:upper:]' '[:lower:]' | head -c 8)@fiap.local"
PASS="hunter22-rt"

echo "→ register $EMAIL"
http=$(curl -sS -o /tmp/rt-reg.json -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  -X POST "$GATEWAY/api/v1/auth/register" \
  -d "$(jq -nc --arg e "$EMAIL" --arg p "$PASS" '{email:$e, password:$p, displayName:"RT"}')")
[ "$http" = "201" ] || { red "register $http"; cat /tmp/rt-reg.json; exit 1; }
green "  → 201 created"

echo "→ login"
http=$(curl -sS -o /tmp/rt-login.json -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  -X POST "$GATEWAY/api/v1/auth/login" \
  -d "$(jq -nc --arg e "$EMAIL" --arg p "$PASS" '{email:$e, password:$p}')")
[ "$http" = "200" ] || { red "login $http"; cat /tmp/rt-login.json; exit 1; }
ACCESS=$(jq -r .accessToken /tmp/rt-login.json)
green "  → 200, access token issued"

echo "→ create bundle"
http=$(curl -sS -o /tmp/rt-bundle.json -w '%{http_code}' \
  -H "Authorization: Bearer $ACCESS" \
  -X POST "$GATEWAY/api/v1/asset-bundles")
[ "$http" = "201" ] || { red "bundle $http"; cat /tmp/rt-bundle.json; exit 1; }
BUNDLE_ID=$(jq -r .bundleId /tmp/rt-bundle.json)
green "  → bundleId=$BUNDLE_ID"

echo "→ upload asset"
http=$(curl -sS -o /tmp/rt-asset.json -w '%{http_code}' \
  -H "Authorization: Bearer $ACCESS" \
  -F "file=@$FIXTURE;type=image/png" \
  -X POST "$GATEWAY/api/v1/asset-bundles/$BUNDLE_ID/assets")
[ "$http" = "201" ] || { red "upload $http"; cat /tmp/rt-asset.json; exit 1; }
green "  → 201, asset stored"

echo "→ finalize"
http=$(curl -sS -o /tmp/rt-fin.json -w '%{http_code}' \
  -H "Authorization: Bearer $ACCESS" \
  -X POST "$GATEWAY/api/v1/asset-bundles/$BUNDLE_ID/finalize")
[ "$http" = "202" ] || { red "finalize $http"; cat /tmp/rt-fin.json; exit 1; }
SESSION_ID=$(jq -r .sessionId /tmp/rt-fin.json)
[ "$SESSION_ID" = "$BUNDLE_ID" ] || { red "sessionId != bundleId ($SESSION_ID vs $BUNDLE_ID)"; exit 1; }
green "  → sessionId=$SESSION_ID"

echo "→ polling GET /sessions/$SESSION_ID until REPORT_READY (deadline ${DEADLINE_SECONDS}s)"
deadline=$(( $(date +%s) + DEADLINE_SECONDS ))
state=""
while [ "$(date +%s)" -lt "$deadline" ]; do
  http=$(curl -sS -o /tmp/rt-sess.json -w '%{http_code}' \
    -H "Authorization: Bearer $ACCESS" \
    "$GATEWAY/api/v1/sessions/$SESSION_ID")
  if [ "$http" = "200" ]; then
    state=$(jq -r .state /tmp/rt-sess.json)
    echo "    state=$state"
    [ "$state" = "REPORT_READY" ] && break
    [ "$state" = "FAILED" ] && { red "session failed: $(jq -r .failureReason /tmp/rt-sess.json)"; exit 1; }
  fi
  sleep 2
done

[ "$state" = "REPORT_READY" ] || { red "did not reach REPORT_READY in ${DEADLINE_SECONDS}s (last=$state)"; exit 1; }
green "  → REPORT_READY"

echo "→ GET report"
http=$(curl -sS -o /tmp/rt-report.json -w '%{http_code}' \
  -H "Authorization: Bearer $ACCESS" \
  "$GATEWAY/api/v1/sessions/$SESSION_ID/report")
[ "$http" = "200" ] || { red "report $http"; cat /tmp/rt-report.json; exit 1; }
SUMMARY=$(jq -r .summary /tmp/rt-report.json)
green "  → got report, summary=\"$SUMMARY\""

green "✓ gateway round-trip OK"
