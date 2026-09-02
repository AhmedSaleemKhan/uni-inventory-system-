import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, Package, ArrowUpFromLine, ArrowDownToLine, Printer,
  GraduationCap, FileText, Truck, ShoppingCart, BarChart3, UserCog, Settings, LogOut, Boxes,
} from "lucide-react";
import { hasPermission } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", permission: "view_dashboard", end: true, icon: LayoutDashboard },
  { to: "/inventory", label: "Inventory", permission: "view_inventory", icon: Package },
  { to: "/issue", label: "Issue Items", permission: "issue_items", icon: ArrowUpFromLine },
  { to: "/return", label: "Return Items", permission: "return_items", icon: ArrowDownToLine },
  { to: "/printing", label: "Printing", permission: "manage_printing", icon: Printer },
  { to: "/teachers", label: "Teachers", permission: "manage_teachers", icon: GraduationCap },
  { to: "/documents", label: "Documents", permission: "manage_documents", icon: FileText },
  { to: "/suppliers", label: "Suppliers", permission: "manage_suppliers", icon: Truck },
  { to: "/purchases", label: "Purchases", permission: "manage_purchases", icon: ShoppingCart },
  { to: "/reports", label: "Reports", permission: "view_reports", icon: BarChart3 },
  { to: "/users", label: "Users", permission: "manage_users", icon: UserCog },
  { to: "/settings", label: "Settings", permission: "manage_settings", icon: Settings },
];

export default function Sidebar({ role, onLogout }) {
  return (
    <div className="sidebar">
      <div className="sidebar-brand">
        <span className="brand-mark"><Boxes size={19} strokeWidth={2.4} /></span>
        UAIMS
      </div>
      <div className="sidebar-role">{role}</div>
      <nav>
        {NAV_ITEMS.filter((item) => hasPermission(role, item.permission)).map((item) => {
          const Icon = item.icon;
          return (
            <NavLink key={item.to} to={item.to} end={item.end} className={({ isActive }) => (isActive ? "active" : "")}>
              <Icon strokeWidth={2} />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
      <button className="sidebar-logout" onClick={onLogout}>
        <LogOut size={15} strokeWidth={2.2} /> Logout
      </button>
    </div>
  );
}
