import { useEffect, useState } from "react";
import { Pencil, Trash2 } from "lucide-react";
import { api } from "../api/client";
import { useAuth, hasPermission } from "../context/AuthContext";
import DataTable from "../components/DataTable";
import FormModal from "../components/FormModal";

export default function Suppliers() {
  const { user } = useAuth();
  const canManage = hasPermission(user.role, "manage_suppliers");

  const [suppliers, setSuppliers] = useState([]);
  const [editing, setEditing] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState("");

  function load() {
    api.get("/suppliers").then(setSuppliers).catch((e) => setError(e.message));
  }
  useEffect(load, []);

  const fields = [
    { key: "name", label: "Supplier Name", required: true },
    { key: "address", label: "Address", kind: "textarea" },
    { key: "phone", label: "Phone" },
    { key: "email", label: "Email" },
    { key: "gst_number", label: "GST Number" },
    { key: "notes", label: "Notes", kind: "textarea" },
  ];

  async function handleSave(values) {
    if (editing) await api.put(`/suppliers/${editing.id}`, values);
    else await api.post("/suppliers", values);
    setShowModal(false);
    setEditing(null);
    load();
  }

  async function handleDelete() {
    if (!selected || !confirm("Delete this supplier permanently?")) return;
    try {
      await api.del(`/suppliers/${selected.id}`);
      setSelected(null);
      load();
    } catch (e) {
      alert(e.message);
    }
  }

  const columns = [
    { key: "id", label: "ID" }, { key: "name", label: "Name" }, { key: "phone", label: "Phone" },
    { key: "email", label: "Email" }, { key: "gst_number", label: "GST Number" }, { key: "address", label: "Address" },
    { key: "total_purchases", label: "Total Purchases", render: (r) => `Rs. ${r.total_purchases.toFixed(2)}` },
  ];

  return (
    <div>
      {error && <div className="error-banner">{error}</div>}
      <DataTable
        title="Supplier Management" columns={columns} rows={suppliers}
        addLabel="Add Supplier" canAdd={canManage}
        onAdd={() => { setEditing(null); setShowModal(true); }}
        selectedId={selected?.id} onSelectRow={setSelected}
        extraActions={canManage && (
          <>
            <button className="btn secondary" disabled={!selected} onClick={() => { setEditing(selected); setShowModal(true); }}><Pencil size={14} /> Edit Selected</button>
            <button className="btn danger" disabled={!selected} onClick={handleDelete}><Trash2 size={14} /> Delete Selected</button>
          </>
        )}
      />
      {showModal && (
        <FormModal title={editing ? "Edit Supplier" : "Add Supplier"} fields={fields} initial={editing}
          onSave={handleSave} onClose={() => { setShowModal(false); setEditing(null); }} />
      )}
    </div>
  );
}
