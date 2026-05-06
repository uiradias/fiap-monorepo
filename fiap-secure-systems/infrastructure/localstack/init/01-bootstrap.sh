#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
ACCOUNT="000000000000"

echo "[bootstrap] creating S3 bucket"
awslocal s3api create-bucket --bucket fiap-secure-systems-assets --region "$REGION" >/dev/null
awslocal s3api put-bucket-encryption \
  --bucket fiap-secure-systems-assets \
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' >/dev/null

echo "[bootstrap] creating SNS topic"
TOPIC_ARN=$(awslocal sns create-topic --name session-events --query TopicArn --output text)
echo "[bootstrap] topic arn: $TOPIC_ARN"

create_queue () {
  local name="$1" dlq="$2"
  echo "[bootstrap] creating queue $name (dlq=$dlq)"
  local dlq_url dlq_arn
  awslocal sqs create-queue --queue-name "$dlq" >/dev/null
  dlq_url=$(awslocal sqs get-queue-url --queue-name "$dlq" --query QueueUrl --output text)
  dlq_arn=$(awslocal sqs get-queue-attributes --queue-url "$dlq_url" \
    --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)
  awslocal sqs create-queue \
    --queue-name "$name" \
    --attributes "{\"VisibilityTimeout\":\"300\",\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"$dlq_arn\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"}" \
    >/dev/null
}

create_queue analysis-jobs           analysis-jobs-dlq
create_queue analysis-results        analysis-results-dlq
create_queue session-events-gateway  session-events-gateway-dlq

echo "[bootstrap] subscribing session-events-gateway to SNS topic"
QUEUE_ARN=$(awslocal sqs get-queue-attributes \
  --queue-url "http://localhost:4566/${ACCOUNT}/session-events-gateway" \
  --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)
awslocal sns subscribe \
  --topic-arn "$TOPIC_ARN" \
  --protocol sqs \
  --notification-endpoint "$QUEUE_ARN" \
  --attributes "RawMessageDelivery=true" >/dev/null

echo "[bootstrap] done"
