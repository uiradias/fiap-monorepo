import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, render, screen } from "@testing-library/react";
import { AuthProvider, useAuth } from "../auth/AuthContext";

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function Probe() {
  const { authed, login, logout } = useAuth();
  return (
    <div>
      <span data-testid="state">{authed ? "in" : "out"}</span>
      <button onClick={() => login("a@b.com", "hunter22").catch(() => {})}>login</button>
      <button onClick={() => logout()}>logout</button>
    </div>
  );
}

describe("AuthContext", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("starts unauthenticated when no tokens are present", () => {
    render(<AuthProvider><Probe /></AuthProvider>);
    expect(screen.getByTestId("state")).toHaveTextContent("out");
  });

  it("stores tokens and flips to authenticated on login()", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResponse(200, {
      accessToken: "a", refreshToken: "r", expiresIn: 900,
    }));

    render(<AuthProvider><Probe /></AuthProvider>);
    await act(async () => {
      screen.getByText("login").click();
    });
    expect(localStorage.getItem("fss.accessToken")).toBe("a");
    expect(screen.getByTestId("state")).toHaveTextContent("in");
  });

  it("clears storage and flips back to unauthenticated on logout()", async () => {
    localStorage.setItem("fss.accessToken", "x");
    localStorage.setItem("fss.refreshToken", "y");
    // logout() also calls /auth/logout — mock to 204.
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(null, { status: 204 }));

    render(<AuthProvider><Probe /></AuthProvider>);
    expect(screen.getByTestId("state")).toHaveTextContent("in");
    await act(async () => {
      screen.getByText("logout").click();
    });
    expect(localStorage.getItem("fss.accessToken")).toBeNull();
    expect(screen.getByTestId("state")).toHaveTextContent("out");
  });
});
