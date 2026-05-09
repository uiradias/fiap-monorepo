import { useState, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../api/types";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(ev: FormEvent) {
    ev.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
      navigate("/upload");
    } catch (e) {
      const msg = e instanceof ApiError ? e.problem.detail || e.problem.title : String(e);
      setError(msg ?? "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <h1>Login</h1>
      <form className="card" onSubmit={onSubmit}>
        {error && <div className="alert">{error}</div>}
        <label>
          Email
          <input type="email" required value={email}
                 onChange={(e) => setEmail(e.target.value)} autoFocus />
        </label>
        <label>
          Password
          <input type="password" required minLength={8} value={password}
                 onChange={(e) => setPassword(e.target.value)} />
        </label>
        <button type="submit" disabled={busy}>
          {busy ? "Logging in…" : "Login"}
        </button>
        <p style={{ marginTop: 16, fontSize: 14 }}>
          New here? <Link to="/register">Register</Link>
        </p>
      </form>
    </main>
  );
}
