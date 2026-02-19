"""Prompt templates for Bedrock-enhanced self-injury analysis."""

import json
from typing import Any, Dict, List


def build_label_interpretation_prompt(
    rekognition_labels: List[Dict[str, Any]],
    transcript_context: str,
) -> str:
    """Build prompt for contextual interpretation of Rekognition moderation labels.

    Use Case 1: Takes raw Rekognition content moderation labels and the
    transcript text around the flagged timestamps, and asks the model to
    assess genuine self-injury risk vs. false positives.
    """
    labels_json = json.dumps(rekognition_labels, indent=2)

    return f"""\
You are a clinical psychology analysis assistant reviewing content moderation \
results from a patient therapy session video. Your task is to interpret visual \
content moderation labels in their clinical context.

## Content Moderation Labels (from video analysis)
{labels_json}

## Transcript Context (spoken words around flagged timestamps)
{transcript_context if transcript_context else "No transcript available for the flagged timestamps."}

## Instructions
1. For each flagged label, assess whether it represents genuine self-injury \
risk or is a false positive (e.g., discussion of past events, educational \
content, physical therapy movements, metaphorical language).
2. Assign an overall severity: low, moderate, high, or critical.
3. Provide clinical rationale for your assessment.
4. Consider that therapy sessions often discuss difficult topics without \
indicating active risk.
5. Be precise and cite specific evidence. Never overstate findings.

## Response Format (strict JSON, no other text)
{{
  "has_signals": true or false,
  "severity": "low" | "moderate" | "high" | "critical",
  "summary": "Brief one-sentence summary of findings",
  "confidence": 0.0 to 1.0,
  "clinical_rationale": "Detailed rationale for the assessment",
  "label_assessments": [
    {{"label": "label name", "is_relevant": true or false, "reasoning": "why"}}
  ]
}}"""


def build_transcript_analysis_prompt(full_transcript: str) -> str:
    """Build prompt for scanning transcript for verbal self-injury indicators.

    Use Case 2: Analyzes the full session transcript for linguistic patterns
    associated with self-injury risk, suicidal ideation, or severe distress.
    """
    # Truncate to avoid exceeding token limits
    truncated = full_transcript[:8000] if len(full_transcript) > 8000 else full_transcript

    return f"""\
You are a clinical psychology analysis assistant. Analyze the following \
therapy session transcript for verbal indicators of self-injury risk, \
suicidal ideation, or severe psychological distress.

## Full Transcript
{truncated}

## Look for these categories of verbal indicators:
1. **Direct mentions**: self-harm, suicide, death wishes, wanting to disappear, \
references to specific methods
2. **Absolutist language**: "always", "never", "nothing matters", "everyone \
hates me", "I can't do anything right"
3. **Hopelessness markers**: "no point", "won't get better", "trapped", \
"nothing will change"
4. **Burden statements**: "better off without me", "I'm a burden", "nobody \
would miss me"
5. **Farewell/planning language**: giving away possessions, saying goodbye, \
settling affairs
6. **Cognitive distortions**: catastrophizing, overgeneralizing, emotional \
reasoning indicating severe depression

## Important guidelines
- Only flag genuine indicators, not therapeutic discussion about coping strategies
- Quote exact phrases from the transcript as evidence
- Consider context: a patient learning about warning signs is different from \
expressing them
- Be precise. Do not overstate or understate findings.

## Response Format (strict JSON, no other text)
{{
  "has_verbal_signals": true or false,
  "severity": "low" | "moderate" | "high" | "critical",
  "findings": ["Finding 1", "Finding 2"],
  "evidence_quotes": ["exact quote from transcript"],
  "confidence": 0.0 to 1.0,
  "risk_factors_identified": ["factor1", "factor2"]
}}"""
