"""Drains a DLQ back into its primary queue. Implements DlqReplayerPort.

Naming convention: a DLQ named `<queue>-dlq` maps to primary queue `<queue>`.
"""
from __future__ import annotations

import boto3


class SqsDlqReplayer:
    def __init__(
        self,
        *,
        endpoint_url: str,
        region: str,
        access_key: str,
        secret_key: str,
    ) -> None:
        self._sqs = boto3.client(
            "sqs",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    def replay_dlq(self, queue: str) -> int:
        if not queue.endswith("-dlq"):
            raise ValueError(f"not a DLQ name: {queue!r}")
        primary = queue.removesuffix("-dlq")
        dlq_url = self._sqs.get_queue_url(QueueName=queue)["QueueUrl"]
        primary_url = self._sqs.get_queue_url(QueueName=primary)["QueueUrl"]

        moved = 0
        while True:
            resp = self._sqs.receive_message(
                QueueUrl=dlq_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=1,
            )
            msgs = resp.get("Messages", [])
            if not msgs:
                break
            for m in msgs:
                self._sqs.send_message(QueueUrl=primary_url, MessageBody=m["Body"])
                self._sqs.delete_message(QueueUrl=dlq_url, ReceiptHandle=m["ReceiptHandle"])
                moved += 1
        return moved
