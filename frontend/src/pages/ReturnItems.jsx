import { useEffect, useState } from "react";
import { api } from "../api/client";
import DataTable from "../components/DataTable";
import FormModal from "../components/FormModal";

export default function ReturnItems() {
  const [records, setRecords] = useState([]);
  const [selected, setSelected] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState("");

  function load() {
    api.get("/returns").then((r) => setRecords(r.map((x) => ({ ...x, id: x.issue_id })))).catch((e) => setError(e.message));
  }
  useEffect(load, []);

  const fields = [
    { key: "returned_quantity", label: "Returned Quantity", kind: "number", min: 1, max: 100000, default: selected?.quantity || 1 },
    { key: "condition", label: "Condition", kind: "select", options: ["Good", "Damaged", "Partially Used"] },
    { key: "remarks", label: "Remarks", kind: "textarea" },
  ];

  function openReturn() {
    if (!selected) {
      alert("Select an 'Issued' or 'Overdue' record to return.");
      return;
    }
    if (selected.status === "Returned") {
      alert("This record is already returned.");
      return;
    }
    setShowModal(true);
  }

  async function handleSave(values) {
    const result = await api.post(`/returns/${selected.id}`, values);
    setShowModal(false);
    setSelected(null);
    load();
    if (result.is_late) alert("Return recorded and stock updated. (Late return)");
  }

  const columns = [
    { key: "id", label: "Issue ID" }, { key: "teacher", label: "Teacher" }, { key: "item", label: "Item" },
    { key: "quantity", label: "Qty Issued" }, { key: "issue_date", label: "Issue Date" },
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
        title="Return Management" columns={columns} rows={records}
        addLabel="Record Return" onAdd={openReturn}
        filterOptions={["Issued", "Returned", "Overdue"]} filterKey="status"
        selectedId={selected?.id} onSelectRow={setSelected}
      />
      {showModal && (
        <FormModal title="Record Return" fields={fields} onSave={handleSave} onClose={() => setShowModal(false)} />
      )}
    </div>
  );
}
