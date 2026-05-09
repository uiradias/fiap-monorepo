import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiClient } from "../api/client";
import type { ReportResponse, SessionState } from "../api/types";
import { ApiError } from "../api/types";
import { getAccessToken } from "../auth/tokens";
import {
  subscribeSessionEvents,
  type SessionEventData,
  type SessionFrame,
} from "../ws/sessionEventsClient";

const TERMINAL_STATES: SessionState[] = [
  "REPORT_READY",
  "FAILED",
  "CANCELED",
];

export default function SessionPage() {
  const { id: sessionId } = useParams<{ id: string }>();
  const [events, setEvents] = useState<SessionEventData[]>([]);
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);

  // Open WebSocket on mount, tear down on unmount.
  useEffect(() => {
    if (!sessionId) {
      setError("No session ID in URL.");
      return;
    }

    const token = getAccessToken();
    if (!token) {
      setError("Not authenticated — please log in.");
      return;
    }

    const cancel = subscribeSessionEvents({
      sessionId,
      token,
      onFrame: (frame: SessionFrame) => {
        if (frame.type === "session.snapshot") {
          // Snapshot wraps each event without a `type`; normalise to session.event.
          const normalised: SessionEventData[] = frame.events.map((e) => ({
            type: "session.event" as const,
            ...e,
          }));
          setEvents(normalised);
        } else if (frame.type === "session.event") {
          setEvents((prev) => [...prev, frame]);
        }
      },
      onError: () => {
        setError("WebSocket connection error.");
      },
    });

    // React calls this on unmount — closes the socket cleanly (code 1000).
    return cancel;
  }, [sessionId]);

  // Fetch the report when a terminal REPORT_READY event arrives.
  useEffect(() => {
    if (!sessionId) return;
    const lastTerminal = events.find((e) => TERMINAL_STATES.includes(e.toState));
    if (lastTerminal?.toState === "REPORT_READY" && !report) {
      apiClient
        .getReport(sessionId)
        .then(setReport)
        .catch((e: unknown) => {
          const msg =
            e instanceof ApiError
              ? e.problem.detail || e.problem.title
              : String(e);
          setReportError(`Failed to load report: ${msg ?? "unknown error"}`);
        });
    }
  }, [events, sessionId, report]);

  if (error) {
    return (
      <main>
        <h1>Session</h1>
        <div className="alert">{error}</div>
      </main>
    );
  }

  const currentState =
    events.length > 0 ? events[events.length - 1].toState : null;

  return (
    <main>
      <h1>Session</h1>
      {sessionId && (
        <p style={{ fontSize: 13, color: "#64748b", wordBreak: "break-all" }}>
          <strong>ID:</strong> {sessionId}
        </p>
      )}

      {currentState && (
        <p>
          <strong>Current state:</strong>{" "}
          <span style={{ fontFamily: "monospace" }}>{currentState}</span>
        </p>
      )}

      {/* Timeline */}
      <section style={{ marginTop: 24 }}>
        <h2 style={{ fontSize: 16, marginBottom: 8 }}>Event timeline</h2>
        {events.length === 0 ? (
          <p style={{ color: "#64748b", fontSize: 14 }}>
            Connecting…
          </p>
        ) : (
          <ol
            style={{
              listStyle: "none",
              padding: 0,
              margin: 0,
              display: "flex",
              flexDirection: "column",
              gap: 8,
            }}
          >
            {events.map((ev) => (
              <li
                key={ev.eventId}
                style={{
                  fontSize: 13,
                  padding: "8px 12px",
                  background: "#f8fafc",
                  border: "1px solid #e2e8f0",
                  borderRadius: 6,
                }}
              >
                <span style={{ color: "#94a3b8", marginRight: 8 }}>
                  {new Date(ev.occurredAt).toLocaleTimeString()}
                </span>
                {ev.fromState && (
                  <>
                    <span style={{ fontFamily: "monospace" }}>{ev.fromState}</span>
                    <span style={{ margin: "0 6px", color: "#94a3b8" }}>→</span>
                  </>
                )}
                <span
                  style={{
                    fontFamily: "monospace",
                    fontWeight: 600,
                    color: stateColor(ev.toState),
                  }}
                >
                  {ev.toState}
                </span>
              </li>
            ))}
          </ol>
        )}
      </section>

      {/* Report */}
      {reportError && (
        <div className="alert" style={{ marginTop: 24 }}>
          {reportError}
        </div>
      )}

      {report && (
        <section style={{ marginTop: 32 }}>
          <h2 style={{ fontSize: 18, marginBottom: 4 }}>Analysis report</h2>
          <p style={{ fontSize: 13, color: "#64748b", marginBottom: 16 }}>
            Confidence: <strong>{report.confidence}</strong> &middot;{" "}
            {new Date(report.createdAt).toLocaleString()}
          </p>

          <p style={{ marginBottom: 16 }}>{report.payload.summary}</p>

          {report.payload.risks.length > 0 && (
            <>
              <h3 style={{ fontSize: 15, marginBottom: 8 }}>Risks</h3>
              <ul style={{ paddingLeft: 20, marginBottom: 16 }}>
                {report.payload.risks.map((r, i) => (
                  <li key={i} style={{ marginBottom: 8, fontSize: 14 }}>
                    <strong>{r.title}</strong>{" "}
                    <span
                      style={{
                        fontSize: 11,
                        padding: "1px 6px",
                        borderRadius: 4,
                        background: severityBg(r.severity),
                        color: "#fff",
                        marginLeft: 4,
                      }}
                    >
                      {r.severity}
                    </span>
                    <br />
                    <span style={{ color: "#475569" }}>{r.description}</span>
                  </li>
                ))}
              </ul>
            </>
          )}

          {report.payload.strengths.length > 0 && (
            <>
              <h3 style={{ fontSize: 15, marginBottom: 8 }}>Strengths</h3>
              <ul style={{ paddingLeft: 20, marginBottom: 16 }}>
                {report.payload.strengths.map((s, i) => (
                  <li key={i} style={{ marginBottom: 4, fontSize: 14 }}>
                    <strong>{s.title}</strong> — {s.description}
                  </li>
                ))}
              </ul>
            </>
          )}

          {report.payload.improvements.length > 0 && (
            <>
              <h3 style={{ fontSize: 15, marginBottom: 8 }}>Improvements</h3>
              <ul style={{ paddingLeft: 20 }}>
                {report.payload.improvements.map((im, i) => (
                  <li key={i} style={{ marginBottom: 4, fontSize: 14 }}>
                    <strong>{im.title}</strong> — {im.rationale}
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}

      {/* Waiting indicator for non-terminal states */}
      {currentState && !TERMINAL_STATES.includes(currentState) && (
        <p style={{ marginTop: 24, fontSize: 13, color: "#64748b" }}>
          Processing… waiting for analysis to complete.
        </p>
      )}

      {currentState === "FAILED" && (
        <div className="alert" style={{ marginTop: 24 }}>
          Session failed.
        </div>
      )}

      {currentState === "CANCELED" && (
        <div className="alert" style={{ marginTop: 24 }}>
          Session was canceled.
        </div>
      )}
    </main>
  );
}

function stateColor(state: SessionState): string {
  switch (state) {
    case "REPORT_READY":
      return "#16a34a";
    case "FAILED":
      return "#b91c1c";
    case "CANCELED":
      return "#92400e";
    default:
      return "#1d4ed8";
  }
}

function severityBg(severity: string): string {
  switch (severity.toLowerCase()) {
    case "critical":
      return "#7f1d1d";
    case "high":
      return "#b91c1c";
    case "medium":
      return "#b45309";
    case "low":
      return "#15803d";
    default:
      return "#475569";
  }
}
