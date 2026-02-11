"""AWS S3 client for file storage operations."""

import boto3
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO
from functools import partial
import asyncio
import json
import logging

from config.settings import AWSSettings

logger = logging.getLogger(__name__)


class S3Client:
    """Wrapper for AWS S3 operations."""

    def __init__(self, settings: AWSSettings):
        self._settings = settings
        self._client = boto3.client(
            's3',
            region_name=settings.region,
            aws_access_key_id=settings.access_key_id,
            aws_secret_access_key=settings.secret_access_key,
        )
        self._bucket = settings.s3_bucket

    @property
    def bucket_name(self) -> str:
        return self._bucket

    async def _run_sync(self, func, *args, **kwargs):
        """Run a synchronous boto3 call in a thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))

    async def upload_file(
        self,
        file_obj: BinaryIO,
        s3_key: str,
        content_type: Optional[str] = None,
    ) -> str:
        """
        Upload a file to S3.

        Args:
            file_obj: File-like object to upload
            s3_key: S3 key (path) for the file
            content_type: Optional MIME type

        Returns:
            S3 URI of the uploaded file
        """
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type

        try:
            await self._run_sync(
                self._client.upload_fileobj,
                file_obj,
                self._bucket,
                s3_key,
                ExtraArgs=extra_args if extra_args else None,
            )
            logger.info(f"Uploaded file to s3://{self._bucket}/{s3_key}")
            return f"s3://{self._bucket}/{s3_key}"
        except ClientError as e:
            logger.error(f"Failed to upload file: {e}")
            raise

    async def upload_bytes(
        self,
        data: bytes,
        s3_key: str,
        content_type: Optional[str] = None,
    ) -> str:
        """Upload bytes to S3."""
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type

        try:
            await self._run_sync(
                self._client.put_object,
                Bucket=self._bucket,
                Key=s3_key,
                Body=data,
                **(extra_args if extra_args else {}),
            )
            logger.info(f"Uploaded bytes to s3://{self._bucket}/{s3_key}")
            return f"s3://{self._bucket}/{s3_key}"
        except ClientError as e:
            logger.error(f"Failed to upload bytes: {e}")
            raise

    async def upload_json(self, data: dict, s3_key: str) -> str:
        """Upload JSON data to S3."""
        json_bytes = json.dumps(data, indent=2, default=str).encode('utf-8')
        return await self.upload_bytes(json_bytes, s3_key, 'application/json')

    async def download_file(self, s3_key: str) -> bytes:
        """Download a file from S3."""
        try:
            response = await self._run_sync(self._client.get_object, Bucket=self._bucket, Key=s3_key)
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, response['Body'].read)
        except ClientError as e:
            logger.error(f"Failed to download file: {e}")
            raise

    async def get_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600,
        operation: str = 'get_object',
    ) -> str:
        """
        Generate a presigned URL for S3 object access.

        Args:
            s3_key: S3 key of the object
            expiration: URL expiration time in seconds
            operation: 'get_object' or 'put_object'

        Returns:
            Presigned URL
        """
        try:
            url = await self._run_sync(
                self._client.generate_presigned_url,
                operation,
                Params={'Bucket': self._bucket, 'Key': s3_key},
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise

    async def delete_file(self, s3_key: str) -> bool:
        """Delete a file from S3."""
        try:
            await self._run_sync(self._client.delete_object, Bucket=self._bucket, Key=s3_key)
            logger.info(f"Deleted s3://{self._bucket}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file: {e}")
            return False

    async def list_files(self, prefix: str) -> list:
        """List files in S3 with given prefix."""
        try:
            response = await self._run_sync(
                self._client.list_objects_v2,
                Bucket=self._bucket,
                Prefix=prefix,
            )
            return [obj['Key'] for obj in response.get('Contents', [])]
        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            return []

    async def file_exists(self, s3_key: str) -> bool:
        """Check if a file exists in S3."""
        try:
            await self._run_sync(self._client.head_object, Bucket=self._bucket, Key=s3_key)
            return True
        except ClientError:
            return False
