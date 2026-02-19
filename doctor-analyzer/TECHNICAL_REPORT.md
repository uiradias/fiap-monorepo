# Technical Report: Multimodal Clinical Analysis System

## 1. Overview

Doctor Analyzer is a multimodal clinical analysis system that processes therapy session videos to detect potential mental health concerns and safety risks. It combines computer vision, speech-to-text, natural language processing, and large language model reasoning to produce cross-referenced clinical assessments from a single video input.

---

## 2. Multimodal Analysis Flow

### 2.1 Pipeline Architecture

The system processes a single video input through six sequential stages, each feeding into the next:

```
                        ┌─────────────────┐
                        │  Video Upload    │
                        │  (S3 Storage)    │
                        └────────┬────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Stage 1: Video Analysis │
                    │  (Rekognition Face       │
                    │   Detection)             │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  Stage 2: Injury Check    │
                    │  (Rekognition Content     │
                    │   Moderation)             │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  Stage 3: Audio Analysis  │
                    │  (Transcribe + Comprehend)│
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  Stage 4: Bedrock         │
                    │  Enhancement              │
                    │  - Injury interpretation   │
                    │  - Transcript analysis     │
                    │  - Multimodal aggregation  │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  Stage 5: Rule-Based      │
                    │  Aggregation              │
                    │  (Clinical Indicators)    │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  Stage 6: Final Report    │
                    │  (S3 Storage)             │
                    └──────────────────────────┘
```

### 2.2 Real-Time Streaming

Each stage streams results to the frontend via WebSocket as they become available:
- **Emotion detections** are sent per-frame during video analysis
- **Transcription segments** are sent as they are parsed
- **Status updates** with progress percentage are sent at each stage transition
- **Completion message** includes the full aggregated result

### 2.3 Pipeline Status Progression

```
PENDING → UPLOADING → PROCESSING_VIDEO → PROCESSING_INJURY_CHECK
    → PROCESSING_AUDIO → PROCESSING_BEDROCK → AGGREGATING → COMPLETED
```

If any stage fails fatally, the session transitions to `FAILED` with an error message. Non-critical stages (injury check, Bedrock enhancement) degrade gracefully without blocking the pipeline.

---

## 3. Models Applied to Each Data Type

### 3.1 Video: AWS Rekognition Face Detection

**Input:** Video file stored in S3 (MP4, MOV, AVI, WebM)

**Model:** AWS Rekognition Video — asynchronous face detection with `FaceAttributes: ALL`

**What it detects per frame:**
- Face bounding box (position and size as percentages)
- 8 raw emotions with confidence scores (0.0 to 1.0)
- Age range (low/high estimate)
- Gender

**Raw emotions from Rekognition:**

| Emotion | Description |
|---------|-------------|
| HAPPY | Joy, contentment |
| SAD | Sadness, grief |
| ANGRY | Anger, frustration |
| CONFUSED | Confusion, uncertainty |
| DISGUSTED | Disgust, revulsion |
| SURPRISED | Surprise, shock |
| CALM | Calmness, composure |
| FEAR | Fear, anxiety |

**Derived clinical emotions** (calculated from raw scores):

| Derived Emotion | Formula |
|-----------------|---------|
| **Discomfort** | DISGUSTED x 0.4 + CONFUSED x 0.3 + SAD x 0.3 |
| **Anxiety** | FEAR x 0.7 + SURPRISED x 0.3 |
| **Depression** | SAD x 0.6 + (1 - HAPPY) x 0.2 + CALM x 0.2 |

The system produces an **emotion summary** by averaging each emotion's confidence score across all frames in the video.

**Parameters:**
| Parameter | Value |
|-----------|-------|
| Polling interval | 5 seconds |
| Results per page | 100 detections |
| Async notification | Optional (SNS) |

### 3.2 Video: AWS Rekognition Content Moderation

**Input:** Same video file in S3

**Model:** AWS Rekognition Video — asynchronous content moderation

**Purpose:** Detect visual signals of injury, violence, or self-harm in the video.

**Injury-related keywords matched** (case-insensitive):
```
self-harm, self harm, violence, graphic violence, visually disturbing,
physical abuse, abuse, wounds, blood, fighting, assault
```

**Confidence threshold:** 0.5 (50%) — labels below this confidence are discarded.

**Output per detection:**
- `name`: Moderation label category
- `confidence`: 0.0 to 1.0
- `timestamp_ms`: Position in video
- `parent_name`: Parent category (if hierarchical)

### 3.3 Audio: AWS Transcribe

**Input:** Audio track extracted from the uploaded video

**Model:** AWS Transcribe — asynchronous speech-to-text

**Configuration:**
| Parameter | Value |
|-----------|-------|
| Language | `en-US` |
| Speaker labels | Enabled (up to 5 speakers) |
| Segment chunking | Every 10 words or at sentence boundaries (`.` `?` `!`) |

