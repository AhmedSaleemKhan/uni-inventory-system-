import { useState } from "react";
import { useAuth } from "../context/AuthContext";

const THEME_KEY = "uaims_theme";

export function applyStoredTheme() {
  const theme = localStorage.getItem(THEME_KEY) || "light";
  document.documentElement.setAttribute("data-theme", theme);
}

export default function Settings() {
  const { user } = useAuth();
  const [dark, setDark] = useState(() => (localStorage.getItem(THEME_KEY) || "light") === "dark");

  function toggleTheme(checked) {
    setDark(checked);
    const theme = checked ? "dark" : "light";
    localStorage.setItem(THEME_KEY, theme);
    document.documentElement.setAttribute("data-theme", theme);
  }

  return (
    <div>
      <h1 className="page-title-heading">Settings</h1>

      <div className="card" style={{ padding: 16, marginBottom: 16 }}>
        <div style={{ fontWeight: 700, marginBottom: 8 }}>Profile</div>
        <div><strong>Logged in as:</strong> {user.full_name} ({user.username})</div>
        <div><strong>Role:</strong> {user.role}</div>
      </div>

      <div className="card" style={{ padding: 16 }}>
        <div style={{ fontWeight: 700, marginBottom: 8 }}>Appearance</div>
        <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13.5 }}>
          <input type="checkbox" checked={dark} onChange={(e) => toggleTheme(e.target.checked)} style={{ width: 18, height: 18 }} />
          Enable Dark Mode
        </label>
      </div>
    </div>
  );
}
