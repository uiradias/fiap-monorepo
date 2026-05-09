import type { TokenPair } from "../api/types";

const ACCESS_KEY = "fss.accessToken";
const REFRESH_KEY = "fss.refreshToken";

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens(pair: TokenPair): void {
  localStorage.setItem(ACCESS_KEY, pair.accessToken);
  localStorage.setItem(REFRESH_KEY, pair.refreshToken);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

/** True if both tokens exist. Does NOT verify the JWT — that's the gateway's job. */
export function isAuthenticated(): boolean {
  return getAccessToken() !== null && getRefreshToken() !== null;
}
