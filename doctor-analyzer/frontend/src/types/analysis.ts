/**
 * Analysis type definitions matching backend domain models.
 */

export type AnalysisStatus =
  | 'pending'
  | 'uploading'
  | 'processing_video'
  | 'processing_injury_check'
  | 'processing_audio'
  | 'processing_bedrock'
  | 'aggregating'
  | 'completed'
  | 'failed';

export type EmotionType =
  | 'discomfort'
  | 'depression'
  | 'anxiety'
  | 'fear'
  | 'calm'
  | 'happy'
  | 'confused'
  | 'angry'
  | 'surprised'
  | 'disgusted'
  | 'sad'
  | 'neutral';

export interface EmotionScore {
  emotion: EmotionType;
  confidence: number;
}

export interface BoundingBox {
  left: number;
  top: number;
  width: number;
  height: number;
}

export interface FaceDetection {
  timestamp_ms: number;
  bounding_box: BoundingBox;
  emotions: EmotionScore[];
  primary_emotion: EmotionScore | null;
  age_range: { low: number; high: number } | null;
  gender: string | null;
}

export interface VideoEmotionTimeline {
  video_id: string;
  duration_ms: number;
  detection_count: number;
  emotion_summary: Record<string, number>;
}

export interface SentimentResult {
  sentiment: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL' | 'MIXED';
  positive_score: number;
  negative_score: number;
  neutral_score: number;
  mixed_score: number;
}

export interface TranscriptionSegment {
  text: string;
  start_time: number;
  end_time: number;
  confidence: number;
  speaker_label: string | null;
}

export interface AudioAnalysis {
  full_transcript: string;
  segment_count: number;
  overall_sentiment: SentimentResult | null;
}

export interface ClinicalIndicator {
  indicator_type: string;
  confidence: number;
  evidence: string[];
  timestamp_ranges: Array<{ start: number; end: number }>;
}

export interface ModerationLabelItem {
  name: string;
  confidence: number;
  timestamp_ms?: number;
  parent_name?: string;
}

export type InjurySeverity = 'low' | 'moderate' | 'high' | 'critical';

export interface TranscriptInjuryAnalysis {
  has_verbal_signals: boolean;
  severity: string;
  findings: string[];
  evidence_quotes: string[];
  confidence: number;
  risk_factors_identified?: string[];
}

export interface InjuryCheckResult {
  enabled: boolean;
  rekognition_labels: ModerationLabelItem[];
  bedrock_has_signals: boolean;
  bedrock_summary: string;
  bedrock_confidence: number;
  bedrock_severity?: InjurySeverity;
  bedrock_clinical_rationale?: string;
  bedrock_transcript_analysis?: TranscriptInjuryAnalysis;
  error_message?: string;
}

export interface BedrockAggregation {
  clinical_summary: string;
  risk_level: InjurySeverity;
  cross_referenced_evidence: Array<{
    source: string;
    finding: string;
    supporting_sources: string[];
  }>;
  concordant_signals: string[];
  discordant_signals: string[];
  recommendations: string[];
}

export interface Patient {
  id: string;
  codename: string;
  created_at: string;
}

export interface AnalysisSession {
  session_id: string;
  patient_id: string;
  created_at: string;
  updated_at: string | null;
  status: AnalysisStatus;
  video_s3_key: string | null;
  emotion_summary: Record<string, number>;
  clinical_indicators: ClinicalIndicator[];
  error_message: string | null;
  injury_check?: InjuryCheckResult | null;
  bedrock_aggregation?: BedrockAggregation | null;
}

export interface AnalysisSessionFull extends AnalysisSession {
  video_emotions: VideoEmotionTimeline | null;
  audio_analysis: AudioAnalysis | null;
  results_s3_key: string | null;
  injury_check: InjuryCheckResult | null;
  bedrock_aggregation: BedrockAggregation | null;
}

// WebSocket message types
export interface EmotionUpdateMessage {
  type: 'emotion_update';
  timestamp_ms: number;
  emotions: EmotionScore[];
  bounding_box: BoundingBox;
}

export interface StatusUpdateMessage {
  type: 'status_update';
  status: AnalysisStatus;
  progress?: number;
  message?: string;
}

export interface TranscriptionUpdateMessage {
  type: 'transcription_update';
  text: string;
  start_time: number;
  end_time: number;
}

export interface CompleteMessage {
  type: 'complete';
  results: AnalysisSessionFull;
}

export interface ErrorMessage {
  type: 'error';
  message: string;
}

export type WebSocketMessage =
  | EmotionUpdateMessage
  | StatusUpdateMessage
  | TranscriptionUpdateMessage
  | CompleteMessage
  | ErrorMessage;

// Upload response types
export interface UploadVideoResponse {
  session_id: string;
  video_s3_key: string;
  status: AnalysisStatus;
}

