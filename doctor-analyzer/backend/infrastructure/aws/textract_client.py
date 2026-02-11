"""AWS Textract client for PDF text extraction."""

import boto3
from typing import Optional
from functools import partial
import asyncio
import logging

from config.settings import AWSSettings

logger = logging.getLogger(__name__)


class TextractClient:
    """Wrapper for AWS Textract document text extraction."""

    def __init__(self, settings: AWSSettings):
        self._settings = settings
        self._client = boto3.client(
            'textract',
            region_name=settings.region,
            aws_access_key_id=settings.access_key_id,
            aws_secret_access_key=settings.secret_access_key,
        )

    async def _run_sync(self, func, *args, **kwargs):
        """Run a synchronous boto3 call in a thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))

    async def extract_text_from_s3(
        self,
        s3_bucket: str,
        s3_key: str,
    ) -> str:
        """
        Extract text from a document in S3.

        For multi-page documents, uses async document analysis.
        For single-page, uses synchronous detection.

        Args:
            s3_bucket: S3 bucket name
            s3_key: S3 key of the document

        Returns:
            Extracted text from the document
        """
        # Start async analysis for potentially multi-page documents
        job_id = await self._start_document_text_detection(s3_bucket, s3_key)
        return await self._wait_and_get_results(job_id)

    async def _start_document_text_detection(self, s3_bucket: str, s3_key: str) -> str:
        """Start async document text detection."""
        response = await self._run_sync(self._client.start_document_text_detection,
            DocumentLocation={
                'S3Object': {
                    'Bucket': s3_bucket,
                    'Name': s3_key,
                }
            }
        )
        job_id = response['JobId']
        logger.info(f"Started Textract job: {job_id}")
        return job_id

    async def _wait_and_get_results(
        self,
        job_id: str,
        poll_interval: float = 2.0,
        max_wait: float = 300.0,
    ) -> str:
        """Wait for job completion and get extracted text."""
        elapsed = 0.0

        while elapsed < max_wait:
            response = await self._run_sync(self._client.get_document_text_detection, JobId=job_id)
            status = response['JobStatus']

            if status == 'SUCCEEDED':
                return await self._parse_text_from_response(response, job_id)

            if status == 'FAILED':
                error = response.get('StatusMessage', 'Unknown error')
                raise RuntimeError(f"Textract job failed: {error}")

            logger.debug(f"Textract job {job_id} status: {status}")
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"Textract job {job_id} timed out")

    async def _parse_text_from_response(self, response: dict, job_id: str) -> str:
        """Parse text from Textract response, handling pagination."""
        all_text = []
        next_token = None

        # Process first page
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                all_text.append(block['Text'])

        next_token = response.get('NextToken')

        # Process additional pages
        while next_token:
            response = await self._run_sync(
                self._client.get_document_text_detection,
                JobId=job_id,
                NextToken=next_token,
            )

            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    all_text.append(block['Text'])

            next_token = response.get('NextToken')

        text = '\n'.join(all_text)
        logger.info(f"Extracted {len(text)} characters from document")
        return text

    async def extract_text_from_bytes(self, document_bytes: bytes) -> str:
        """
        Extract text from document bytes (synchronous, single page only).

        Args:
            document_bytes: Document content as bytes

        Returns:
            Extracted text
        """
        response = await self._run_sync(
            self._client.detect_document_text,
            Document={'Bytes': document_bytes},
        )

        text_lines = []
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text_lines.append(block['Text'])

        return '\n'.join(text_lines)

    async def analyze_document(
        self,
        s3_bucket: str,
        s3_key: str,
        feature_types: Optional[list] = None,
    ) -> dict:
        """
        Analyze document for forms, tables, and text.

        Args:
            s3_bucket: S3 bucket name
            s3_key: S3 key of the document
            feature_types: List of features to detect (TABLES, FORMS)

        Returns:
            Dictionary with extracted text, tables, and forms
        """
        if feature_types is None:
            feature_types = ['TABLES', 'FORMS']

        response = await self._run_sync(self._client.start_document_analysis,
            DocumentLocation={
                'S3Object': {
                    'Bucket': s3_bucket,
                    'Name': s3_key,
                }
            },
            FeatureTypes=feature_types,
        )

        job_id = response['JobId']
        logger.info(f"Started Textract analysis job: {job_id}")

        # Wait for completion
        elapsed = 0.0
        while elapsed < 300.0:
            response = await self._run_sync(self._client.get_document_analysis, JobId=job_id)
            status = response['JobStatus']

            if status == 'SUCCEEDED':
                return await self._parse_analysis_response(response, job_id)

            if status == 'FAILED':
                raise RuntimeError(f"Textract analysis failed: {response.get('StatusMessage')}")

            await asyncio.sleep(2.0)
            elapsed += 2.0

        raise TimeoutError("Textract analysis timed out")

    async def _parse_analysis_response(self, response: dict, job_id: str) -> dict:
        """Parse analysis response into structured data."""
        result = {
            'text': [],
            'tables': [],
            'forms': [],
        }

        blocks_by_id = {}

        # First pass: collect all blocks
        for block in response.get('Blocks', []):
            blocks_by_id[block['Id']] = block

            if block['BlockType'] == 'LINE':
                result['text'].append(block['Text'])

        # Handle pagination
        next_token = response.get('NextToken')
        while next_token:
            response = await self._run_sync(
                self._client.get_document_analysis,
                JobId=job_id,
                NextToken=next_token,
            )

            for block in response.get('Blocks', []):
                blocks_by_id[block['Id']] = block
                if block['BlockType'] == 'LINE':
                    result['text'].append(block['Text'])

            next_token = response.get('NextToken')

        result['full_text'] = '\n'.join(result['text'])
        return result
