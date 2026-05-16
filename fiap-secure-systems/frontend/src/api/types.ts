// Mirrors the gateway DTOs (spec §8.1) — kept thin and field-for-field accurate.

export interface TokenPair {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface RegisterResponse {
  userId: string;
}

export interface BundleSummary {
  bundleId: string;
  status: "INITIATED" | "UPLOADING" | "UPLOADED" | "FAILED";
  assetCount: number;
  totalBytes: number;
  createdAt: string;
  updatedAt: string;
  assets: AssetSummary[];
}

export interface AssetSummary {
  id: string;
  filename: string;
  contentType: string;
  sizeBytes: number;
  s3Key: string;
  checksumSha256: string;
  uploadedAt: string;
}

/** Short-lived HTTPS GET URL for the asset in S3 (gateway-issued). */
export interface AssetDownloadUrlResponse {
  url: string;
  expiresInSeconds: number;
}

export interface FinalizeResponse {
  sessionId: string;
  state: SessionState;
}

export type SessionState =
  | "CREATED"
  | "ASSETS_UPLOADED"
  | "QUEUED_FOR_ANALYSIS"
  | "ANALYZING"
  | "ANALYSIS_COMPLETED"
  | "REPORT_READY"
  | "FAILED"
  | "CANCELED";

export interface SessionResponse {
  id: string;
  state: SessionState;
  lastEventAt: string;
  failureReason: string | null;
  reportId: string | null;
}

/** Row from `GET /api/v1/sessions` (gateway SessionSummaryResponse). */
export interface SessionSummary {
  id: string;
  userId: string;
  state: SessionState;
  assetCount: number;
  failureReason: string | null;
  createdAt: string;
  updatedAt: string;
  reportId: string | null;
}

export interface ReportResponse {
  id: string;
  sessionId: string;
  summary: string;
  confidence: "high" | "medium" | "low";
  payload: ReportPayload;
  modelMetadata: Record<string, unknown>;
  createdAt: string;
}

export interface ReportPayload {
  summary: string;
  components: Array<{
    name: string;
    kind: string;
    responsibility: string;
    relevance: string;
    evidence: string;
  }>;
  risks: Array<{
    title: string;
    category: string;
    severity: string;
    description: string;
    affected_components: string[];
    recommendation: string;
  }>;
  improvements: Array<{
    title: string;
    rationale: string;
    impact: string;
    effort: string;
    affected_components: string[];
  }>;
  strengths: Array<{ title: string; description: string }>;
  confidence: string;
  model_metadata: Record<string, unknown>;
}

export interface ProblemDetail {
  type?: string;
  title?: string;
  status?: number;
  detail?: string;
  code?: string;
  instance?: string;
}

export class ApiError extends Error {
  constructor(public readonly status: number, public readonly problem: ProblemDetail) {
    super(problem.detail || problem.title || `HTTP ${status}`);
  }
}
