#!/usr/bin/env bash
set -euo pipefail

PASS=0
FAIL=0

check () {
  local label="$1" cmd="$2" expect="$3"
  local out
  if out=$(eval "$cmd" 2>&1); then
    if echo "$out" | grep -q "$expect"; then
      printf "  \033[32mOK\033[0m   %s\n" "$label"
      PASS=$((PASS+1))
      return 0
    fi
  fi
  printf "  \033[31mFAIL\033[0m %s  (got: %s)\n" "$label" "$(echo "$out" | head -c 200)"
  FAIL=$((FAIL+1))
}

echo "== Postgres =="
for db in gateway_db orchestrator_db smart_db; do
  check "$db exists" \
    "docker exec fss-postgres psql -U postgres -tAc \"SELECT 1 FROM pg_database WHERE datname='$db'\"" \
    "1"
done

echo "== LocalStack: S3 =="
check "bucket fiap-secure-systems-assets" \
  "docker exec fss-localstack awslocal s3api list-buckets --query 'Buckets[].Name' --output text" \
  "fiap-secure-systems-assets"

echo "== LocalStack: SNS =="
check "topic session-events" \
  "docker exec fss-localstack awslocal sns list-topics --query 'Topics[].TopicArn' --output text" \
  ":session-events"

echo "== LocalStack: SQS =="
for q in analysis-jobs analysis-jobs-dlq \
         analysis-results analysis-results-dlq \
         session-events-gateway session-events-gateway-dlq; do
  check "queue $q" \
    "docker exec fss-localstack awslocal sqs list-queues --query 'QueueUrls[]' --output text" \
    "/$q"
done

echo "== LocalStack: subscription =="
check "session-events → session-events-gateway" \
  "docker exec fss-localstack awslocal sns list-subscriptions --query 'Subscriptions[].Endpoint' --output text" \
  ":session-events-gateway"

echo "== OTel Collector =="
check "health" \
  "curl -fsS http://localhost:13133/" \
  "Server available"

echo
printf "PASS=%d FAIL=%d\n" "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
