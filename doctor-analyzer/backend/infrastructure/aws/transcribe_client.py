"""AWS Transcribe client for audio transcription."""

import boto3
from typing import List, Optional
from functools import partial
from urllib.parse import urlparse
import asyncio
import logging
import json

from config.settings import AWSSettings
from domain.analysis import TranscriptionSegment

logger = logging.getLogger(__name__)


class TranscribeClient:
    """Wrapper for AWS Transcribe audio transcription."""

    def __init__(self, settings: AWSSettings):
        self._settings = settings
        self._client = boto3.client(
            'transcribe',
            region_name=settings.region,
            aws_access_key_id=settings.access_key_id,
            aws_secret_access_key=settings.secret_access_key,
        )
        self._s3_client = boto3.client(
            's3',
            region_name=settings.region,
            aws_access_key_id=settings.access_key_id,
            aws_secret_access_key=settings.secret_access_key,
        )

    async def _run_sync(self, func, *args, **kwargs):
        """Run a synchronous boto3 call in a thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))

    async def start_transcription_job(
        self,
        job_name: str,
        s3_uri: str,
        language_code: str = 'en-US',
        output_bucket: Optional[str] = None,
        output_key: Optional[str] = None,
    ) -> str:
        """
        Start an asynchronous transcription job.

        Args:
            job_name: Unique name for the job
            s3_uri: S3 URI of the audio/video file
            language_code: Language code (default: en-US)
            output_bucket: Optional S3 bucket for output
            output_key: Optional S3 key for output (requires output_bucket)

        Returns:
            Job name for tracking
        """
        params = {
            'TranscriptionJobName': job_name,
            'Media': {'MediaFileUri': s3_uri},
            'LanguageCode': language_code,
            'Settings': {
                'ShowSpeakerLabels': True,
                'MaxSpeakerLabels': 5,
            },
        }

        if output_bucket:
            params['OutputBucketName'] = output_bucket
            if output_key:
                params['OutputKey'] = output_key

        await self._run_sync(self._client.start_transcription_job, **params)
        logger.info(f"Started transcription job: {job_name}")
        return job_name

    async def get_transcription_status(self, job_name: str) -> dict:
        """Get status of transcription job."""
        response = await self._run_sync(
            self._client.get_transcription_job,
            TranscriptionJobName=job_name,
        )
        job = response['TranscriptionJob']
        return {
            'status': job['TranscriptionJobStatus'],
            'transcript_uri': job.get('Transcript', {}).get('TranscriptFileUri'),
            'failure_reason': job.get('FailureReason'),
        }

    async def wait_for_transcription(
        self,
        job_name: str,
        poll_interval: float = 5.0,
        max_wait: float = 600.0,
    ) -> List[TranscriptionSegment]:
        """
        Wait for transcription job to complete and return segments.

        Args:
            job_name: Transcription job name
            poll_interval: Seconds between status checks
            max_wait: Maximum seconds to wait

        Returns:
            List of transcription segments
        """
        elapsed = 0.0

        while elapsed < max_wait:
            status = await self.get_transcription_status(job_name)

            if status['status'] == 'COMPLETED':
                transcript_uri = status['transcript_uri']
                return await self._fetch_and_parse_transcript(transcript_uri)

            if status['status'] == 'FAILED':
                raise RuntimeError(f"Transcription failed: {status['failure_reason']}")

            logger.debug(f"Transcription job {job_name} status: {status['status']}")
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"Transcription job {job_name} timed out after {max_wait}s")

    def _parse_s3_uri(self, uri: str) -> tuple:
        """Extract bucket and key from an s3:// URI or https S3 URL."""
        parsed = urlparse(uri)
        if parsed.scheme == 's3':
            return parsed.netloc, parsed.path.lstrip('/')
        # https://s3.region.amazonaws.com/bucket/key or
        # https://bucket.s3.region.amazonaws.com/key
        host = parsed.hostname or ''
        if host.endswith('.amazonaws.com'):
            path_parts = parsed.path.lstrip('/').split('/', 1)
            if host.startswith('s3'):
                # path-style: https://s3.region.amazonaws.com/bucket/key
                return path_parts[0], path_parts[1] if len(path_parts) > 1 else ''
            else:
                # virtual-hosted: https://bucket.s3.region.amazonaws.com/key
                bucket = host.split('.s3')[0]
                return bucket, parsed.path.lstrip('/')
        raise ValueError(f"Cannot parse S3 location from URI: {uri}")

    async def _fetch_and_parse_transcript(self, uri: str) -> List[TranscriptionSegment]:
        """Fetch transcript from S3 via boto3 and parse into segments."""
        bucket, key = self._parse_s3_uri(uri)
        response = await self._run_sync(
            self._s3_client.get_object,
            Bucket=bucket,
            Key=key,
        )
        body = await self._run_sync(response['Body'].read)
        data = json.loads(body)

        segments = []
        results = data.get('results', {})

        # Parse items for word-level timing
        items = results.get('items', [])
        current_segment_text = []
        segment_start = None
        segment_end = None

        for item in items:
            if item['type'] == 'pronunciation':
                word = item['alternatives'][0]['content']
                confidence = float(item['alternatives'][0].get('confidence', 0))
                start_time = float(item.get('start_time', 0))
                end_time = float(item.get('end_time', 0))

                if segment_start is None:
                    segment_start = start_time

                segment_end = end_time
                current_segment_text.append(word)

                # Create segment every ~10 words or at sentence end
                if len(current_segment_text) >= 10 or word.endswith(('.', '?', '!')):
                    segments.append(TranscriptionSegment(
                        text=' '.join(current_segment_text),
                        start_time=segment_start,
                        end_time=segment_end,
                        confidence=confidence,
                        speaker_label=None,
                    ))
                    current_segment_text = []
                    segment_start = None

            elif item['type'] == 'punctuation':
                if current_segment_text:
                    current_segment_text[-1] += item['alternatives'][0]['content']

        # Add remaining text
        if current_segment_text and segment_start is not None:
            segments.append(TranscriptionSegment(
                text=' '.join(current_segment_text),
                start_time=segment_start,
                end_time=segment_end or segment_start,
                confidence=0.0,
                speaker_label=None,
            ))

        logger.info(f"Parsed {len(segments)} transcription segments")
        return segments

    async def delete_transcription_job(self, job_name: str) -> bool:
        """Delete a transcription job."""
        try:
            await self._run_sync(self._client.delete_transcription_job, TranscriptionJobName=job_name)
            logger.info(f"Deleted transcription job: {job_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete transcription job: {e}")
            return False
