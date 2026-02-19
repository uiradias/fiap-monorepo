"""Service for optional injury check using Rekognition content moderation only (no Bedrock)."""

import logging
from typing import List, Dict, Any, Tuple

from domain.session import AnalysisSession
from domain.analysis import InjuryCheckResult, AnalysisStatus
from infrastructure.aws.rekognition_client import RekognitionClient
from infrastructure.aws.s3_client import S3Client
from infrastructure.websocket.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

# Rekognition labels that may indicate injury or related concern (case-insensitive match)
INJURY_RELATED_KEYWORDS = (
    "self-harm",
    "self harm",
    "violence",
    "graphic violence",
    "visually disturbing",
    "physical abuse",
    "abuse",
    "wounds",
    "blood",
    "fighting",
    "assault",
)
CONFIDENCE_THRESHOLD = 0.5  # minimum confidence to consider a label as a signal


def _interpret_labels(labels: List[Dict[str, Any]]) -> Tuple[bool, str, float]:
    """
    Derive has_signals, summary, and confidence from Rekognition moderation labels only.

    Returns:
        (has_signals, summary, confidence)
    """
    if not labels:
        return False, "No concerning content detected.", 0.0

    relevant = []
    for lb in labels:
        name = (lb.get("name") or "").lower()
        confidence = lb.get("confidence", 0)
        if confidence < CONFIDENCE_THRESHOLD:
            continue
        if any(kw in name for kw in INJURY_RELATED_KEYWORDS):
            relevant.append((lb.get("name", ""), confidence))

    if not relevant:
        return False, "No injury or violence-related content detected.", 0.0

    has_signals = True
    max_conf = max(c for _, c in relevant)
    names = [n for n, _ in relevant]
    summary = "Rekognition detected: " + ", ".join(names) + "."
    return has_signals, summary, max_conf


class InjuryCheckService:
    """Runs Rekognition content moderation on video and interprets labels for injury signals."""

    def __init__(
        self,
        rekognition: RekognitionClient,
        s3: S3Client,
        ws_manager: ConnectionManager,
    ):
        self._rekognition = rekognition
        self._s3 = s3
        self._ws_manager = ws_manager

    async def run_injury_check(
        self,
        session: AnalysisSession,
    ) -> InjuryCheckResult:
        """
        Run content moderation on the session video; interpret labels for injury (Rekognition only).

        On failure, returns a result with enabled=True and error_message set.
        """
        if not session.video_s3_key:
            return InjuryCheckResult(
                enabled=True,
                rekognition_labels=[],
                has_signals=False,
                summary="",
                confidence=0.0,
                error_message="Session has no video.",
            )

        await self._ws_manager.send_status_update(
            session.session_id,
            AnalysisStatus.PROCESSING_INJURY_CHECK.value,
            progress=0.0,
            message="Running injury check (content moderation)...",
        )

        labels: List[Dict[str, Any]] = []
        try:
            job_id = await self._rekognition.start_content_moderation(
                self._s3.bucket_name,
                session.video_s3_key,
            )
            async for label in self._rekognition.get_content_moderation_results(job_id):
                labels.append(label)
        except Exception as e:
            logger.exception("Rekognition content moderation failed: %s", e)
            return InjuryCheckResult(
                enabled=True,
                rekognition_labels=[],
                has_signals=False,
                summary="",
                confidence=0.0,
                error_message=f"Content moderation failed: {str(e)}",
            )

        await self._ws_manager.send_status_update(
            session.session_id,
            AnalysisStatus.PROCESSING_INJURY_CHECK.value,
            progress=0.0,
            message="Interpreting content moderation results...",
        )

        has_signals, summary, confidence = _interpret_labels(labels)
        return InjuryCheckResult(
            enabled=True,
            rekognition_labels=labels,
            has_signals=has_signals,
            summary=summary,
            confidence=confidence,
        )
