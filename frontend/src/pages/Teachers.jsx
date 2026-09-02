import { useEffect, useState } from "react";
import { Pencil, Trash2 } from "lucide-react";
import { api } from "../api/client";
import { useAuth, hasPermission } from "../context/AuthContext";
import DataTable from "../components/DataTable";
import FormModal from "../components/FormModal";

const DEPARTMENTS = [
  "Computer Science", "Software Engineering", "Electrical Engineering",
  "Mechanical Engineering", "Civil Engineering", "Business Administration",
  "Applied Physics", "Mathematics", "English", "Humanities",
];
const DESIGNATIONS = ["Lecturer", "Assistant Professor", "Associate Professor", "Professor", "Visiting Faculty"];
const STATUSES = ["Active", "On Leave", "Retired"];

export default function Teachers() {
  const { user } = useAuth();
  const canManage = hasPermission(user.role, "manage_teachers");

  const [teachers, setTeachers] = useState([]);
  const [editing, setEditing] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState("");

  function load() {
    api.get("/teachers").then(setTeachers).catch((e) => setError(e.message));
  }
  useEffect(load, []);

  const fields = [
    { key: "name", label: "Full Name", required: true },
    { key: "department", label: "Department", kind: "select", options: DEPARTMENTS, required: true },
    { key: "designation", label: "Designation", kind: "select", options: DESIGNATIONS },
    { key: "phone", label: "Phone" },
    { key: "email", label: "Email" },
    { key: "office_number", label: "Office Number" },
    { key: "assigned_courses", label: "Assigned Courses (comma separated)", kind: "textarea" },
    { key: "status", label: "Status", kind: "select", options: STATUSES },
  ];

  async function handleSave(values) {
    if (editing) await api.put(`/teachers/${editing.id}`, values);
    else await api.post("/teachers", values);
    setShowModal(false);
    setEditing(null);
    load();
  }

  async function handleDelete() {
    if (!selected || !confirm("Delete this teacher record permanently?")) return;
    try {
      await api.del(`/teachers/${selected.id}`);
      setSelected(null);
      load();
    } catch (e) {
      alert(e.message);
    }
  }

  const columns = [
    { key: "id", label: "ID" }, { key: "employee_id", label: "Employee ID" }, { key: "name", label: "Name" },
    { key: "department", label: "Department" }, { key: "designation", label: "Designation" },
    { key: "phone", label: "Phone" }, { key: "email", label: "Email" }, { key: "office_number", label: "Office" },
    { key: "status", label: "Status" },
  ];

  return (
    <div>
      {error && <div className="error-banner">{error}</div>}
      <DataTable
        title="Teacher Management" columns={columns} rows={teachers}
        addLabel="Add Teacher" canAdd={canManage}
        onAdd={() => { setEditing(null); setShowModal(true); }}
        filterOptions={DEPARTMENTS} filterKey="department"
        selectedId={selected?.id} onSelectRow={setSelected}
        extraActions={canManage && (
          <>
            <button className="btn secondary" disabled={!selected} onClick={() => { setEditing(selected); setShowModal(true); }}><Pencil size={14} /> Edit Selected</button>
            <button className="btn danger" disabled={!selected} onClick={handleDelete}><Trash2 size={14} /> Delete Selected</button>
          </>
        )}
      />
      {showModal && (
        <FormModal title={editing ? "Edit Teacher" : "Add Teacher"} fields={fields} initial={editing}
          onSave={handleSave} onClose={() => { setShowModal(false); setEditing(null); }} />
      )}
    </div>
  );
}
