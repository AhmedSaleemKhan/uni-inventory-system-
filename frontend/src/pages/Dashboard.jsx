import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import StatCard from "../components/StatCard";

function MiniBarChart({ labels, issueCounts, printCounts }) {
  const max = Math.max(1, ...issueCounts, ...printCounts);
  const width = 560, height = 200, padding = 28, chartH = height - padding * 2;
  const groupWidth = (width - padding * 2) / labels.length;
  const barWidth = groupWidth * 0.32;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} width="100%" style={{ maxWidth: 560 }}>
      <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="var(--border)" />
      {labels.map((label, i) => {
        const cx = padding + groupWidth * i + groupWidth / 2;
        const issueH = (issueCounts[i] / max) * chartH;
        const printH = (printCounts[i] / max) * chartH;
        return (
          <g key={label}>
            <rect x={cx - barWidth - 2} y={height - padding - issueH} width={barWidth} height={issueH} fill="#028090" rx="2" />
            <rect x={cx + 2} y={height - padding - printH} width={barWidth} height={printH} fill="#F0A202" rx="2" />
            <text x={cx} y={height - padding + 14} textAnchor="middle" fontSize="10" fill="var(--text-muted)">{label}</text>
          </g>
        );
      })}
      <g transform={`translate(${width - 130}, 10)`} fontSize="10" fill="var(--text-muted)">
        <rect width="9" height="9" fill="#028090" />
        <text x="13" y="8.5">Issues</text>
        <rect x="60" width="9" height="9" fill="#F0A202" />
        <text x="73" y="8.5">Printing</text>
      </g>
    </svg>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/dashboard").then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="error-banner">{error}</div>;
  if (!data) return <div className="empty-state">Loading dashboard...</div>;

  return (
    <div>
      <h1 className="page-title-heading">Welcome back, {user.full_name}</h1>

      <div className="stat-grid">
        <StatCard label="Total Inventory Items" value={data.total_items} color="#028090" />
        <StatCard label="Available Stock (units)" value={data.available_stock} color="#2E8B57" />
        <StatCard label="Low Stock Items" value={data.low_stock} color="#F0A202" />
        <StatCard label="Out of Stock Items" value={data.out_of_stock} color="#D64545" />
        <StatCard label="Today's Issued Items" value={data.today_issued} color="#028090" />
        <StatCard label="Today's Returned Items" value={data.today_returned} color="#028090" />
        <StatCard label="Today's Printing Jobs" value={data.today_printing} color="#028090" />
        <StatCard label="Pending Documents" value={data.pending_docs} color="#F0A202" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16, marginBottom: 20 }}>
        <div className="card" style={{ padding: 16 }}>
          <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 8 }}>Monthly Activity Overview</div>
          <MiniBarChart labels={data.monthly_labels} issueCounts={data.monthly_issue_counts} printCounts={data.monthly_print_counts} />
        </div>
        <div className="card" style={{ padding: 16, maxHeight: 260, overflowY: "auto" }}>
          <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 8 }}>Notifications &amp; Alerts</div>
          {data.notifications.map((n, i) => (
            <div key={i} style={{ fontSize: 12.5, padding: "6px 0", borderTop: i > 0 ? "1px solid var(--border)" : "none" }}>{n}</div>
          ))}
        </div>
      </div>

      <div className="card" style={{ padding: 16 }}>
        <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 8 }}>Recent Activities</div>
        {data.recent_activity.map((a, i) => (
          <div key={i} style={{ fontSize: 12.5, padding: "6px 0", borderTop: i > 0 ? "1px solid var(--border)" : "none" }}>{a}</div>
        ))}
      </div>
    </div>
  );
}
