// WebSocket client for session live events.
//
// Frame types:
//   session.snapshot — sent once on connection open; contains `events: Array<SessionEventData>`
//   session.event    — sent live on each state transition
//
// Reconnect policy:
//   Reconnects after 1 s on unexpected close UNLESS:
//   - cancel() was called (stopped flag)
//   - code === 1000 (normal close)
//   - code 4400-4499 (gateway-issued auth/ownership/missing — terminal)

import type { SessionState } from "../api/types";

export interface SessionEventData {
  type: "session.event";
  eventId: string;
  sessionId: string;
  fromState: SessionState | null;
  toState: SessionState;
  payload: Record<string, unknown> | null;
  occurredAt: string;
}

export interface SessionSnapshotFrame {
  type: "session.snapshot";
  events: Array<Omit<SessionEventData, "type">>;
}

export type SessionFrame = SessionSnapshotFrame | SessionEventData;

export interface SubscribeOpts {
  sessionId: string;
  token: string;
  onFrame: (frame: SessionFrame) => void;
  onError?: (err: Event) => void;
}

const WS_BASE =
  (import.meta.env.VITE_GATEWAY_WS_URL as string) || "ws://localhost:8080";

/**
 * Opens a WebSocket to `/ws/sessions/{id}?token={access}` and delivers
 * frames via `opts.onFrame`.  Returns a `cancel()` function that closes
 * the socket cleanly (code 1000) and prevents any further reconnects.
 */
export function subscribeSessionEvents(opts: SubscribeOpts): () => void {
  let stopped = false;
  let socket: WebSocket | null = null;

  function connect() {
    if (stopped) return;

    const url = `${WS_BASE}/ws/sessions/${encodeURIComponent(opts.sessionId)}?token=${encodeURIComponent(opts.token)}`;
    socket = new WebSocket(url);

    socket.onmessage = (ev: MessageEvent) => {
      try {
        const raw = JSON.parse(ev.data as string) as SessionFrame;
        opts.onFrame(raw);
      } catch {
        // Ignore malformed frames — server invariant; not worth crashing over.
      }
    };

    socket.onerror = (ev: Event) => {
      opts.onError?.(ev);
    };

    socket.onclose = (ev: CloseEvent) => {
      const { code } = ev;
      const isTerminal =
        stopped || code === 1000 || (code >= 4400 && code < 4500);
      if (!isTerminal) {
        setTimeout(connect, 1000);
      }
    };
  }

  connect();

  return function cancel() {
    stopped = true;
    socket?.close(1000, "component unmounted");
  };
}
