import { useEffect, useState } from "react";
import { FileText, FileSpreadsheet, FileDown } from "lucide-react";
import { api, downloadBlob } from "../api/client";

const REPORT_TYPES = [
  "Inventory Report", "Low Stock Report", "Teacher Report", "Printing Report",
  "Issue Report", "Return Report", "Pending Documents Report",
];

export default function Reports() {
  const [reportType, setReportType] = useState(REPORT_TYPES[0]);
  const [data, setData] = useState({ headers: [], rows: [] });
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState("");

  useEffect(() => {
    api.get(`/reports/${encodeURIComponent(reportType)}`).then(setData).catch((e) => setError(e.message));
  }, [reportType]);

  async function handleExport(fmt) {
    setExporting(fmt);
    try {
      const blob = await api.file(`/reports/${encodeURIComponent(reportType)}/export/${fmt}`);
      downloadBlob(blob, `${reportType.toLowerCase().replace(/ /g, "_")}.${fmt}`);
    } catch (e) {
      alert(e.message);
    } finally {
      setExporting("");
    }
  }

  return (
    <div>
      <h1 className="page-title-heading">Reports Center</h1>
      <div className="toolbar">
        <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Report Type:</span>
        <select value={reportType} onChange={(e) => setReportType(e.target.value)}>
          {REPORT_TYPES.map((r) => <option key={r}>{r}</option>)}
        </select>
        <div className="spacer" />
        <button className="btn secondary" disabled={!!exporting} onClick={() => handleExport("pdf")}>
          <FileText size={14} /> {exporting === "pdf" ? "Exporting..." : "Export PDF"}
        </button>
        <button className="btn secondary" disabled={!!exporting} onClick={() => handleExport("xlsx")}>
          <FileSpreadsheet size={14} /> {exporting === "xlsx" ? "Exporting..." : "Export Excel"}
        </button>
        <button className="btn secondary" disabled={!!exporting} onClick={() => handleExport("csv")}>
          <FileDown size={14} /> {exporting === "csv" ? "Exporting..." : "Export CSV"}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="table-wrap">
        <table className="data-table">
          <thead><tr>{data.headers.map((h) => <th key={h}>{h}</th>)}</tr></thead>
          <tbody>
            {data.rows.length === 0 && (
              <tr><td colSpan={data.headers.length || 1}><div className="empty-state">No records found.</div></td></tr>
            )}
            {data.rows.map((row, i) => (
              <tr key={i}>{row.map((cell, j) => <td key={j}>{cell}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={{ marginTop: 10, fontSize: 12.5, color: "var(--text-muted)" }}>{data.rows.length} records</div>
    </div>
  );
}
