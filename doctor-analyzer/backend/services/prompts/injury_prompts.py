"""Prompt templates for Bedrock-enhanced injury analysis."""

import json
from typing import Any, Dict, List


def build_label_interpretation_prompt(
    rekognition_labels: List[Dict[str, Any]],
    transcript_context: str,
) -> str:
    """Build prompt for contextual interpretation of Rekognition moderation labels.

    Use Case 1: Takes raw Rekognition content moderation labels and the
    transcript text around the flagged timestamps, and asks the model to
    assess genuine injury risk vs. false positives.
    """
    labels_json = json.dumps(rekognition_labels, indent=2)

    return f"""\
You are a clinical psychology analysis assistant reviewing content moderation \
results from a patient therapy session video. Your task is to interpret visual \
content moderation labels in their clinical context, assessing injury risk \
(self-inflicted, inflicted by others, or accidental).

## Content Moderation Labels (from video analysis)
{labels_json}

## Transcript Context (spoken words around flagged timestamps)
{transcript_context if transcript_context else "No transcript available for the flagged timestamps."}

## Instructions
1. For each flagged label, assess whether it represents genuine injury \
risk or is a false positive (e.g., discussion of past events, educational \
content, physical therapy movements, metaphorical language).
2. Distinguish between: self-harm, domestic violence/abuse, accidental \
injury, and benign content.
3. Assign an overall severity: low, moderate, high, or critical.
4. Provide clinical rationale for your assessment.
5. Consider that therapy sessions often discuss difficult topics without \
indicating active risk.
6. Be precise and cite specific evidence. Never overstate findings.

## Response Format (strict JSON, no other text)
{{
  "has_signals": true or false,
  "severity": "low" | "moderate" | "high" | "critical",
  "summary": "Brief one-sentence summary of findings",
  "confidence": 0.0 to 1.0,
  "clinical_rationale": "Detailed rationale for the assessment",
  "injury_type": "self_harm" | "domestic_violence" | "abuse" | "accidental" | "unknown" | "none",
  "label_assessments": [
    {{"label": "label name", "is_relevant": true or false, "reasoning": "why"}}
  ]
}}"""


def build_transcript_analysis_prompt(full_transcript: str) -> str:
    """Build prompt for scanning transcript for verbal injury indicators.

    Use Case 2: Analyzes the full session transcript for linguistic patterns
    associated with injury risk — including self-harm, domestic violence,
    abuse, physical neglect, and accidental injury.
    """
    # Truncate to avoid exceeding token limits
    truncated = full_transcript[:8000] if len(full_transcript) > 8000 else full_transcript

    return f"""\
You are a clinical psychology analysis assistant. Analyze the following \
therapy session transcript for verbal indicators of injury risk, including \
self-harm, domestic violence, abuse, physical neglect, and accidental injury.

## Full Transcript
{truncated}

## Look for these categories of verbal indicators:

### Self-harm / suicidal ideation
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

### Abuse / violence by others
6. **Direct reports of being hurt**: "he/she hit me", "I was pushed", \
"they grabbed me", mentions of being struck, slapped, kicked
7. **Fear of someone**: "I'm scared of...", "when he/she gets angry", \
"I have to be careful around..."
8. **Controlling behavior descriptions**: isolation from friends/family, \
monitoring movements, financial control, threats

### Domestic violence markers
9. **Minimization of harm**: "it wasn't that bad", "I probably deserved it", \
"it only happened once"
10. **Cycle descriptions**: tension building, explosive episodes, \
reconciliation/honeymoon phases

### Physical neglect / harm
11. **Untreated injuries**: descriptions of wounds not receiving care, \
withholding medical treatment
12. **Basic needs unmet**: lack of food, shelter, hygiene due to another's actions

### Accidental injury context
13. **Injury descriptions**: falls, workplace accidents, sports injuries, \
car accidents
14. **Cognitive distortions**: catastrophizing, overgeneralizing, emotional \
reasoning indicating severe distress related to injuries

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
  "risk_factors_identified": ["factor1", "factor2"],
  "injury_types_detected": ["self_harm", "domestic_violence", "abuse", "accidental", "neglect"]
}}"""
