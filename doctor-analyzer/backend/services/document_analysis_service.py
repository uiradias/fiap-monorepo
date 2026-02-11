"""Service for document (PDF) analysis."""

import logging
import uuid

from infrastructure.aws.textract_client import TextractClient
from infrastructure.aws.comprehend_client import ComprehendClient
from infrastructure.aws.s3_client import S3Client
from infrastructure.websocket.connection_manager import ConnectionManager
from domain.session import AnalysisSession, SessionStore
from domain.analysis import DocumentAnalysis, AnalysisStatus

logger = logging.getLogger(__name__)


class DocumentAnalysisService:
    """Orchestrates PDF text extraction and analysis."""

    def __init__(
        self,
        textract: TextractClient,
        comprehend: ComprehendClient,
        s3: S3Client,
        ws_manager: ConnectionManager,
        session_store: SessionStore,
    ):
        self._textract = textract
        self._comprehend = comprehend
        self._s3 = s3
        self._ws_manager = ws_manager
        self._sessions = session_store

    async def analyze_documents(
        self,
        session: AnalysisSession,
    ) -> list:
        """
        Analyze all PDF documents in a session.

        This method:
        1. Extracts text from each PDF using Textract
        2. Analyzes sentiment and key phrases using Comprehend
        3. Streams results to WebSocket clients
        """
        if not session.documents_s3_keys:
            return []

        await self._ws_manager.send_status_update(
            session.session_id,
            AnalysisStatus.PROCESSING_DOCUMENTS.value,
            progress=0.0,
            message=f"Extracting and analyzing document 1 of {len(session.documents_s3_keys)}...",
        )

        # Update session status
        session.update_status(AnalysisStatus.PROCESSING_DOCUMENTS)
        await self._sessions.update(session)

        analyses = []
        total_docs = len(session.documents_s3_keys)

        for i, s3_key in enumerate(session.documents_s3_keys):
            logger.info(f"Processing document {i + 1}/{total_docs}: {s3_key}")

            # Extract text using Textract
            try:
                extracted_text = await self._textract.extract_text_from_s3(
                    self._s3.bucket_name,
                    s3_key,
                )
            except Exception as e:
                logger.error(f"Failed to extract text from {s3_key}: {e}")
                continue

            # Get filename from S3 key
            filename = s3_key.split('/')[-1]
            doc_id = str(uuid.uuid4())

            # Create document analysis
            doc_analysis = DocumentAnalysis(
                document_id=doc_id,
                filename=filename,
                extracted_text=extracted_text,
            )

            # Analyze sentiment and key phrases if we have text
            if extracted_text:
                # Detect language first
                language = await self._comprehend.detect_dominant_language(extracted_text)

                # Sentiment analysis
                sentiment = await self._comprehend.detect_sentiment(
                    extracted_text,
                    language_code=language,
                )
                doc_analysis.sentiment = sentiment

                # Key phrases
                key_phrases = await self._comprehend.detect_key_phrases(
                    extracted_text,
                    language_code=language,
                )
                doc_analysis.key_phrases = key_phrases[:20]  # Top 20

                # Entities
                entities = await self._comprehend.detect_entities(
                    extracted_text,
                    language_code=language,
                )
                doc_analysis.entities = entities

                # Send sentiment update
                await self._ws_manager.send_sentiment_update(
                    session.session_id,
                    sentiment.to_dict(),
                    "document",
                )

            analyses.append(doc_analysis)

            # Update progress
            progress = (i + 1) / total_docs
            await self._ws_manager.send_status_update(
                session.session_id,
                AnalysisStatus.PROCESSING_DOCUMENTS.value,
                progress=progress,
                message=f"Extracting and analyzing document {i + 2} of {total_docs}..."
                    if i + 1 < total_docs
                    else f"Document analysis complete — {total_docs} document{'s' if total_docs != 1 else ''} processed",
            )

        # Save results to S3
        results_key = f"sessions/{session.session_id}/results/document_analyses.json"
        await self._s3.upload_json(
            [a.to_dict() for a in analyses],
            results_key,
        )

        # Update session
        session.document_analyses = analyses
        await self._sessions.update(session)

        logger.info(f"Completed document analysis for session {session.session_id}: {len(analyses)} documents")
        return analyses

    async def analyze_text_input(
        self,
        session: AnalysisSession,
    ) -> dict:
        """
        Analyze the text input provided by the doctor.

        Returns:
            Dictionary with sentiment and key findings
        """
        if not session.text_input:
            return None

        text = session.text_input

        # Detect language
        language = await self._comprehend.detect_dominant_language(text)

        # Sentiment analysis
        sentiment = await self._comprehend.detect_sentiment(text, language_code=language)

        # Key phrases
        key_phrases = await self._comprehend.detect_key_phrases(text, language_code=language)

        # Entities (medical terms, etc.)
        entities = await self._comprehend.detect_entities(text, language_code=language)

        result = {
            "sentiment": sentiment.to_dict(),
            "key_phrases": key_phrases[:15],
            "entities": entities,
        }

        # Update session
        session.text_sentiment = result
        await self._sessions.update(session)

        # Send to WebSocket
        await self._ws_manager.send_sentiment_update(
            session.session_id,
            sentiment.to_dict(),
            "text",
        )

        return result
