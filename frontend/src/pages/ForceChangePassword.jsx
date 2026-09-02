import { useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function ForceChangePassword() {
  const { refreshMe, logout } = useAuth();
  const [pwd, setPwd] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (pwd.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }
    if (pwd !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await api.post("/auth/change-password", { new_password: pwd });
      await refreshMe();
    } catch (err) {
      setError(err.message || "Could not update password.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <h2>Change Password Required</h2>
        <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
          For security, please set a new password before continuing.
        </p>
        <form onSubmit={handleSubmit}>
          {error && <div className="error-banner">{error}</div>}
          <div className="field">
            <label>New Password</label>
            <input type="password" value={pwd} onChange={(e) => setPwd(e.target.value)} autoFocus />
          </div>
          <div className="field">
            <label>Confirm Password</label>
            <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn secondary" onClick={logout}>Cancel</button>
            <button type="submit" className="btn" disabled={busy}>{busy ? "Saving..." : "Set New Password"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