**Output:** Timed transcription segments with speaker identification:
```json
{
  "text": "I've been feeling really down lately",
  "start_time": 12.5,
  "end_time": 15.8,
  "confidence": 0.94,
  "speaker_label": "spk_0"
}
```

### 3.4 Text: AWS Comprehend

**Input:** Transcribed text from Transcribe

**Model:** AWS Comprehend — sentiment analysis

**Two levels of analysis:**

1. **Overall sentiment** — full concatenated transcript analyzed as a single block
2. **Segment sentiment** — batch analysis of individual segments (minimum 20 characters, batches of 25)

**Text limit:** 5,000 bytes (automatically truncated to 4,500 characters if exceeded)

**Output per analysis:**
```json
{
  "sentiment": "NEGATIVE",
  "positive_score": 0.05,
  "negative_score": 0.75,
  "neutral_score": 0.15,
  "mixed_score": 0.05
}
```

### 3.5 Multi-Signal Reasoning: AWS Bedrock (Claude 3 Sonnet)

**Input:** Combined outputs from all previous stages

**Model:** Claude 3 Sonnet via AWS Bedrock (`us.anthropic.claude-3-sonnet-20240229-v1:0`, configurable)

**Parameters:**
| Parameter | Value |
|-----------|-------|
| Temperature | 0.1 (highly deterministic) |
| Max tokens | 2,048 |
| Retry strategy | Adaptive, 3 attempts max |
| Response format | JSON with regex fallback parsing |

**Three distinct invocations:**

#### 3.5.1 Injury Label Interpretation

Contextualizes Rekognition content moderation labels using the transcript.

- Extracts transcript text within a **+/- 10 second window** around each flagged timestamp
- Assesses whether each label represents genuine risk vs. false positive
- Distinguishes between: self-harm, domestic violence, accidental injury, or benign content
- Assigns severity: `low` | `moderate` | `high` | `critical`

#### 3.5.2 Transcript Verbal Indicator Analysis

Scans the full transcript (truncated to **8,000 characters**) for linguistic patterns associated with injury risk:

| Category | Example Patterns |
|----------|-----------------|
| **Self-harm / suicidal ideation** | "want to disappear", "no point", "better off without me", absolutist language ("always", "never", "nothing matters") |
| **Abuse / violence** | "he hit me", "I was pushed", "I'm scared of...", descriptions of controlling behavior |
| **Domestic violence** | Minimization ("wasn't that bad"), cycle descriptions (tension, explosion, reconciliation) |
| **Physical neglect** | Untreated injuries, basic needs unmet |
| **Accidental injury** | Falls, workplace injuries with catastrophic thinking |

#### 3.5.3 Multimodal Aggregation

Cross-references all signals (transcript truncated to **4,000 characters**) to produce:

- **Clinical summary**: 2-4 sentence overview
- **Risk level**: `low` | `moderate` | `high` | `critical`
- **Cross-referenced evidence**: Findings with corroborating sources
- **Concordant signals**: Multiple sources agreeing (e.g., sad face + negative speech + distress topic)
- **Discordant signals**: Conflicting sources (e.g., calm face + distressing speech = possible emotional masking)
- **Recommendations**: Actionable clinical suggestions

---

## 4. Rule-Based Clinical Indicator Generation

After all model outputs are collected, the aggregation service derives clinical indicators using fixed thresholds:

### 4.1 Emotion-Based Indicators

| Indicator | Threshold | Source |
|-----------|-----------|--------|
| Discomfort | >= 0.3 | Average discomfort score from emotion summary |
| Depression | >= 0.3 | Average depression score from emotion summary |
| Anxiety | >= 0.3 | Average anxiety score from emotion summary |
| Fear | >= 0.4 | Average fear score from emotion summary |

### 4.2 Sentiment-Based Indicators

| Indicator | Condition | Source |
|-----------|-----------|--------|
| Distress | `negative_score > 0.5` | Comprehend overall sentiment |
| Uncertainty | `mixed_score > 0.4` | Comprehend overall sentiment |

### 4.3 Injury-Based Indicator

If `injury_check.has_signals = true`, a `potential_injury_signals` indicator is created with the injury check's confidence score.

### 4.4 Bedrock Risk Indicator

If Bedrock aggregation returns `risk_level = "high"` or `"critical"`, a `bedrock_risk_assessment` indicator is created with confidence 0.7 (high) or 0.9 (critical).

All indicators are sorted by confidence (descending) before storage.

---

## 5. Results and Examples of Anomalies Detected

### 5.1 Example: Moderate Risk — Past Domestic Violence

A session where the patient discusses past abuse shows concordant distress signals across all modalities:

