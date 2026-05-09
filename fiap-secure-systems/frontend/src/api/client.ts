import type {
  AssetSummary,
  BundleSummary,
  FinalizeResponse,
  ProblemDetail,
  RegisterResponse,
  ReportResponse,
  SessionResponse,
  TokenPair,
} from "./types";
import { ApiError } from "./types";

const BASE = (import.meta.env.VITE_GATEWAY_BASE_URL as string) || "http://localhost:8080";

// Token storage hooks — implemented in src/auth/tokens.ts (Task 4).
// Late-bound via setter so the client module doesn't depend on the auth module
// at import time (avoids a tight cycle and keeps testing trivial).
type TokenStore = {
  getAccess(): string | null;
  getRefresh(): string | null;
  set(pair: TokenPair): void;
  clear(): void;
};

let tokenStore: TokenStore = {
  getAccess: () => null,
  getRefresh: () => null,
  set: () => {},
  clear: () => {},
};

export function configureTokenStore(store: TokenStore): void {
  tokenStore = store;
}

async function request<T>(method: string, path: string, body?: unknown,
                          isMultipart = false, retried = false): Promise<T> {
  const headers: Record<string, string> = {};
  const access = tokenStore.getAccess();
  if (access) headers["Authorization"] = `Bearer ${access}`;

  let payload: BodyInit | undefined;
  if (body instanceof FormData) {
    payload = body;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const res = await fetch(`${BASE}${path}`, { method, headers, body: payload });

  if (res.status === 401 && !retried && tokenStore.getRefresh()) {
    const ok = await tryRefresh();
    if (ok) return request<T>(method, path, body, isMultipart, true);
    tokenStore.clear();
    throw new ApiError(401, await asProblem(res));
  }

  if (!res.ok) throw new ApiError(res.status, await asProblem(res));

  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

async function asProblem(res: Response): Promise<ProblemDetail> {
  try {
    return (await res.json()) as ProblemDetail;
  } catch {
    return { status: res.status, title: res.statusText };
  }
}

async function tryRefresh(): Promise<boolean> {
  const refreshToken = tokenStore.getRefresh();
  if (!refreshToken) return false;
  try {
    const res = await fetch(`${BASE}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refreshToken }),
    });
    if (!res.ok) return false;
    const pair = (await res.json()) as TokenPair;
    tokenStore.set(pair);
    return true;
  } catch {
    return false;
  }
}

// --- Public surface ---

export const apiClient = {
  register: (email: string, password: string, displayName?: string) =>
    request<RegisterResponse>("POST", "/api/v1/auth/register",
      { email, password, displayName }),

  login: (email: string, password: string) =>
    request<TokenPair>("POST", "/api/v1/auth/login", { email, password }),

  logout: (refreshToken: string) =>
    request<void>("POST", "/api/v1/auth/logout", { refreshToken }),

  createBundle: () =>
    request<BundleSummary>("POST", "/api/v1/asset-bundles"),

  uploadAsset: (bundleId: string, file: File) => {
    const fd = new FormData();
    fd.append("file", file, file.name);
    return request<AssetSummary>("POST",
      `/api/v1/asset-bundles/${bundleId}/assets`, fd, true);
  },

  finalizeBundle: (bundleId: string) =>
    request<FinalizeResponse>("POST", `/api/v1/asset-bundles/${bundleId}/finalize`),

  getBundle: (bundleId: string) =>
    request<BundleSummary>("GET", `/api/v1/asset-bundles/${bundleId}`),

  getSession: (sessionId: string) =>
    request<SessionResponse>("GET", `/api/v1/sessions/${sessionId}`),

  getReport: (sessionId: string) =>
    request<ReportResponse>("GET", `/api/v1/sessions/${sessionId}/report`),

  cancelSession: (sessionId: string) =>
    request<void>("POST", `/api/v1/sessions/${sessionId}/cancel`),
};
