import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiClient } from "../api/client";
import type { SessionState, SessionSummary } from "../api/types";
import { ApiError } from "../api/types";

function formatShortId(id: string): string {
  if (id.length <= 12) return id;
  return `${id.slice(0, 8)}…${id.slice(-4)}`;
}

function stateBadgeClass(state: SessionState): string {
  switch (state) {
    case "REPORT_READY":
      return "session-badge session-badge--ready";
    case "FAILED":
      return "session-badge session-badge--failed";
    case "CANCELED":
      return "session-badge session-badge--canceled";
    default:
      return "session-badge session-badge--progress";
  }
}

export default function SessionsListPage() {
  const [rows, setRows] = useState<SessionSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.listSessions(50);
      setRows(data);
    } catch (e: unknown) {
      const msg =
        e instanceof ApiError ? e.problem.detail || e.problem.title : String(e);
      setError(msg ?? "Failed to load sessions");
      setRows(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <main>
      <header className="sessions-list-header">
        <div>
          <h1>Past analyses</h1>
          <p className="sessions-list-sub">
            Sessions you have uploaded and analyzed. Open one to see the full timeline and report.
          </p>
        </div>
        <div className="sessions-list-actions">
          <Link to="/upload" className="button-link">
            New upload
          </Link>
          <button type="button" className="link-button" onClick={() => void load()} disabled={loading}>
            Refresh
          </button>
        </div>
      </header>

      {error && <div className="alert">{error}</div>}

      {loading && rows === null && !error && (
        <p className="sessions-list-muted">Loading sessions…</p>
      )}

      {!loading && rows && rows.length === 0 && (
        <div className="sessions-list-empty">
          <p>No sessions yet.</p>
          <p className="sessions-list-muted">
            <Link to="/upload">Upload architecture assets</Link> to start your first analysis.
          </p>
        </div>
      )}

      {rows && rows.length > 0 && (
        <div className="sessions-table-wrap">
          <table className="sessions-table">
            <thead>
              <tr>
                <th>Session</th>
                <th>State</th>
                <th>Assets</th>
                <th>Created</th>
                <th>Updated</th>
                <th>Report</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((s) => (
                <tr key={s.id}>
                  <td>
                    <span className="sessions-table-id" title={s.id}>
                      {formatShortId(s.id)}
                    </span>
                  </td>
                  <td>
                    <span className={stateBadgeClass(s.state)}>{s.state}</span>
                  </td>
                  <td>{s.assetCount}</td>
                  <td className="sessions-table-date">
                    {new Date(s.createdAt).toLocaleString()}
                  </td>
                  <td className="sessions-table-date">
                    {new Date(s.updatedAt).toLocaleString()}
                  </td>
                  <td>
                    {s.reportId ? (
                      <span className="sessions-list-muted">Yes</span>
                    ) : (
                      <span className="sessions-list-muted">—</span>
                    )}
                  </td>
                  <td className="sessions-table-actions">
                    <Link to={`/sessions/${s.id}`} className="sessions-open-link">
                      Open
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