```json
{
  "emotion_summary": {
    "happy": 0.15,
    "sad": 0.45,
    "discomfort": 0.38,
    "anxiety": 0.22,
    "fear": 0.18,
    "calm": 0.30
  },
  "audio_analysis": {
    "overall_sentiment": {
      "sentiment": "NEGATIVE",
      "negative_score": 0.72,
      "positive_score": 0.08
    }
  },
  "injury_check": {
    "bedrock_has_signals": true,
    "bedrock_severity": "moderate",
    "bedrock_summary": "Patient references past domestic violence in therapeutic context",
    "bedrock_clinical_rationale": "Content moderation flagged 'violence' at 15s, coinciding with patient describing being pushed by former partner. The flag is contextually valid — patient is recounting abuse, not exhibiting active risk.",
    "bedrock_transcript_analysis": {
      "has_verbal_signals": true,
      "severity": "moderate",
      "findings": [
        "Direct report of physical violence by intimate partner",
        "Fear expressions when discussing partner's anger"
      ],
      "evidence_quotes": [
        "He used to push me around when he got angry",
        "I was always scared when he came home late"
      ],
      "risk_factors_identified": [
        "History of intimate partner violence",
        "Unresolved trauma responses"
      ]
    }
  },
  "clinical_indicators": [
    { "indicator_type": "distress", "confidence": 0.72 },
    { "indicator_type": "potential_injury_signals", "confidence": 0.65 },
    { "indicator_type": "discomfort", "confidence": 0.38 }
  ],
  "bedrock_aggregation": {
    "risk_level": "moderate",
    "clinical_summary": "Patient displays persistent sadness (45%) and discomfort (38%) while discussing history of domestic violence. Negative verbal sentiment (72%) is concordant with facial distress. No immediate suicidal ideation detected, but unresolved trauma processing is evident.",
    "concordant_signals": [
      "Sad facial expression (45%) + negative sentiment (72%) + abuse discussion = active trauma processing",
      "Content moderation flag at 15s aligns with verbal report of physical violence"
    ],
    "discordant_signals": [
      "Periodic calm baseline (30%) with sadness spikes suggests patient maintains emotional regulation despite distress"
    ],
    "recommendations": [
      "Continue trauma-informed therapy approach",
      "Develop safety plan given domestic violence history",
      "Monitor for escalating distress or re-traumatization in future sessions"
    ]
  }
}
```

### 5.2 Example: Low Risk — Routine Session

A session with no significant concerns produces minimal indicators:

```json
{
  "emotion_summary": {
    "happy": 0.55,
    "calm": 0.65,
    "sad": 0.08,
    "discomfort": 0.05,
    "anxiety": 0.04,
    "fear": 0.02
  },
  "audio_analysis": {
    "overall_sentiment": {
      "sentiment": "NEUTRAL",
      "neutral_score": 0.60,
      "positive_score": 0.30,
      "negative_score": 0.08
    }
  },
  "injury_check": {
    "bedrock_has_signals": false,
    "bedrock_severity": "low",
    "bedrock_summary": "No injury-related signals detected",
    "bedrock_confidence": 0.05
  },
  "clinical_indicators": [],
  "bedrock_aggregation": {
    "risk_level": "low",
    "clinical_summary": "Patient presents as calm and engaged. No distress signals detected across visual, verbal, or content moderation channels. Session appears to be a routine therapeutic interaction.",
    "concordant_signals": [
      "Calm facial expression (65%) + neutral sentiment (60%) + absence of concerning content = stable emotional state"
    ],
    "discordant_signals": [],
    "recommendations": [
      "Continue current therapeutic approach",
      "No immediate intervention needed"
    ]
  }
}
```

### 5.3 Example: High Risk — Suicidal Ideation Indicators

A session where verbal patterns suggest suicidal ideation triggers high-risk assessment:

