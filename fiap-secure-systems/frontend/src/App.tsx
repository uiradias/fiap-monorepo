import { Link, Outlet, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import ProtectedRoute from "./auth/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import SessionPage from "./pages/SessionPage";
import SessionsListPage from "./pages/SessionsListPage";
import UploadPage from "./pages/UploadPage";

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
    <nav className="topbar-right" aria-label="Account">
      {!authed && <Link to="/login">Login</Link>}
      {!authed && <Link to="/register">Register</Link>}
      {authed && (
        <button type="button" onClick={logout} className="link-button">
          Logout
        </button>
      )}
    </nav>
  );
}

function MainNav() {
  const { authed } = useAuth();
  if (!authed) return null;
  return (
    <nav className="topbar-main" aria-label="Main">
      <Link to="/sessions">Past analyses</Link>
      <Link to="/upload">Upload</Link>
    </nav>
  );
}

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-left">
          <Link to="/" className="brand">
            fiap-secure-systems
          </Link>
          <MainNav />
        </div>
        <NavLinks />
      </header>
      <Routes>
        <Route path="/" element={<Placeholder name="Home" />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/upload" element={<ProtectedRoute><UploadPage /></ProtectedRoute>} />
        <Route
          path="/sessions"
          element={
            <ProtectedRoute>
              <Outlet />
            </ProtectedRoute>
          }
        >
          <Route index element={<SessionsListPage />} />
          <Route path=":id" element={<SessionPage />} />
        </Route>
        <Route path="*" element={<Placeholder name="Not found" />} />
      </Routes>
    </div>
  );
}
