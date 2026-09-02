import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth, hasPermission } from "../context/AuthContext";
import DataTable from "../components/DataTable";
import FormModal from "../components/FormModal";

export default function Printing() {
  const { user } = useAuth();
  const canManage = hasPermission(user.role, "manage_printing");

  const [records, setRecords] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState("");

  function load() {
    api.get("/printing").then(setRecords).catch((e) => setError(e.message));
    api.get("/teachers").then((t) => setTeachers(t.map((x) => x.name))).catch(() => {});
  }
  useEffect(load, []);

  const fields = [
    { key: "teacher", label: "Teacher", kind: "select", options: ["", ...teachers] },
    { key: "department", label: "Department" },
    { key: "course", label: "Course" },
    { key: "document_name", label: "Document Name", required: true },
    { key: "color_mode", label: "Color Mode", kind: "select", options: ["Black & White", "Color"] },
    { key: "side_mode", label: "Side Mode", kind: "select", options: ["Single Side", "Double Side"] },
    { key: "pages", label: "Pages", kind: "number", min: 1, max: 10000, default: 1 },
    { key: "copies", label: "Copies", kind: "number", min: 1, max: 10000, default: 1 },
  ];

  async function handleSave(values) {
    const result = await api.post("/printing", values);
    setShowModal(false);
    load();
    alert(`Printing job recorded. Cost: Rs. ${result.cost.toFixed(2)}`);
  }

  const columns = [
    { key: "id", label: "ID" }, { key: "teacher_name", label: "Teacher" }, { key: "department", label: "Department" },
    { key: "course", label: "Course" }, { key: "document_name", label: "Document" }, { key: "color_mode", label: "Mode" },
    { key: "side_mode", label: "Sides" }, { key: "pages", label: "Pages" }, { key: "copies", label: "Copies" },
    { key: "cost", label: "Cost", render: (r) => `Rs. ${r.cost.toFixed(2)}` },
    { key: "print_date", label: "Date" }, { key: "status", label: "Status" },
  ];

  return (
    <div>
      {error && <div className="error-banner">{error}</div>}
      <DataTable
        title="Printing Management" columns={columns} rows={records}
        addLabel="New Printing Job" canAdd={canManage} onAdd={() => setShowModal(true)}
        filterOptions={["Black & White", "Color"]} filterKey="color_mode"
      />
      {showModal && (
        <FormModal title="New Printing Job" fields={fields} onSave={handleSave} onClose={() => setShowModal(false)} />
      )}
    </div>
  );
}
