import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { apiClient, configureTokenStore } from "../api/client";
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  isAuthenticated,
  setTokens,
} from "./tokens";

interface AuthState {
  authed: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthCtx = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authed, setAuthed] = useState<boolean>(isAuthenticated());

  // Wire apiClient to tokens synchronously on first render so the very first fetch
  // after navigation (e.g. drag-drop on /upload) already sends Authorization.
  const storeConfigured = useRef(false);
  if (!storeConfigured.current) {
    storeConfigured.current = true;
    configureTokenStore({
      getAccess: getAccessToken,
      getRefresh: getRefreshToken,
      set: (pair) => {
        setTokens(pair);
        setAuthed(true);
      },
      clear: () => {
        clearTokens();
        setAuthed(false);
      },
    });
  }

  const login = useCallback(async (email: string, password: string) => {
    const pair = await apiClient.login(email, password);
    setTokens(pair);
    setAuthed(true);
  }, []);

  const register = useCallback(async (email: string, password: string, displayName?: string) => {
    await apiClient.register(email, password, displayName);
    // Auto-login right after registration to land the user in /upload.
    const pair = await apiClient.login(email, password);
    setTokens(pair);
    setAuthed(true);
  }, []);

  const logout = useCallback(async () => {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      try { await apiClient.logout(refreshToken); }
      catch { /* swallow — clear local state anyway */ }
    }
    clearTokens();
    setAuthed(false);
  }, []);

  const value = useMemo(() => ({ authed, login, register, logout }), [authed, login, register, logout]);
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthCtx);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
