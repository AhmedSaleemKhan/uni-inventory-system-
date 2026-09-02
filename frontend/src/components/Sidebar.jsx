import { NavLink } from "react-router-dom";
import { hasPermission } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", permission: "view_dashboard", end: true },
  { to: "/inventory", label: "Inventory", permission: "view_inventory" },
  { to: "/issue", label: "Issue Items", permission: "issue_items" },
  { to: "/return", label: "Return Items", permission: "return_items" },
  { to: "/printing", label: "Printing", permission: "manage_printing" },
  { to: "/teachers", label: "Teachers", permission: "manage_teachers" },
  { to: "/documents", label: "Documents", permission: "manage_documents" },
  { to: "/suppliers", label: "Suppliers", permission: "manage_suppliers" },
  { to: "/purchases", label: "Purchases", permission: "manage_purchases" },
  { to: "/reports", label: "Reports", permission: "view_reports" },
  { to: "/users", label: "Users", permission: "manage_users" },
  { to: "/settings", label: "Settings", permission: "manage_settings" },
];

export default function Sidebar({ role, onLogout }) {
  return (
    <div className="sidebar">
      <div className="sidebar-brand">UAIMS</div>
      <div className="sidebar-role">{role}</div>
      <nav>
        {NAV_ITEMS.filter((item) => hasPermission(role, item.permission)).map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} className={({ isActive }) => (isActive ? "active" : "")}>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <button className="sidebar-logout" onClick={onLogout}>Logout</button>
    </div>
  );
}
