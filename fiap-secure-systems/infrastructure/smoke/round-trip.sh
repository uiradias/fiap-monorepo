#!/usr/bin/env bash
# End-to-end synthetic round-trip for smart-service.
#
# Generates fresh UUIDs, uploads the fixture PNG to S3, sends an analysis-job
# to SQS, then polls analysis-results until both STARTED and SUCCEEDED arrive
# for that jobId. Filters by jobId so leftover messages from prior runs are
# ignored. Each matching response is consumed (delete-message) so the queue
# is clean afterwards. Exits non-zero if both statuses don't show within the
# deadline.
#
# Requires: docker, jq, uuidgen. Stack must be up (`make up`) with smart-service
# running in SMART_SERVICE_PROFILE=e2e (FakeAnalysisModel) or production with a
# real ANTHROPIC_API_KEY.

set -euo pipefail

QUEUE_JOBS="http://localhost:4566/000000000000/analysis-jobs"
QUEUE_RESULTS="http://localhost:4566/000000000000/analysis-results"
# When orchestrator-service is also running, it consumes analysis-results and
# treats this script's synthetic sessionIds as poison pills (no matching session
# in its DB), forwarding them to the DLQ. So we poll both queues — the message
# lands in whichever the orchestrator did not race us to.
QUEUE_RESULTS_DLQ="http://localhost:4566/000000000000/analysis-results-dlq"
BUCKET="fiap-secure-systems-assets"
DEADLINE_SECONDS="${DEADLINE_SECONDS:-30}"
FIXTURE="smart-service/tests/fixtures/sample-architecture.png"

green() { printf "\033[32m%s\033[0m\n" "$*"; }
red()   { printf "\033[31m%s\033[0m\n" "$*"; }

# Pre-flight
for cmd in docker jq uuidgen; do
  command -v "$cmd" >/dev/null 2>&1 || { red "missing dependency: $cmd"; exit 2; }
done
[ -f "$FIXTURE" ] || { red "fixture not found: $FIXTURE (run from project root)"; exit 2; }
docker inspect fss-localstack >/dev/null 2>&1 || { red "fss-localstack not running — try: make up"; exit 2; }
docker inspect fss-smart-service >/dev/null 2>&1 || { red "fss-smart-service not running — try: make up"; exit 2; }

JOB_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
SESSION_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
ASSET_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
S3_KEY="sessions/${SESSION_ID}/sample-architecture.png"

echo "→ jobId=${JOB_ID}"
echo "→ sessionId=${SESSION_ID}"

# Upload the asset
echo "→ uploading fixture to s3://${BUCKET}/${S3_KEY}"
docker cp "$FIXTURE" fss-localstack:/tmp/round-trip.png >/dev/null
docker exec fss-localstack awslocal s3 cp /tmp/round-trip.png \
  "s3://${BUCKET}/${S3_KEY}" >/dev/null

# Build the job body in a temp file (no shell-quoting traps)
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT
cat > "$TMP" <<JSON
{
  "schemaVersion": 1,
  "jobId": "${JOB_ID}",
  "sessionId": "${SESSION_ID}",
  "userId": "00000000-0000-4000-8000-000000000001",
  "assets": [{
    "assetId": "${ASSET_ID}",
    "s3Key": "${S3_KEY}",
    "contentType": "image/png",
    "filename": "sample-architecture.png",
    "sizeBytes": 70
  }],
  "promptVersion": "v1",
  "submittedAt": "${TS}"
}
JSON
docker cp "$TMP" fss-localstack:/tmp/round-trip-job.json >/dev/null

echo "→ sending analysis-job"
docker exec fss-localstack awslocal sqs send-message \
  --queue-url "${QUEUE_JOBS}" \
  --message-body file:///tmp/round-trip-job.json >/dev/null

echo "→ waiting up to ${DEADLINE_SECONDS}s for STARTED + SUCCEEDED on analysis-results (or DLQ)"
deadline=$(( $(date +%s) + DEADLINE_SECONDS ))
seen_started=0
seen_succeeded=0

drain_one() {
  # $1 = queue url. Receives one message, matches against JOB_ID, marks seen_*
  # if matched, otherwise releases visibility on non-DLQ queues so other readers
  # can see it. DLQ is terminal — we delete unmatched DLQ entries to avoid
  # mis-attributing leftovers.
  local q="$1" resp body receipt msg_job status
  resp=$(docker exec fss-localstack awslocal sqs receive-message \
    --queue-url "$q" --max-number-of-messages 1 --wait-time-seconds 1 \
    --output json 2>/dev/null || true)
  body=$(echo "$resp" | jq -r '.Messages[0].Body // empty')
  receipt=$(echo "$resp" | jq -r '.Messages[0].ReceiptHandle // empty')
  [ -z "$body" ] && return 0

  msg_job=$(echo "$body" | jq -r '.jobId')
  status=$(echo "$body" | jq -r '.status')
  if [ "$msg_job" = "${JOB_ID}" ]; then
    printf "    queue=%-20s status=%-9s jobId=%s\n" "$(basename "$q")" "$status" "$msg_job"
    [ "$status" = "STARTED" ]   && seen_started=1
    [ "$status" = "SUCCEEDED" ] && seen_succeeded=1
    docker exec fss-localstack awslocal sqs delete-message \
      --queue-url "$q" --receipt-handle "$receipt" >/dev/null
  else
    if [ "$q" = "${QUEUE_RESULTS_DLQ}" ]; then
      docker exec fss-localstack awslocal sqs delete-message \
        --queue-url "$q" --receipt-handle "$receipt" >/dev/null 2>&1 || true
    else
      docker exec fss-localstack awslocal sqs change-message-visibility \
        --queue-url "$q" --receipt-handle "$receipt" \
        --visibility-timeout 0 >/dev/null 2>&1 || true
    fi
  fi
}

while [ "$(date +%s)" -lt "$deadline" ]; do
  drain_one "${QUEUE_RESULTS}"
  drain_one "${QUEUE_RESULTS_DLQ}"
  [ $seen_started -eq 1 ] && [ $seen_succeeded -eq 1 ] && break
done

if [ $seen_started -eq 1 ] && [ $seen_succeeded -eq 1 ]; then
  green "✓ round-trip OK"
  exit 0
fi
red "✗ round-trip FAILED (started=$seen_started succeeded=$seen_succeeded)"
exit 1
