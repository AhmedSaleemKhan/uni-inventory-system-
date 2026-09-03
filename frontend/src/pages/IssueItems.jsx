import { useEffect, useState } from "react";
import { Printer } from "lucide-react";
import { api, downloadBlob } from "../api/client";
import { useAuth, hasPermission } from "../context/AuthContext";
import DataTable from "../components/DataTable";
import FormModal from "../components/FormModal";

export default function IssueItems() {
  const { user } = useAuth();
  const canManage = hasPermission(user.role, "issue_items");

  const [records, setRecords] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState("");
  const [printing, setPrinting] = useState(false);

  function load() {
    api.get("/issues").then(setRecords).catch((e) => setError(e.message));
    api.get("/teachers").then((t) => setTeachers(t.map((x) => x.name))).catch(() => {});
    api.get("/inventory").then((i) => setItems(i.filter((x) => x.current_quantity > 0).map((x) => x.name))).catch(() => {});
  }
  useEffect(load, []);

  const fields = [
    { key: "teacher", label: "Teacher", kind: "select", options: teachers, required: true },
    { key: "item", label: "Item", kind: "select", options: items, required: true },
    { key: "quantity", label: "Quantity", kind: "number", min: 1, max: 100000, default: 1 },
    { key: "department", label: "Department" },
    { key: "remarks", label: "Remarks", kind: "textarea" },
    { key: "return_required", label: "Return Required", kind: "checkbox" },
    { key: "expected_return_date", label: "Expected Return Date", kind: "date" },
  ];

  async function handleSave(values) {
    await api.post("/issues", values);
    setShowModal(false);
    load();
  }

  async function printRequisition() {
    if (!selected) {
      alert("Please select an issue record first.");
      return;
    }
    setPrinting(true);
    try {
      const blob = await api.file(`/issues/${selected.id}/requisition`);
      downloadBlob(blob, `internal_requisition_${selected.id}.pdf`);
    } catch (e) {
      alert(e.message);
    } finally {
      setPrinting(false);
    }
  }

  const columns = [
    { key: "id", label: "ID" }, { key: "teacher", label: "Teacher" }, { key: "item", label: "Item" },
    { key: "quantity", label: "Qty" }, { key: "issue_date", label: "Issue Date" }, { key: "department", label: "Department" },
    { key: "return_required", label: "Return Required", render: (r) => (r.return_required ? "Yes" : "No") },
    { key: "expected_return_date", label: "Expected Return", render: (r) => r.expected_return_date || "-" },
    {
      key: "status", label: "Status", render: (r) => (
        <span className={`pill ${r.status === "Overdue" ? "danger" : r.status === "Returned" ? "success" : ""}`}>{r.status}</span>
      ),
    },
  ];

  return (
    <div>
      {error && <div className="error-banner">{error}</div>}
      <DataTable
        title="Inventory Issue" columns={columns} rows={records}
        addLabel="Issue Item" canAdd={canManage} onAdd={() => setShowModal(true)}
        filterOptions={["Issued", "Returned", "Overdue"]} filterKey="status"
        selectedId={selected?.id} onSelectRow={setSelected}
        extraActions={(
          <button className="btn secondary" disabled={printing} onClick={printRequisition}>
            <Printer size={14} /> {printing ? "Generating..." : "Print Requisition"}
          </button>
        )}
      />
      {showModal && (
        <FormModal title="Issue Item" fields={fields} onSave={handleSave} onClose={() => setShowModal(false)} />
      )}
    </div>
  );
}
