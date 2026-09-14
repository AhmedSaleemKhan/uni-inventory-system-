import { useEffect, useRef, useState } from "react";
import { Routes, Route, Navigate, Outlet, useLocation } from "react-router-dom";
import { Clock, Bell } from "lucide-react";
import { useAuth, hasPermission } from "./context/AuthContext";
import { api } from "./api/client";
import Sidebar from "./components/Sidebar";
import Footer from "./components/Footer";

import Login from "./pages/Login";
import ForceChangePassword from "./pages/ForceChangePassword";
import Dashboard from "./pages/Dashboard";
import Inventory from "./pages/Inventory";
import IssueItems from "./pages/IssueItems";
import ReturnItems from "./pages/ReturnItems";
import Printing from "./pages/Printing";
import Teachers from "./pages/Teachers";
import Documents from "./pages/Documents";
import Reports from "./pages/Reports";
import Users from "./pages/Users";
import Settings from "./pages/Settings";

const PAGE_TITLES = {
  "/": "Dashboard",
  "/inventory": "Inventory Management",
  "/issue": "Inventory Issue",
  "/return": "Return Management",
  "/printing": "Printing Management",
  "/teachers": "Teacher Management",
  "/documents": "Document Tracking",
  "/reports": "Reports Center",
  "/users": "User Management",
  "/settings": "Settings",
};

function LiveClock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  const text = now.toLocaleString(undefined, {
    weekday: "long", day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
  return (
    <div className="datetime-chip">
      <Clock strokeWidth={2.2} />
      {text}
    </div>
  );
}

function NotifBell() {
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);

  useEffect(() => {
    api.get("/dashboard").then((d) => setNotifications(d.notifications || [])).catch(() => {});
  }, []);

  useEffect(() => {
    if (!open) return;
    function onDocMouseDown(e) {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", onDocMouseDown);
    return () => document.removeEventListener("mousedown", onDocMouseDown);
  }, [open]);

  const realCount = notifications.filter((n) => n !== "No active notifications.").length;

  return (
    <div style={{ position: "relative" }} ref={wrapRef}>
      <button className="notif-bell" onClick={() => setOpen((o) => !o)} aria-label="Notifications">
        <Bell strokeWidth={2.2} />
        {realCount > 0 && <span className="badge">{realCount > 99 ? "99+" : realCount}</span>}
      </button>
      {open && (
        <div className="notif-panel">
          <div className="notif-panel-title">Notifications &amp; Alerts</div>
          {realCount === 0 && <div className="notif-panel-empty">No active notifications.</div>}
          {notifications.filter((n) => n !== "No active notifications.").map((n, i) => (
            <div key={i} className="notif-panel-item">{n}</div>
          ))}
        </div>
      )}
    </div>
  );
}

function Breadcrumb({ pathname }) {
  const title = PAGE_TITLES[pathname] || "";
  if (pathname === "/") {
    return (
      <div className="breadcrumb">
        <span className="crumb-current">Dashboard</span>
      </div>
    );
  }
  return (
    <div className="breadcrumb">
      <span>Dashboard</span>
      <span className="crumb-sep">/</span>
      <span className="crumb-current">{title}</span>
    </div>
  );
}

function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const initials = (user.full_name || user.username || "?").trim().split(/\s+/).map((p) => p[0]).slice(0, 2).join("").toUpperCase();

  return (
    <div className="app-shell">
      <Sidebar role={user.role} onLogout={logout} />
      <div className="main-area">
        <div className="topbar">
          <Breadcrumb pathname={location.pathname} />
          <div className="topbar-extras">
            <LiveClock />
            <NotifBell />
            <div className="user-chip">
              <span className="avatar">{initials}</span>
              <span className="who">
                <span className="role">{user.role}</span>
                <span className="name">{user.full_name}</span>
              </span>
            </div>
          </div>
        </div>
        <div className="page">
          <Outlet />
        </div>
        <Footer />
      </div>
    </div>
  );
}

function RequirePermission({ permission, children }) {
  const { user } = useAuth();
  if (!hasPermission(user.role, permission)) {
    return <div className="empty-state">You don't have permission to view this page.</div>;
  }
  return children;
}

export default function App() {
  const { user, loading } = useAuth();

  if (loading) return <div className="empty-state">Loading...</div>;
  if (!user) {
    return (
      <Routes>
        <Route path="*" element={<Login />} />
      </Routes>
    );
  }
  if (user.must_change_password) {
    return <ForceChangePassword />;
  }

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/inventory" element={<RequirePermission permission="view_inventory"><Inventory /></RequirePermission>} />
        <Route path="/issue" element={<RequirePermission permission="issue_items"><IssueItems /></RequirePermission>} />
        <Route path="/return" element={<RequirePermission permission="return_items"><ReturnItems /></RequirePermission>} />
        <Route path="/printing" element={<RequirePermission permission="manage_printing"><Printing /></RequirePermission>} />
        <Route path="/teachers" element={<RequirePermission permission="manage_teachers"><Teachers /></RequirePermission>} />
        <Route path="/documents" element={<RequirePermission permission="manage_documents"><Documents /></RequirePermission>} />
        <Route path="/reports" element={<RequirePermission permission="view_reports"><Reports /></RequirePermission>} />
        <Route path="/users" element={<RequirePermission permission="manage_users"><Users /></RequirePermission>} />
        <Route path="/settings" element={<RequirePermission permission="manage_settings"><Settings /></RequirePermission>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
