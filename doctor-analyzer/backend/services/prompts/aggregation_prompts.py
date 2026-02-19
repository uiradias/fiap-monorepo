"""Prompt templates for Bedrock multi-modal aggregation."""

import json
from typing import Any, Dict, List, Optional


def build_multimodal_aggregation_prompt(
    emotion_summary: Dict[str, float],
    transcript_text: str,
    sentiment_result: Optional[Dict[str, Any]],
    self_injury_result: Optional[Dict[str, Any]],
    clinical_indicators: List[Dict[str, Any]],
) -> str:
    """Build prompt for multi-modal aggregation of all analysis signals.

    Use Case 3: Combines emotion data, transcript, sentiment, and self-injury
    results into a unified clinical summary with cross-referenced evidence.
    """
    # Truncate transcript to fit token limits
    truncated_transcript = transcript_text[:4000] if len(transcript_text) > 4000 else transcript_text

    emotion_json = json.dumps(emotion_summary, indent=2)
    sentiment_json = json.dumps(sentiment_result, indent=2) if sentiment_result else "Not available"
    self_injury_json = json.dumps(self_injury_result, indent=2) if self_injury_result else "Not performed"
    indicators_json = json.dumps(clinical_indicators, indent=2) if clinical_indicators else "[]"

    return f"""\
You are a clinical psychology analysis assistant. Synthesize all available \
analysis signals from a patient therapy session into a unified clinical summary.

## Visual Analysis (Emotion Summary)
Average emotion scores detected in the patient's face throughout the session:
{emotion_json}

## Audio Analysis
Transcript excerpt:
{truncated_transcript}

Overall sentiment analysis:
{sentiment_json}

## Self-Injury Check Results
{self_injury_json}

## Existing Clinical Indicators (Rule-Based)
{indicators_json}

## Instructions
Cross-reference all available signals. Specifically:
1. Identify **concordant signals** — when multiple sources agree (e.g., sad \
facial expression + negative verbal content + distress topic in transcript).
2. Identify **discordant signals** — when sources conflict (e.g., calm facial \
expression + distressing verbal content). Discordance can itself be clinically \
significant (emotional masking, dissociation).
3. Note **temporal correlations** if timestamps suggest emotional spikes \
coincide with specific topics.
4. Produce an overall risk assessment considering all evidence.
5. Provide actionable clinical recommendations.
6. Be precise and evidence-based. Do not overstate findings.

## Response Format (strict JSON, no other text)
{{
  "clinical_summary": "Comprehensive 2-4 sentence paragraph summarizing all findings",
  "risk_level": "low" | "moderate" | "high" | "critical",
  "cross_referenced_evidence": [
    {{
      "source": "video | audio | content_moderation | transcript",
      "finding": "what was observed",
      "supporting_sources": ["other sources that corroborate"]
    }}
  ],
  "concordant_signals": ["Description of agreeing signal pairs"],
  "discordant_signals": ["Description of conflicting signal pairs"],
  "recommendations": ["Clinical recommendation 1", "Clinical recommendation 2"]
}}"""
