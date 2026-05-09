import { useState, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../api/types";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(ev: FormEvent) {
    ev.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await register(email, password, displayName.trim() || undefined);
      navigate("/upload");
    } catch (e) {
      const msg = e instanceof ApiError ? e.problem.detail || e.problem.title : String(e);
      setError(msg ?? "Registration failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <h1>Register</h1>
      <form className="card" onSubmit={onSubmit}>
        {error && <div className="alert">{error}</div>}
        <label>
          Email
          <input type="email" required value={email}
                 onChange={(e) => setEmail(e.target.value)} autoFocus />
        </label>
        <label>
          Password (≥ 8 chars)
          <input type="password" required minLength={8} value={password}
                 onChange={(e) => setPassword(e.target.value)} />
        </label>
        <label>
          Display name (optional)
          <input type="text" value={displayName}
                 onChange={(e) => setDisplayName(e.target.value)} />
        </label>
        <button type="submit" disabled={busy}>
          {busy ? "Registering…" : "Register"}
        </button>
        <p style={{ marginTop: 16, fontSize: 14 }}>
          Already have an account? <Link to="/login">Login</Link>
        </p>
      </form>
    </main>
  );
}
