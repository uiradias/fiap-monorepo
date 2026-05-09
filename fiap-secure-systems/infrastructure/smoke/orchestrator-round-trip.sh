#!/usr/bin/env bash
# End-to-end orchestrator round-trip:
# - POST /internal/sessions (HMAC-signed)
# - Wait for orchestrator to publish analysis-job to SQS
# - Wait for smart-service to consume it and publish STARTED + SUCCEEDED
# - Wait for orchestrator to drive session to REPORT_READY
# - Verify the report is queryable via GET /internal/sessions/{id}/report
#
# Requires: docker, jq, uuidgen, curl, openssl. Stack must be up:
#   make up && make smart-up && make orch-up

set -euo pipefail

ORCH_HOST="${ORCH_HOST:-http://localhost:8081}"
LOCALSTACK="fss-localstack"
BUCKET="fiap-secure-systems-assets"
SECRET="${INTERNAL_HMAC_SECRET:-change-me-32-bytes-min-for-real-deployments}"
DEADLINE_SECONDS="${DEADLINE_SECONDS:-45}"
FIXTURE="smart-service/tests/fixtures/sample-architecture.png"

green() { printf "\033[32m%s\033[0m\n" "$*"; }
red()   { printf "\033[31m%s\033[0m\n" "$*"; }

for cmd in docker jq uuidgen curl openssl; do
  command -v "$cmd" >/dev/null 2>&1 || { red "missing dependency: $cmd"; exit 2; }
done
[ -f "$FIXTURE" ] || { red "fixture not found: $FIXTURE (run from project root)"; exit 2; }
docker inspect fss-orchestrator-service >/dev/null 2>&1 \
  || { red "fss-orchestrator-service not running — try: make orch-up"; exit 2; }
docker inspect fss-smart-service >/dev/null 2>&1 \
  || { red "fss-smart-service not running — try: make smart-up"; exit 2; }

SESSION_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
USER_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
ASSET_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
S3_KEY="sessions/${SESSION_ID}/sample-architecture.png"

echo "→ sessionId=${SESSION_ID}"

docker cp "$FIXTURE" "$LOCALSTACK:/tmp/orch-rt.png" >/dev/null
docker exec "$LOCALSTACK" awslocal s3 cp /tmp/orch-rt.png "s3://${BUCKET}/${S3_KEY}" >/dev/null

BODY=$(jq -nc \
  --arg sid "$SESSION_ID" --arg uid "$USER_ID" --arg aid "$ASSET_ID" --arg key "$S3_KEY" \
  '{sessionId:$sid, userId:$uid, assetCount:1,
    assets:[{assetId:$aid, s3Key:$key, contentType:"image/png",
             filename:"sample-architecture.png", sizeBytes:70}]}')

TS=$(date +%s)
PATH_REQ="/internal/sessions"
BODY_SHA=$(printf "%s" "$BODY" | openssl dgst -sha256 -hex | awk '{print $2}')
CANON=$(printf "%s\n%s\n%s\n%s" "$TS" "POST" "$PATH_REQ" "$BODY_SHA")
SIG=$(printf "%s" "$CANON" | openssl dgst -sha256 -hmac "$SECRET" -hex | awk '{print $2}')

echo "→ POST ${ORCH_HOST}${PATH_REQ}"
HTTP=$(curl -sS -o /tmp/orch-rt-create.json -w "%{http_code}" -X POST "${ORCH_HOST}${PATH_REQ}" \
  -H "Content-Type: application/json" \
  -H "X-Internal-Timestamp: ${TS}" \
  -H "X-Internal-Signature: ${SIG}" \
  --data "$BODY")
[ "$HTTP" = "201" ] || { red "create failed: $HTTP $(cat /tmp/orch-rt-create.json)"; exit 1; }
green "  → 201 CREATED"

echo "→ polling GET ${PATH_REQ}/${SESSION_ID} until REPORT_READY (deadline ${DEADLINE_SECONDS}s)"
deadline=$(( $(date +%s) + DEADLINE_SECONDS ))
state="(none)"
while [ "$(date +%s)" -lt "$deadline" ]; do
  TS=$(date +%s)
  G_PATH="/internal/sessions/${SESSION_ID}"
  G_SHA=$(printf "" | openssl dgst -sha256 -hex | awk '{print $2}')
  G_CANON=$(printf "%s\n%s\n%s\n%s" "$TS" "GET" "$G_PATH" "$G_SHA")
  G_SIG=$(printf "%s" "$G_CANON" | openssl dgst -sha256 -hmac "$SECRET" -hex | awk '{print $2}')
  state=$(curl -sS "${ORCH_HOST}${G_PATH}" \
            -H "X-Internal-Timestamp: ${TS}" \
            -H "X-Internal-Signature: ${G_SIG}" | jq -r .state)
  printf "    state=%s\n" "$state"
  [ "$state" = "REPORT_READY" ] && break
  [ "$state" = "FAILED" ] && { red "session FAILED before REPORT_READY"; exit 1; }
  sleep 2
done
[ "$state" = "REPORT_READY" ] || { red "did not reach REPORT_READY (last=$state)"; exit 1; }
green "  → REPORT_READY"

echo "→ GET report"
TS=$(date +%s)
R_PATH="/internal/sessions/${SESSION_ID}/report"
R_SHA=$(printf "" | openssl dgst -sha256 -hex | awk '{print $2}')
R_CANON=$(printf "%s\n%s\n%s\n%s" "$TS" "GET" "$R_PATH" "$R_SHA")
R_SIG=$(printf "%s" "$R_CANON" | openssl dgst -sha256 -hmac "$SECRET" -hex | awk '{print $2}')
HTTP=$(curl -sS -o /tmp/orch-rt-report.json -w "%{http_code}" "${ORCH_HOST}${R_PATH}" \
  -H "X-Internal-Timestamp: ${TS}" \
  -H "X-Internal-Signature: ${R_SIG}")
[ "$HTTP" = "200" ] || { red "report fetch failed: $HTTP"; exit 1; }
SUMMARY=$(jq -r .summary /tmp/orch-rt-report.json)
[ -n "$SUMMARY" ] && [ "$SUMMARY" != "null" ] || { red "report has empty summary"; exit 1; }
green "  → got report, summary=\"${SUMMARY}\""

echo "→ checking SNS event delivery on session-events-gateway queue"
SNS_QUEUE="http://localhost:4566/000000000000/session-events-gateway"
events=$(docker exec "$LOCALSTACK" awslocal sqs receive-message \
  --queue-url "$SNS_QUEUE" --max-number-of-messages 10 --wait-time-seconds 2 \
  --query 'Messages[].Body' --output text 2>/dev/null || true)
matches=$(echo "$events" | tr ' ' '\n' | grep -c "$SESSION_ID" || true)
echo "    received ${matches} session-events for our sessionId"
[ "$matches" -ge 4 ] || { red "expected ≥ 4 session-events, got $matches"; exit 1; }
green "  → at least 4 transition events delivered"

green "✓ orchestrator round-trip OK"
