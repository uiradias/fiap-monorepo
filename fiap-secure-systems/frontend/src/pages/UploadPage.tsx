import { useState, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../api/client";
import { ApiError } from "../api/types";

const ALLOWED_TYPES = new Set(["application/pdf", "image/png", "image/jpeg", "image/webp"]);
const MAX_FILE_BYTES = 25 * 1024 * 1024; // 25 MiB
const MAX_FILES = 20;

type FileItem = {
  id: string;
  file: File;
  status: "pending" | "uploading" | "done" | "error";
  error?: string;
};

export default function UploadPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<FileItem[]>([]);
  const [bundleId, setBundleId] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Creates bundle lazily on first call; subsequent calls return the cached id.
  const ensureBundle = useCallback(async (): Promise<string> => {
    if (bundleId) return bundleId;
    const bundle = await apiClient.createBundle();
    setBundleId(bundle.bundleId);
    return bundle.bundleId;
  }, [bundleId]);

  function validate(files: File[]): { valid: File[]; errors: string[] } {
    const errors: string[] = [];
    const valid: File[] = [];
    const remaining = MAX_FILES - items.length;

    for (const f of files) {
      if (!ALLOWED_TYPES.has(f.type)) {
        errors.push(`${f.name}: unsupported type (${f.type || "unknown"})`);
        continue;
      }
      if (f.size > MAX_FILE_BYTES) {
        errors.push(`${f.name}: exceeds 25 MiB limit`);
        continue;
      }
      valid.push(f);
    }

    if (valid.length > remaining) {
      const excess = valid.splice(remaining);
      errors.push(`${excess.length} file(s) skipped — would exceed ${MAX_FILES}-file limit`);
    }

    return { valid, errors };
  }

  async function addFiles(files: File[]) {
    const { valid, errors } = validate(files);

    if (errors.length) {
      setGlobalError(errors.join("\n"));
    } else {
      setGlobalError(null);
    }

    if (!valid.length) return;

    // Append as pending first so the UI updates immediately. Each item gets a stable
    // id so subsequent state transitions can locate it after `setItems` replaces objects.
    const newItems: FileItem[] = valid.map((f) => ({
      id: crypto.randomUUID(),
      file: f,
      status: "pending",
    }));
    setItems((prev) => [...prev, ...newItems]);
    const newIds = new Set(newItems.map((it) => it.id));

    // Obtain (or create) the bundle.
    let bid: string;
    try {
      bid = await ensureBundle();
    } catch (e) {
      const msg = e instanceof ApiError ? e.problem.detail || e.problem.title : String(e);
      setGlobalError(`Failed to create bundle: ${msg ?? "unknown error"}`);
      setItems((prev) => prev.filter((it) => !newIds.has(it.id)));
      return;
    }

    // Upload each file sequentially (keeps bundle state sane on the server).
    for (const item of newItems) {
      setItems((prev) =>
        prev.map((it) => (it.id === item.id ? { ...it, status: "uploading" } : it))
      );
      try {
        await apiClient.uploadAsset(bid, item.file);
        setItems((prev) =>
          prev.map((it) => (it.id === item.id ? { ...it, status: "done" } : it))
        );
      } catch (e) {
        const msg = e instanceof ApiError ? e.problem.detail || e.problem.title : String(e);
        setItems((prev) =>
          prev.map((it) =>
            it.id === item.id ? { ...it, status: "error", error: msg ?? "upload failed" } : it
          )
        );
      }
    }
  }

  function onDragOver(ev: React.DragEvent) {
    ev.preventDefault();
    setDragOver(true);
  }

  function onDragLeave() {
    setDragOver(false);
  }

  function onDrop(ev: React.DragEvent) {
    ev.preventDefault();
    setDragOver(false);
    const files = Array.from(ev.dataTransfer.files);
    if (files.length) addFiles(files);
  }

  function onInputChange(ev: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(ev.target.files ?? []);
    ev.target.value = ""; // reset so same file can be re-picked after removal
    if (files.length) addFiles(files);
  }

  async function onFinalize() {
    if (!bundleId) return;
    const hasErrors = items.some((it) => it.status === "error");
    if (hasErrors) {
      setGlobalError("Some files failed to upload. Remove them or retry before finalizing.");
      return;
    }
    setBusy(true);
    setGlobalError(null);
    try {
      const result = await apiClient.finalizeBundle(bundleId);
      navigate(`/sessions/${result.sessionId}`);
    } catch (e) {
      const msg = e instanceof ApiError ? e.problem.detail || e.problem.title : String(e);
      setGlobalError(`Finalize failed: ${msg ?? "unknown error"}`);
    } finally {
      setBusy(false);
    }
  }

  const doneCount = items.filter((it) => it.status === "done").length;
  const canFinalize = doneCount > 0 && !busy && items.every((it) => it.status !== "uploading");

  return (
    <main>
      <h1>Upload Files</h1>
      <p style={{ fontSize: 14, color: "#475569" }}>
        PDF, PNG, JPEG, or WebP · max 25 MiB each · up to {MAX_FILES} files
      </p>

      {globalError && (
        <div className="alert" style={{ whiteSpace: "pre-line", marginBottom: 16 }}>
          {globalError}
        </div>
      )}

      <div
        className={`dropzone${dragOver ? " over" : ""}`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        style={{ cursor: "pointer", marginBottom: 24 }}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        aria-label="Drop files here or click to pick"
      >
        <p style={{ margin: 0, color: "#64748b" }}>
          Drop files here, or <strong>click to pick</strong>
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.png,.jpg,.jpeg,.webp"
          style={{ display: "none" }}
          onChange={onInputChange}
        />
      </div>

      {items.length > 0 && (
        <ul style={{ listStyle: "none", padding: 0, marginBottom: 24 }}>
          {items.map((it) => (
            <li
              key={it.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "6px 0",
                borderBottom: "1px solid #e2e8f0",
                fontSize: 14,
              }}
            >
              <StatusIcon status={it.status} />
              <span style={{ flex: 1 }}>{it.file.name}</span>
              <span style={{ color: "#94a3b8" }}>
                {(it.file.size / 1024 / 1024).toFixed(2)} MiB
              </span>
              {it.error && <span style={{ color: "#b91c1c", fontSize: 12 }}>{it.error}</span>}
            </li>
          ))}
        </ul>
      )}

      {items.length > 0 && (
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <button
            className="primary"
            onClick={onFinalize}
            disabled={!canFinalize}
          >
            {busy ? "Finalizing…" : `Finalize (${doneCount} file${doneCount !== 1 ? "s" : ""})`}
          </button>
          <span style={{ fontSize: 13, color: "#64748b" }}>
            {items.filter((it) => it.status === "uploading").length > 0 && "Uploading…"}
          </span>
        </div>
      )}
    </main>
  );
}

function StatusIcon({ status }: { status: FileItem["status"] }) {
  switch (status) {
    case "pending":
      return <span style={{ color: "#94a3b8" }}>○</span>;
    case "uploading":
      return <span style={{ color: "#3b82f6" }}>↑</span>;
    case "done":
      return <span style={{ color: "#16a34a" }}>✓</span>;
    case "error":
      return <span style={{ color: "#b91c1c" }}>✗</span>;
  }
}
