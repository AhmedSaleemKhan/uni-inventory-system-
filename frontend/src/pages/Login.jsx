import { useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!username || !password) {
      setError("Please enter both username and password.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await login(username, password);
    } catch (err) {
      setError(err.message || "Invalid username or password.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-screen">
      <div className="login-brand">
        <h1>UAIMS</h1>
        <p>University Administration
          <br />Inventory &amp; Office
          <br />Management System</p>
      </div>
      <div className="login-form-panel">
        <form className="login-form" onSubmit={handleSubmit}>
          <h2>Sign in to your account</h2>
          <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
          <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
          {error && <div className="error-banner">{error}</div>}
          <button className="btn" type="submit" disabled={busy}>{busy ? "Signing in..." : "Login"}</button>
          <div className="login-hint">Default: admin / admin123</div>
        </form>
      </div>
    </div>
  );
}
