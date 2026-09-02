import { Routes, Route, Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth, hasPermission } from "./context/AuthContext";
import Sidebar from "./components/Sidebar";

import Login from "./pages/Login";
import ForceChangePassword from "./pages/ForceChangePassword";
import Dashboard from "./pages/Dashboard";
import Inventory from "./pages/Inventory";
import IssueItems from "./pages/IssueItems";
import ReturnItems from "./pages/ReturnItems";
import Printing from "./pages/Printing";
import Teachers from "./pages/Teachers";
import Documents from "./pages/Documents";
import Suppliers from "./pages/Suppliers";
import Purchases from "./pages/Purchases";
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
  "/suppliers": "Supplier Management",
  "/purchases": "Purchase Orders",
  "/reports": "Reports Center",
  "/users": "User Management",
  "/settings": "Settings",
};

function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();

  return (
    <div className="app-shell">
      <Sidebar role={user.role} onLogout={logout} />
      <div className="main-area">
        <div className="topbar">
          <div className="page-title">{PAGE_TITLES[location.pathname] || ""}</div>
          <div className="user">{user.full_name}</div>
        </div>
        <div className="page">
          <Outlet />
        </div>
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
        <Route path="/suppliers" element={<RequirePermission permission="manage_suppliers"><Suppliers /></RequirePermission>} />
        <Route path="/purchases" element={<RequirePermission permission="manage_purchases"><Purchases /></RequirePermission>} />
        <Route path="/reports" element={<RequirePermission permission="view_reports"><Reports /></RequirePermission>} />
        <Route path="/users" element={<RequirePermission permission="manage_users"><Users /></RequirePermission>} />
        <Route path="/settings" element={<RequirePermission permission="manage_settings"><Settings /></RequirePermission>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
