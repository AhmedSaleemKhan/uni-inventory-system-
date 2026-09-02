import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth, hasPermission } from "../context/AuthContext";
import DataTable from "../components/DataTable";
import FormModal from "../components/FormModal";

const DOCUMENT_TYPES = [
  "Internship Files", "TA Files", "Attendance Sheets", "Official Letters",
  "Purchase Requests", "Exam Files", "Course Files", "Office Files", "Teacher Documents",
];
const STATUSES = ["Pending", "Received", "Approved", "Rejected"];

export default function Documents() {
  const { user } = useAuth();
  const canManage = hasPermission(user.role, "manage_documents");

  const [docs, setDocs] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [selected, setSelected] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState("");

  function load() {
    api.get("/documents").then(setDocs).catch((e) => setError(e.message));
    api.get("/teachers").then((t) => setTeachers(t.map((x) => x.name))).catch(() => {});
  }
  useEffect(load, []);

  const fields = [
    { key: "document_type", label: "Document Type", kind: "select", options: DOCUMENT_TYPES, required: true },
    { key: "title", label: "Title", required: true },
    { key: "department", label: "Department" },
    { key: "submitted_by", label: "Submitted By", kind: "select", options: ["", ...teachers] },
    { key: "status", label: "Status", kind: "select", options: STATUSES },
    { key: "remarks", label: "Remarks", kind: "textarea" },
  ];

  async function handleSave(values) {
    await api.post("/documents", values);
    setShowModal(false);
    load();
  }

  async function updateStatus(newStatus) {
    if (!selected) {
      alert("Please select a document record.");
      return;
    }
    await api.post(`/documents/${selected.id}/status/${newStatus}`);
    setSelected(null);
    load();
  }

  const columns = [
    { key: "id", label: "ID" }, { key: "document_type", label: "Type" }, { key: "title", label: "Title" },
    { key: "department", label: "Department" }, { key: "submitted_by", label: "Submitted By" },
    { key: "received_date", label: "Received Date" },
    {
      key: "status", label: "Status", render: (r) => (
        <span className={`pill ${r.status === "Approved" ? "success" : r.status === "Rejected" ? "danger" : r.status === "Pending" ? "warn" : ""}`}>{r.status}</span>
      ),
    },
  ];

  return (
    <div>
      {error && <div className="error-banner">{error}</div>}
      <DataTable
        title="Document Tracking" columns={columns} rows={docs}
        addLabel="+ Add Document" canAdd={canManage} onAdd={() => setShowModal(true)}
        filterOptions={STATUSES} filterKey="status"
        selectedId={selected?.id} onSelectRow={setSelected}
        extraActions={canManage && (
          <>
            <button className="btn secondary" onClick={() => updateStatus("Received")}>Mark Received</button>
            <button className="btn success" onClick={() => updateStatus("Approved")}>Approve Selected</button>
            <button className="btn danger" onClick={() => updateStatus("Rejected")}>Reject Selected</button>
          </>
        )}
      />
      {showModal && (
        <FormModal title="Add Document Record" fields={fields} onSave={handleSave} onClose={() => setShowModal(false)} />
      )}
    </div>
  );
}
