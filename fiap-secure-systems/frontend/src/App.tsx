import { Link, Route, Routes } from "react-router-dom";

function Placeholder({ name }: { name: string }) {
  return (
    <main>
      <h1>{name}</h1>
      <p>Will be implemented in a later task.</p>
    </main>
  );
}

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <Link to="/" className="brand">fiap-secure-systems</Link>
        <nav>
          <Link to="/login">Login</Link>
          <Link to="/register">Register</Link>
          <Link to="/upload">Upload</Link>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<Placeholder name="Home" />} />
        <Route path="/login" element={<Placeholder name="Login" />} />
        <Route path="/register" element={<Placeholder name="Register" />} />
        <Route path="/upload" element={<Placeholder name="Upload" />} />
        <Route path="/sessions/:id" element={<Placeholder name="Session" />} />
        <Route path="*" element={<Placeholder name="Not found" />} />
      </Routes>
    </div>
  );
}
