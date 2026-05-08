"""S3 asset reader. Implements `AssetReaderPort` (structural)."""
from __future__ import annotations

import boto3
from botocore.exceptions import ClientError

from smart_service.domain.model import Asset


class S3AssetReadError(Exception):
    """Raised when an asset cannot be read (missing object, network failure, etc.)."""


class S3AssetReader:
    def __init__(
        self,
        *,
        endpoint_url: str,
        region: str,
        access_key: str,
        secret_key: str,
        bucket: str,
    ) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        self._bucket = bucket

    def read(self, asset: Asset) -> bytes:
        try:
            obj = self._client.get_object(Bucket=self._bucket, Key=asset.s3_key)
        except ClientError as e:
            raise S3AssetReadError(
                f"failed to read s3://{self._bucket}/{asset.s3_key}: {e}"
            ) from e
        body: bytes = obj["Body"].read()
        return body
