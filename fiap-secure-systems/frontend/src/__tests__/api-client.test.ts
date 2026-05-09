import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiClient, configureTokenStore } from "../api/client";
import type { TokenPair } from "../api/types";
import { ApiError } from "../api/types";

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("apiClient", () => {
  let access: string | null;
  let refresh: string | null;
  let setCalls: TokenPair[] = [];
  let _clearCalls = 0;

  beforeEach(() => {
    access = "tok-1";
    refresh = "ref-1";
    setCalls = [];
    _clearCalls = 0;
    configureTokenStore({
      getAccess: () => access,
      getRefresh: () => refresh,
      set: (p) => { setCalls.push(p); access = p.accessToken; refresh = p.refreshToken; },
      clear: () => { _clearCalls++; access = null; refresh = null; },
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("attaches Authorization: Bearer to authenticated requests", async () => {
    const spy = vi.spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(200, { id: "x", state: "REPORT_READY", lastEventAt: "now", failureReason: null, reportId: null }));

    await apiClient.getSession("sid");

    const init = spy.mock.calls[0]?.[1] as RequestInit;
    const headers = init.headers as Record<string, string>;
    expect(headers["Authorization"]).toBe("Bearer tok-1");
  });

  it("on 401, refreshes once and replays the request", async () => {
    const spy = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(401, { code: "INVALID_TOKEN" }))
      .mockResolvedValueOnce(jsonResponse(200, {
        accessToken: "tok-2", refreshToken: "ref-2", expiresIn: 900,
      } satisfies TokenPair))
      .mockResolvedValueOnce(jsonResponse(200, {
        id: "x", state: "ANALYZING", lastEventAt: "now", failureReason: null, reportId: null,
      }));

    const session = await apiClient.getSession("sid");

    expect(spy).toHaveBeenCalledTimes(3);
    expect(setCalls).toHaveLength(1);
    expect(setCalls[0].accessToken).toBe("tok-2");
    expect(session.state).toBe("ANALYZING");
  });

  it("on 401 with no refresh token, throws ApiError(401) and clears tokens", async () => {
    refresh = null;
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResponse(401, { code: "INVALID_TOKEN" }));

    await expect(apiClient.getSession("sid")).rejects.toBeInstanceOf(ApiError);
  });

  it("uploadAsset sends multipart body without forcing JSON content-type", async () => {
    const spy = vi.spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(201, {
        id: "a", filename: "f.png", contentType: "image/png", sizeBytes: 1,
        s3Key: "k", checksumSha256: "c", uploadedAt: "now",
      }));

    const file = new File([new Uint8Array([0])], "f.png", { type: "image/png" });
    await apiClient.uploadAsset("bid", file);

    const init = spy.mock.calls[0]?.[1] as RequestInit;
    const headers = init.headers as Record<string, string>;
    expect(headers["Content-Type"]).toBeUndefined();
    expect(init.body).toBeInstanceOf(FormData);
  });
});
