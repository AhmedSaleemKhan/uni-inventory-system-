import { useEffect, useState } from "react";
import { Pencil, Trash2 } from "lucide-react";
import { api } from "../api/client";
import { useAuth, hasPermission } from "../context/AuthContext";
import DataTable from "../components/DataTable";
import FormModal from "../components/FormModal";

const UNITS = ["pcs", "box", "ream", "pack", "dozen"];
const STATUSES = ["Active", "Discontinued", "Damaged"];

export default function Inventory() {
  const { user } = useAuth();
  const canManage = hasPermission(user.role, "manage_inventory");

  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [editing, setEditing] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState("");

  function load() {
    api.get("/inventory").then(setItems).catch((e) => setError(e.message));
    api.get("/inventory/categories").then((cs) => setCategories(cs.map((c) => c.name))).catch(() => {});
    api.get("/suppliers").then((ss) => setSuppliers(ss.map((s) => s.name))).catch(() => {});
  }
  useEffect(load, []);

  const fields = [
    { key: "category", label: "Category", kind: "select", options: categories, required: true },
    { key: "name", label: "Item Name", required: true },
    { key: "description", label: "Description", kind: "textarea" },
    { key: "brand", label: "Brand" },
    { key: "supplier", label: "Supplier", kind: "select", options: ["", ...suppliers] },
    { key: "purchase_date", label: "Purchase Date", kind: "date" },
    { key: "purchase_cost", label: "Purchase Cost", kind: "number", step: 0.01, max: 1000000 },
    { key: "selling_cost", label: "Selling Cost", kind: "number", step: 0.01, max: 1000000 },
    { key: "unit", label: "Unit", kind: "select", options: UNITS },
    { key: "current_quantity", label: "Current Quantity", kind: "number", max: 100000 },
    { key: "minimum_quantity", label: "Minimum Quantity", kind: "number", max: 100000, default: 10 },
    { key: "maximum_quantity", label: "Maximum Quantity", kind: "number", max: 1000000, default: 1000 },
    { key: "storage_location", label: "Storage Location" },
    { key: "status", label: "Status", kind: "select", options: STATUSES },
    { key: "notes", label: "Notes", kind: "textarea" },
  ];

  async function handleSave(values) {
    if (editing) await api.put(`/inventory/${editing.id}`, values);
    else await api.post("/inventory", values);
    setShowModal(false);
    setEditing(null);
    load();
  }

  async function handleDelete() {
    if (!selected) return;
    if (!confirm("Delete this inventory item permanently?")) return;
    try {
      await api.del(`/inventory/${selected.id}`);
      setSelected(null);
      load();
    } catch (e) {
      alert(e.message);
    }
  }

  const columns = [
    { key: "id", label: "ID" }, { key: "barcode", label: "Barcode" }, { key: "category", label: "Category" },
    { key: "name", label: "Name" }, { key: "brand", label: "Brand" }, { key: "supplier", label: "Supplier" },
    { key: "unit", label: "Unit" }, { key: "current_quantity", label: "Qty" }, { key: "minimum_quantity", label: "Min Qty" },
    { key: "purchase_cost", label: "Purchase Cost", render: (r) => `Rs. ${r.purchase_cost.toFixed(2)}` },
    { key: "selling_cost", label: "Selling Cost", render: (r) => `Rs. ${r.selling_cost.toFixed(2)}` },
    { key: "storage_location", label: "Location" },
    {
      key: "status", label: "Status", render: (r) => (
        <span className={`pill ${r.is_out_of_stock ? "danger" : r.is_low_stock ? "warn" : "success"}`}>
          {r.is_out_of_stock ? "Out of stock" : r.is_low_stock ? "Low stock" : r.status}
        </span>
      ),
    },
  ];

  return (
    <div>
      {error && <div className="error-banner">{error}</div>}
      <DataTable
        title="Inventory Management" columns={columns} rows={items}
        addLabel="Add Item" canAdd={canManage}
        onAdd={() => { setEditing(null); setShowModal(true); }}
        filterOptions={categories} filterKey="category"
        selectedId={selected?.id} onSelectRow={setSelected}
        extraActions={canManage && (
          <>
            <button className="btn secondary" disabled={!selected} onClick={() => { setEditing(selected); setShowModal(true); }}><Pencil size={14} /> Edit Selected</button>
            <button className="btn danger" disabled={!selected} onClick={handleDelete}><Trash2 size={14} /> Delete Selected</button>
          </>
        )}
      />
      {showModal && (
        <FormModal
          title={editing ? "Edit Inventory Item" : "Add Inventory Item"}
          fields={fields}
          initial={editing}
          onSave={handleSave}
          onClose={() => { setShowModal(false); setEditing(null); }}
        />
      )}
    </div>
  );
}