```json
{
  "emotion_summary": {
    "sad": 0.52,
    "depression": 0.48,
    "happy": 0.05,
    "calm": 0.40,
    "fear": 0.15
  },
  "audio_analysis": {
    "overall_sentiment": {
      "sentiment": "NEGATIVE",
      "negative_score": 0.82,
      "positive_score": 0.03
    }
  },
  "injury_check": {
    "bedrock_has_signals": true,
    "bedrock_severity": "high",
    "bedrock_transcript_analysis": {
      "has_verbal_signals": true,
      "severity": "high",
      "findings": [
        "Hopelessness language detected: statements about future being pointless",
        "Burden statements: patient expresses belief that others would be better off",
        "Absolutist language pattern: repeated use of 'never' and 'nothing'"
      ],
      "evidence_quotes": [
        "Nothing is ever going to change",
        "They'd probably be better off without me around",
        "I can never do anything right"
      ],
      "risk_factors_identified": [
        "Hopelessness",
        "Perceived burdensomeness",
        "Absolutist cognitive patterns"
      ]
    }
  },
  "clinical_indicators": [
    { "indicator_type": "bedrock_risk_assessment", "confidence": 0.70 },
    { "indicator_type": "distress", "confidence": 0.82 },
    { "indicator_type": "depression", "confidence": 0.48 },
    { "indicator_type": "discomfort", "confidence": 0.35 },
    { "indicator_type": "potential_injury_signals", "confidence": 0.78 }
  ],
  "bedrock_aggregation": {
    "risk_level": "high",
    "clinical_summary": "Patient exhibits strong indicators of suicidal ideation through verbal patterns (hopelessness, perceived burdensomeness, absolutist language) corroborated by persistent sadness (52%) and depression-pattern facial expressions (48%). The discrepancy between calm baseline (40%) and severe verbal content may indicate emotional suppression or resignation.",
    "concordant_signals": [
      "Depression-pattern face (48%) + negative sentiment (82%) + hopelessness language = significant depressive episode",
      "Burden statements + sadness + low happiness (5%) = potential suicidal ideation risk"
    ],
    "discordant_signals": [
      "Calm baseline (40%) despite severe verbal distress suggests emotional flatness or resignation rather than active agitation — this pattern can indicate higher risk"
    ],
    "recommendations": [
      "Conduct immediate suicide risk assessment using standardized tool (e.g., C-SSRS)",
      "Develop or review safety plan with patient",
      "Consider increasing session frequency",
      "Evaluate need for psychiatric referral for medication assessment",
      "Document risk factors and protective factors"
    ]
  }
}
```

### 5.4 Example: Discordant Signals — Emotional Masking

When facial expressions and verbal content conflict, the system identifies potential emotional masking:

```json
{
  "emotion_summary": {
    "happy": 0.60,
    "calm": 0.55,
    "sad": 0.10
  },
  "audio_analysis": {
    "overall_sentiment": {
      "sentiment": "NEGATIVE",
      "negative_score": 0.65
    }
  },
  "bedrock_aggregation": {
    "risk_level": "moderate",
    "clinical_summary": "Patient displays positive facial affect (happy 60%, calm 55%) that conflicts with strongly negative verbal content (65% negative sentiment). This discordance may indicate emotional masking or social desirability bias during the session.",
    "concordant_signals": [],
    "discordant_signals": [
      "Happy facial expression (60%) contradicts negative verbal sentiment (65%) — possible emotional masking or dissociation",
      "Calm demeanor (55%) while discussing distressing topics may indicate avoidance or emotional numbing"
    ],
    "recommendations": [
      "Explore potential emotional masking patterns with patient",
      "Consider whether patient feels safe expressing genuine emotions in session",
      "Monitor for incongruence patterns across future sessions"
    ]
  }
}
```

---

## 6. Error Handling and Resilience

The pipeline is designed to degrade gracefully:

| Stage | On Failure | Impact |
|-------|-----------|--------|
| Video Analysis | Pipeline fails — video is the primary input | Fatal |
| Injury Check | Returns empty result with error message, pipeline continues | Non-blocking |
| Audio Analysis | Pipeline fails — transcription is critical for Bedrock | Fatal |
| Bedrock Injury Enhancement | Keeps original Rekognition results | Non-blocking |
| Bedrock Transcript Analysis | Skipped, no verbal indicators reported | Non-blocking |
| Bedrock Multimodal Aggregation | Skipped, only rule-based indicators generated | Non-blocking |
| Rule-Based Aggregation | Pipeline fails | Fatal |

---

## 7. Key Technical Parameters Summary

| Component | Parameter | Value |
|-----------|-----------|-------|
| Rekognition Face | FaceAttributes | ALL |
| Rekognition Face | Poll interval | 5 seconds |
| Rekognition Face | Results per page | 100 |
| Injury Check | Confidence threshold | 0.5 |
| Transcribe | Language | en-US |
| Transcribe | Max speakers | 5 |
| Transcribe | Segment size | 10 words or sentence boundary |
| Comprehend | Text limit | 5,000 bytes |
| Comprehend | Batch limit | 25 items |
| Comprehend | Min segment length | 20 characters |
| Bedrock | Temperature | 0.1 |
| Bedrock | Max tokens | 2,048 |
| Bedrock | Max retries | 3 |
| Bedrock | Transcript limit (injury) | 8,000 characters |
| Bedrock | Transcript limit (aggregation) | 4,000 characters |
| Bedrock | Time window (label context) | +/- 10 seconds |
| Clinical | Discomfort threshold | 0.3 |
| Clinical | Depression threshold | 0.3 |
| Clinical | Anxiety threshold | 0.3 |
| Clinical | Fear threshold | 0.4 |
| Clinical | Distress threshold | negative_score > 0.5 |
| Clinical | Uncertainty threshold | mixed_score > 0.4 |
