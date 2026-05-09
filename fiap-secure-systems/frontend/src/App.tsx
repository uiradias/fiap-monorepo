import { Link, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import ProtectedRoute from "./auth/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";

function Placeholder({ name }: { name: string }) {
  return (
    <main>
      <h1>{name}</h1>
      <p>Will be implemented in a later task.</p>
    </main>
  );
}

function NavLinks() {
  const { authed, logout } = useAuth();
  return (
    <nav>
      {!authed && <Link to="/login">Login</Link>}
      {!authed && <Link to="/register">Register</Link>}
      {authed && <Link to="/upload">Upload</Link>}
      {authed && <button onClick={logout} className="link-button">Logout</button>}
    </nav>
  );
}

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <Link to="/" className="brand">fiap-secure-systems</Link>
        <NavLinks />
      </header>
      <Routes>
        <Route path="/" element={<Placeholder name="Home" />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/upload" element={<ProtectedRoute><Placeholder name="Upload" /></ProtectedRoute>} />
        <Route path="/sessions/:id" element={<ProtectedRoute><Placeholder name="Session" /></ProtectedRoute>} />
        <Route path="*" element={<Placeholder name="Not found" />} />
      </Routes>
    </div>
  );
}
