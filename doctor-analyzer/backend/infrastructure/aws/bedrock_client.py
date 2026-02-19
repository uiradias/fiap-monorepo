"""AWS Bedrock client for LLM-based analysis."""

import json
import re
import boto3
import asyncio
import logging
from functools import partial
from typing import Any, Dict, Optional

from botocore.config import Config as BotoConfig
from config.settings import AWSSettings

logger = logging.getLogger(__name__)

_RETRY_CONFIG = BotoConfig(
    retries={"max_attempts": 3, "mode": "adaptive"},
)


class BedrockClient:
    """Wrapper for AWS Bedrock Runtime model invocation."""

    def __init__(self, settings: AWSSettings):
        self._settings = settings
        self._model_id = settings.bedrock_model_id
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=settings.region,
            aws_access_key_id=settings.access_key_id,
            aws_secret_access_key=settings.secret_access_key,
            config=_RETRY_CONFIG,
        )

    async def _run_sync(self, func, *args, **kwargs):
        """Run a synchronous boto3 call in a thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))

    async def invoke_model(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.1,
    ) -> str:
        """Invoke a Bedrock model with a text prompt.

        Uses the Anthropic Messages API format for Claude models.

        Returns:
            The text content of the model response.
        """
        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
        )

        response = await self._run_sync(
            self._client.invoke_model,
            modelId=self._model_id,
            contentType="application/json",
            accept="application/json",
            body=body,
        )

        response_body = json.loads(response["body"].read())
        text = response_body["content"][0]["text"]

        usage = response_body.get("usage", {})
        if usage:
            logger.info(
                "Bedrock usage — input_tokens=%s output_tokens=%s",
                usage.get("input_tokens", "?"),
                usage.get("output_tokens", "?"),
            )

        return text

    async def invoke_model_json(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.1,
    ) -> Optional[Dict[str, Any]]:
        """Invoke model and parse the response as JSON.

        Falls back to regex extraction of the first JSON object if
        ``json.loads`` fails on the full response.

        Returns:
            Parsed dict, or ``None`` if parsing fails entirely.
        """
        text = await self.invoke_model(prompt, max_tokens, temperature)

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting JSON block from markdown fences or raw braces
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        logger.warning("Could not parse Bedrock response as JSON: %.200s", text)
        return None
