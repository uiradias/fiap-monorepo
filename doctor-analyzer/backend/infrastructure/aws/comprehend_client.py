"""AWS Comprehend client for sentiment analysis."""

import boto3
from typing import List, Optional
from functools import partial
import asyncio
import logging

from config.settings import AWSSettings
from domain.analysis import SentimentResult

logger = logging.getLogger(__name__)


class ComprehendClient:
    """Wrapper for AWS Comprehend NLP analysis."""

    def __init__(self, settings: AWSSettings):
        self._settings = settings
        self._client = boto3.client(
            'comprehend',
            region_name=settings.region,
            aws_access_key_id=settings.access_key_id,
            aws_secret_access_key=settings.secret_access_key,
        )

    async def _run_sync(self, func, *args, **kwargs):
        """Run a synchronous boto3 call in a thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))

    async def detect_sentiment(
        self,
        text: str,
        language_code: str = 'en',
    ) -> SentimentResult:
        """
        Detect sentiment of text.

        Args:
            text: Text to analyze (max 5000 bytes)
            language_code: Language code (default: en)

        Returns:
            SentimentResult with sentiment and scores
        """
        # Truncate text if too long (Comprehend limit is 5000 bytes)
        if len(text.encode('utf-8')) > 5000:
            text = text[:4500]
            logger.warning("Text truncated for sentiment analysis")

        response = await self._run_sync(
            self._client.detect_sentiment,
            Text=text,
            LanguageCode=language_code,
        )

        scores = response['SentimentScore']
        return SentimentResult(
            sentiment=response['Sentiment'],
            positive_score=scores['Positive'],
            negative_score=scores['Negative'],
            neutral_score=scores['Neutral'],
            mixed_score=scores['Mixed'],
            source_text=text[:200],  # Store first 200 chars for reference
        )

    async def batch_detect_sentiment(
        self,
        texts: List[str],
        language_code: str = 'en',
    ) -> List[SentimentResult]:
        """
        Detect sentiment for multiple texts in batch.

        Args:
            texts: List of texts to analyze (max 25 items)
            language_code: Language code

        Returns:
            List of SentimentResult
        """
        # Comprehend batch limit is 25
        if len(texts) > 25:
            results = []
            for i in range(0, len(texts), 25):
                batch = texts[i:i + 25]
                results.extend(await self.batch_detect_sentiment(batch, language_code))
            return results

        # Truncate texts if needed
        truncated_texts = []
        for text in texts:
            if len(text.encode('utf-8')) > 5000:
                truncated_texts.append(text[:4500])
            else:
                truncated_texts.append(text)

        response = await self._run_sync(
            self._client.batch_detect_sentiment,
            TextList=truncated_texts,
            LanguageCode=language_code,
        )

        results = []
        for i, result in enumerate(response['ResultList']):
            scores = result['SentimentScore']
            results.append(SentimentResult(
                sentiment=result['Sentiment'],
                positive_score=scores['Positive'],
                negative_score=scores['Negative'],
                neutral_score=scores['Neutral'],
                mixed_score=scores['Mixed'],
                source_text=truncated_texts[result['Index']][:200],
            ))

        return results

    async def detect_key_phrases(
        self,
        text: str,
        language_code: str = 'en',
    ) -> List[str]:
        """
        Detect key phrases in text.

        Args:
            text: Text to analyze
            language_code: Language code

        Returns:
            List of key phrases
        """
        if len(text.encode('utf-8')) > 5000:
            text = text[:4500]

        response = await self._run_sync(
            self._client.detect_key_phrases,
            Text=text,
            LanguageCode=language_code,
        )

        # Return phrases sorted by score
        phrases = sorted(
            response['KeyPhrases'],
            key=lambda x: x['Score'],
            reverse=True,
        )

        return [p['Text'] for p in phrases]

    async def detect_entities(
        self,
        text: str,
        language_code: str = 'en',
    ) -> List[dict]:
        """
        Detect entities in text.

        Args:
            text: Text to analyze
            language_code: Language code

        Returns:
            List of entity dictionaries with type, text, and score
        """
        if len(text.encode('utf-8')) > 5000:
            text = text[:4500]

        response = await self._run_sync(
            self._client.detect_entities,
            Text=text,
            LanguageCode=language_code,
        )

        return [
            {
                'type': entity['Type'],
                'text': entity['Text'],
                'score': entity['Score'],
                'begin_offset': entity['BeginOffset'],
                'end_offset': entity['EndOffset'],
            }
            for entity in response['Entities']
        ]

    async def detect_dominant_language(self, text: str) -> str:
        """
        Detect the dominant language of text.

        Returns:
            Language code (e.g., 'en', 'es', 'pt')
        """
        response = await self._run_sync(self._client.detect_dominant_language, Text=text[:5000])
        languages = response['Languages']
        if languages:
            return languages[0]['LanguageCode']
        return 'en'  # Default to English
