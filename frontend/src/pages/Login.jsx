import { useState } from "react";
import { ShieldCheck, Package, Briefcase, Printer, LogIn, Boxes } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import Footer from "../components/Footer";

const QUICK_ROLES = [
  { username: "admin", password: "admin123", name: "Super Admin", desc: "Full system access", icon: ShieldCheck, color: "#28466b" },
  { username: "storekeeper", password: "password123", name: "Store Keeper", desc: "Inventory & stock", icon: Package, color: "#3d6ea3" },
  { username: "officestaff", password: "password123", name: "Office Staff", desc: "Issue items & documents", icon: Briefcase, color: "#2e8b57" },
  { username: "printstaff", password: "password123", name: "Printing Staff", desc: "Printing jobs", icon: Printer, color: "#b35a0d" },
];

export default function Login() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function doLogin(u, p) {
    if (!u || !p) {
      setError("Please enter both username and password.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await login(u, p);
    } catch (err) {
      setError(err.message || "Invalid username or password.");
    } finally {
      setBusy(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    doLogin(username, password);
  }

  return (
    <div className="login-screen">
      <div className="login-top-banner">
        <span className="brand-mark"><Boxes size={21} strokeWidth={2.4} /></span>
        <div className="org-text">
          <span className="line1">SCS Inventory</span>
          <span className="line2">School of Computing Sciences</span>
        </div>
      </div>
      <div className="login-body">
        <div className="login-card">
          <div className="login-brand">
            <h1>SCS</h1>
            <p>School of Computing
              <br />Sciences Inventory
              <br />Management System</p>
          </div>
          <div className="login-form-panel">
            <div className="login-form">
              <div className="role-picker-label">Who are you?</div>
              <div className="role-grid">
                {QUICK_ROLES.map((r) => {
                  const Icon = r.icon;
                  return (
                    <button
                      key={r.username}
                      type="button"
                      className="role-card"
                      style={{ "--role-color": r.color }}
                      disabled={busy}
                      onClick={() => { setUsername(r.username); setPassword(r.password); doLogin(r.username, r.password); }}
                    >
                      <span className="role-icon"><Icon strokeWidth={2.2} /></span>
                      <span className="role-name">{r.name}</span>
                      <span className="role-desc">{r.desc}</span>
                    </button>
                  );
                })}
              </div>

              <div className="login-divider">or sign in manually</div>

              <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
                <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
                {error && <div className="error-banner">{error}</div>}
                <button className="btn" type="submit" disabled={busy}><LogIn size={15} /> {busy ? "Signing in..." : "Login"}</button>
                <div className="login-hint">Default: admin / admin123</div>
              </form>
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}
