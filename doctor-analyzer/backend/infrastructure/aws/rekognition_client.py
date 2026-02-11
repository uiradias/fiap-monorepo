"""AWS Rekognition client for video emotion analysis."""

import boto3
from typing import List, AsyncIterator, Optional
import asyncio
from functools import partial
import logging

from config.settings import AWSSettings
from domain.emotion import (
    EmotionType,
    EmotionScore,
    BoundingBox,
    FaceDetection,
)

logger = logging.getLogger(__name__)

# Rekognition emotion to our EmotionType mapping
EMOTION_MAPPING = {
    "HAPPY": EmotionType.HAPPY,
    "SAD": EmotionType.SAD,
    "ANGRY": EmotionType.ANGRY,
    "CONFUSED": EmotionType.CONFUSED,
    "DISGUSTED": EmotionType.DISGUSTED,
    "SURPRISED": EmotionType.SURPRISED,
    "CALM": EmotionType.CALM,
    "FEAR": EmotionType.FEAR,
}


class RekognitionClient:
    """Wrapper for AWS Rekognition video analysis."""

    def __init__(self, settings: AWSSettings):
        self._settings = settings
        self._client = boto3.client(
            'rekognition',
            region_name=settings.region,
            aws_access_key_id=settings.access_key_id,
            aws_secret_access_key=settings.secret_access_key,
        )

    async def start_face_detection(self, s3_bucket: str, s3_key: str) -> str:
        """
        Start asynchronous face detection job.

        Returns:
            Job ID for tracking the analysis.
        """
        params = {
            'Video': {
                'S3Object': {
                    'Bucket': s3_bucket,
                    'Name': s3_key,
                }
            },
            'FaceAttributes': 'ALL',
        }

        # Add notification if configured
        if self._settings.sns_topic_arn and self._settings.rekognition_role_arn:
            params['NotificationChannel'] = {
                'SNSTopicArn': self._settings.sns_topic_arn,
                'RoleArn': self._settings.rekognition_role_arn,
            }

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, partial(self._client.start_face_detection, **params)
        )
        job_id = response['JobId']
        logger.info(f"Started face detection job: {job_id}")
        return job_id

    async def get_face_detection_status(self, job_id: str) -> str:
        """Get status of face detection job."""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, partial(self._client.get_face_detection, JobId=job_id, MaxResults=1)
        )
        return response['JobStatus']

    async def get_face_detection_results(
        self,
        job_id: str,
        poll_interval: float = 5.0,
    ) -> AsyncIterator[FaceDetection]:
        """
        Poll for and yield face detection results as they become available.

        This is designed for streaming results back to the frontend.
        """
        next_token = None
        job_complete = False

        while not job_complete:
            kwargs = {'JobId': job_id, 'MaxResults': 100}
            if next_token:
                kwargs['NextToken'] = next_token

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, partial(self._client.get_face_detection, **kwargs)
            )
            status = response['JobStatus']

            if status == 'FAILED':
                error_msg = response.get('StatusMessage', 'Unknown error')
                logger.error(f"Rekognition job failed: {error_msg}")
                raise RuntimeError(f"Rekognition job failed: {error_msg}")

            if status == 'IN_PROGRESS':
                logger.debug(f"Job {job_id} still in progress, waiting...")
                await asyncio.sleep(poll_interval)
                continue

            # Process faces from this page
            for face_record in response.get('Faces', []):
                face = face_record['Face']
                timestamp = face_record['Timestamp']

                emotions = self._parse_emotions(face.get('Emotions', []))
                bounding_box = self._parse_bounding_box(face['BoundingBox'])

                yield FaceDetection(
                    timestamp_ms=timestamp,
                    bounding_box=bounding_box,
                    emotions=emotions,
                    age_range=face.get('AgeRange'),
                    gender=face.get('Gender', {}).get('Value'),
                )

            next_token = response.get('NextToken')
            if not next_token:
                job_complete = True

        logger.info(f"Completed processing face detection job: {job_id}")

    def _parse_emotions(self, emotions_data: list) -> List[EmotionScore]:
        """Parse Rekognition emotions and add derived emotions."""
        emotions = []
        emotion_dict = {}

        for e in emotions_data:
            emotion_type = EMOTION_MAPPING.get(e['Type'])
            if emotion_type:
                confidence = e['Confidence'] / 100.0
                emotions.append(EmotionScore(emotion=emotion_type, confidence=confidence))
                emotion_dict[emotion_type] = confidence

        # Add derived emotions for clinical indicators
        # Discomfort: combination of disgusted, confused, and sad
        discomfort_score = (
            emotion_dict.get(EmotionType.DISGUSTED, 0) * 0.4 +
            emotion_dict.get(EmotionType.CONFUSED, 0) * 0.3 +
            emotion_dict.get(EmotionType.SAD, 0) * 0.3
        )
        emotions.append(EmotionScore(emotion=EmotionType.DISCOMFORT, confidence=discomfort_score))

        # Anxiety: combination of fear and surprised
        anxiety_score = (
            emotion_dict.get(EmotionType.FEAR, 0) * 0.7 +
            emotion_dict.get(EmotionType.SURPRISED, 0) * 0.3
        )
        emotions.append(EmotionScore(emotion=EmotionType.ANXIETY, confidence=anxiety_score))

        # Depression: based on sad with modifiers
        depression_score = (
            emotion_dict.get(EmotionType.SAD, 0) * 0.6 +
            (1 - emotion_dict.get(EmotionType.HAPPY, 0)) * 0.2 +
            emotion_dict.get(EmotionType.CALM, 0) * 0.2
        )
        emotions.append(EmotionScore(emotion=EmotionType.DEPRESSION, confidence=depression_score))

        return emotions

    def _parse_bounding_box(self, bbox: dict) -> BoundingBox:
        """Parse Rekognition bounding box."""
        return BoundingBox(
            left=bbox['Left'],
            top=bbox['Top'],
            width=bbox['Width'],
            height=bbox['Height'],
        )

    async def detect_faces_in_image(self, image_bytes: bytes) -> List[FaceDetection]:
        """Detect faces in a single image (for testing/preview)."""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, partial(self._client.detect_faces, Image={'Bytes': image_bytes}, Attributes=['ALL'])
        )

        detections = []
        for face in response.get('FaceDetails', []):
            emotions = self._parse_emotions(face.get('Emotions', []))
            bounding_box = self._parse_bounding_box(face['BoundingBox'])

            detections.append(FaceDetection(
                timestamp_ms=0,
                bounding_box=bounding_box,
                emotions=emotions,
                age_range=face.get('AgeRange'),
                gender=face.get('Gender', {}).get('Value'),
            ))

        return detections
