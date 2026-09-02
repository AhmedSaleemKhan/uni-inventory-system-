import { useEffect, useState } from "react";
import { ToggleLeft, KeyRound } from "lucide-react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import DataTable from "../components/DataTable";
import FormModal from "../components/FormModal";

const ROLES = ["Super Admin", "Administrator", "Office Staff", "Store Keeper", "Printing Staff", "Department Staff"];

export default function Users() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState([]);
  const [selected, setSelected] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState("");

  function load() {
    api.get("/users").then(setUsers).catch((e) => setError(e.message));
  }
  useEffect(load, []);

  const fields = [
    { key: "username", label: "Username", required: true },
    { key: "full_name", label: "Full Name", required: true },
    { key: "role", label: "Role", kind: "select", options: ROLES, required: true },
    { key: "email", label: "Email" },
    { key: "phone", label: "Phone" },
    { key: "password", label: "Temporary Password", default: "password123", required: true },
  ];

  async function handleSave(values) {
    await api.post("/users", values);
    setShowModal(false);
    load();
  }

  async function toggleActive() {
    if (!selected) {
      alert("Please select a user.");
      return;
    }
    try {
      await api.post(`/users/${selected.id}/toggle-active`);
      setSelected(null);
      load();
    } catch (e) {
      alert(e.message);
    }
  }

  async function resetPassword() {
    if (!selected) {
      alert("Please select a user.");
      return;
    }
    const result = await api.post(`/users/${selected.id}/reset-password`);
    alert(result.message);
    setSelected(null);
    load();
  }

  const columns = [
    { key: "id", label: "ID" }, { key: "username", label: "Username" }, { key: "full_name", label: "Full Name" },
    { key: "role", label: "Role" }, { key: "email", label: "Email" },
    { key: "is_active", label: "Active", render: (r) => (r.is_active ? "Yes" : "No") },
    { key: "last_login", label: "Last Login", render: (r) => (r.last_login ? new Date(r.last_login).toLocaleString() : "Never") },
  ];

  return (
    <div>
      {error && <div className="error-banner">{error}</div>}
      <DataTable
        title="User Management" columns={columns} rows={users}
        addLabel="Add User" onAdd={() => setShowModal(true)}
        filterOptions={ROLES} filterKey="role"
        selectedId={selected?.id} onSelectRow={setSelected}
        extraActions={
          <>
            <button className="btn secondary" onClick={toggleActive}><ToggleLeft size={14} /> Toggle Active/Inactive</button>
            <button className="btn danger" onClick={resetPassword}><KeyRound size={14} /> Reset Password</button>
          </>
        }
      />
      {showModal && (
        <FormModal title="Add User" fields={fields} onSave={handleSave} onClose={() => setShowModal(false)} />
      )}
    </div>
  );
}
