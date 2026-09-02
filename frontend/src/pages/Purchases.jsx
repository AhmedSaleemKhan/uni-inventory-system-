import { useEffect, useState } from "react";
import { Plus, Trash2, X, CircleDollarSign } from "lucide-react";
import { api } from "../api/client";
import { useAuth, hasPermission } from "../context/AuthContext";
import DataTable from "../components/DataTable";

function PurchaseOrderModal({ suppliers, items, onSave, onClose }) {
  const [supplier, setSupplier] = useState(suppliers[0]?.name || "");
  const [taxPercent, setTaxPercent] = useState(0);
  const [itemName, setItemName] = useState(items[0]?.name || "");
  const [qty, setQty] = useState(1);
  const [unitCost, setUnitCost] = useState(items[0]?.purchase_cost || 0);
  const [lines, setLines] = useState([]);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  // suppliers/items can still be loading when the modal opens (the parent
  // kicks off those fetches on mount, and a fast click beats them back) -
  // useState's initializer only runs once, so re-sync once the data lands
  // instead of leaving these stuck at "" forever.
  useEffect(() => {
    if (!supplier && suppliers.length > 0) setSupplier(suppliers[0].name);
  }, [suppliers, supplier]);

  useEffect(() => {
    if (!itemName && items.length > 0) {
      setItemName(items[0].name);
      setUnitCost(items[0].purchase_cost);
    }
  }, [items, itemName]);

  function onItemChange(name) {
    setItemName(name);
    const found = items.find((i) => i.name === name);
    if (found) setUnitCost(found.purchase_cost);
  }

  function addLine() {
    if (!itemName) return;
    setLines((ls) => [...ls, { item: itemName, quantity: qty, unit_cost: unitCost }]);
  }

  function removeLine(idx) {
    setLines((ls) => ls.filter((_, i) => i !== idx));
  }

  const subtotal = lines.reduce((s, l) => s + l.quantity * l.unit_cost, 0);
  const total = subtotal * (1 + taxPercent / 100);

  async function handleSubmit() {
    if (lines.length === 0) {
      setError("Please add at least one line item.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await onSave({ supplier, tax_percent: Number(taxPercent), lines });
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" style={{ width: 520 }}>
        <h2>New Purchase Order</h2>
        {error && <div className="error-banner">{error}</div>}
        <div className="field">
          <label>Supplier</label>
          <select value={supplier} onChange={(e) => setSupplier(e.target.value)}>
            {suppliers.map((s) => <option key={s.id} value={s.name}>{s.name}</option>)}
          </select>
        </div>
        <div className="field">
          <label>Tax %</label>
          <input type="number" min={0} max={100} value={taxPercent} onChange={(e) => setTaxPercent(e.target.value)} />
        </div>

        <div style={{ display: "flex", gap: 8, alignItems: "flex-end", marginBottom: 10 }}>
          <div className="field" style={{ flex: 2, marginBottom: 0 }}>
            <label>Item</label>
            <select value={itemName} onChange={(e) => onItemChange(e.target.value)}>
              {items.map((i) => <option key={i.id} value={i.name}>{i.name}</option>)}
            </select>
          </div>
          <div className="field" style={{ flex: 1, marginBottom: 0 }}>
            <label>Qty</label>
            <input type="number" min={1} value={qty} onChange={(e) => setQty(parseInt(e.target.value || "1", 10))} />
          </div>
          <div className="field" style={{ flex: 1, marginBottom: 0 }}>
            <label>Unit Cost</label>
            <input type="number" min={0} step={0.01} value={unitCost} onChange={(e) => setUnitCost(parseFloat(e.target.value || "0"))} />
          </div>
          <button type="button" className="btn secondary" onClick={addLine}><Plus size={14} /> Add Line</button>
        </div>

        <div style={{ border: "1px solid var(--border)", borderRadius: 8, maxHeight: 140, overflowY: "auto", marginBottom: 10 }}>
          {lines.length === 0 && <div className="empty-state">No line items yet.</div>}
          {lines.map((l, i) => (
            <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "6px 10px", fontSize: 13, borderTop: i > 0 ? "1px solid var(--border)" : "none" }}>
              <span>{l.item} x{l.quantity} @ Rs. {l.unit_cost.toFixed(2)} = Rs. {(l.quantity * l.unit_cost).toFixed(2)}</span>
              <button type="button" className="btn danger icon-only" onClick={() => removeLine(i)} aria-label="Remove line"><Trash2 size={13} /></button>
            </div>
          ))}
        </div>

        <div style={{ fontWeight: 700, marginBottom: 12 }}>Total: Rs. {total.toFixed(2)}</div>

        <div className="modal-actions">
          <button type="button" className="btn secondary" onClick={onClose}><X size={14} /> Cancel</button>
          <button type="button" className="btn" disabled={saving} onClick={handleSubmit}>
            <CircleDollarSign size={14} /> {saving ? "Saving..." : "Create Purchase Order"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Purchases() {
  const { user } = useAuth();
  const canManage = hasPermission(user.role, "manage_purchases");

  const [orders, setOrders] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState("");

  function load() {
    api.get("/purchases").then(setOrders).catch((e) => setError(e.message));
    api.get("/suppliers").then(setSuppliers).catch(() => {});
    api.get("/inventory").then(setItems).catch(() => {});
  }
  useEffect(load, []);

  async function handleSave(payload) {
    await api.post("/purchases", payload);
    setShowModal(false);
    load();
    alert("Purchase order created and stock updated.");
  }

  async function markPaid() {
    if (!selected) {
      alert("Please select a purchase order.");
      return;
    }
    await api.post(`/purchases/${selected.id}/mark-paid`);
    setSelected(null);
    load();
  }

  const columns = [
    { key: "id", label: "ID" }, { key: "invoice_number", label: "Invoice #" }, { key: "supplier", label: "Supplier" },
    { key: "order_date", label: "Order Date" }, { key: "tax_percent", label: "Tax %" },
    { key: "total_amount", label: "Total Amount", render: (r) => `Rs. ${r.total_amount.toFixed(2)}` },
    {
      key: "payment_status", label: "Payment Status", render: (r) => (
        <span className={`pill ${r.payment_status === "Paid" ? "success" : r.payment_status === "Unpaid" ? "danger" : "warn"}`}>{r.payment_status}</span>
      ),
    },
  ];

  return (
    <div>
      {error && <div className="error-banner">{error}</div>}
      <DataTable
        title="Purchase Orders" columns={columns} rows={orders}
        addLabel="New Purchase Order" canAdd={canManage} onAdd={() => setShowModal(true)}
        selectedId={selected?.id} onSelectRow={setSelected}
        extraActions={canManage && <button className="btn success" onClick={markPaid}><CircleDollarSign size={14} /> Mark Paid</button>}
      />
      {showModal && (
        <PurchaseOrderModal suppliers={suppliers} items={items} onSave={handleSave} onClose={() => setShowModal(false)} />
      )}
    </div>
  );
}
