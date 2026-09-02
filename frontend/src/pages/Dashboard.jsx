import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import StatCard from "../components/StatCard";

/**
 * Grouped bar chart, Issues vs Printing per month.
 * Colors are the dataviz-skill-validated categorical pair (aqua/yellow,
 * OKLCH-checked for CVD separation and contrast in both themes) rather
 * than picked by eye. Gridline value labels give the WCAG-contrast
 * "visible labels" relief the palette check requires; the hover/focus
 * tooltip surfaces both series' exact values per Interaction spec
 * ("one tooltip, every series").
 */
function MiniBarChart({ labels, issueCounts, printCounts }) {
  const [hover, setHover] = useState(null);

  const width = 560, height = 220, padding = { top: 14, right: 12, bottom: 26, left: 30 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;
  const groupWidth = chartW / labels.length;
  const barWidth = Math.min(26, groupWidth * 0.3);

  const rawMax = Math.max(1, ...issueCounts, ...printCounts);
  const niceMax = useMemo(() => {
    const magnitude = Math.pow(10, Math.floor(Math.log10(rawMax || 1)));
    const step = Math.ceil(rawMax / magnitude) * magnitude;
    return step || 1;
  }, [rawMax]);
  const gridSteps = 4;

  const yFor = (v) => padding.top + chartH - (v / niceMax) * chartH;

  return (
    <div style={{ position: "relative" }}>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" style={{ maxWidth: 560, display: "block", overflow: "visible" }}>
        {Array.from({ length: gridSteps + 1 }, (_, i) => {
          const v = (niceMax / gridSteps) * i;
          const y = yFor(v);
          return (
            <g key={i}>
              <line x1={padding.left} y1={y} x2={width - padding.right} y2={y} stroke="var(--border)" strokeWidth="1" />
              <text x={padding.left - 6} y={y + 3} textAnchor="end" fontSize="9" fill="var(--text-muted)">{Math.round(v)}</text>
            </g>
          );
        })}

        {labels.map((label, i) => {
          const cx = padding.left + groupWidth * i + groupWidth / 2;
          const issueV = issueCounts[i];
          const printV = printCounts[i];
          const issueY = yFor(issueV);
          const printY = yFor(printV);
          const baseline = yFor(0);
          const isHovered = hover === i;

          return (
            <g
              key={label}
              tabIndex={0}
              role="img"
              aria-label={`${label}: ${issueV} issues, ${printV} printing jobs`}
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
              onFocus={() => setHover(i)}
              onBlur={() => setHover(null)}
              style={{ cursor: "pointer", outline: "none" }}
            >
              <rect x={padding.left + groupWidth * i} y={padding.top} width={groupWidth} height={chartH} fill="transparent" />
              <rect
                x={cx - barWidth - 2} y={issueY} width={barWidth} height={Math.max(0, baseline - issueY)}
                fill="var(--chart-issues)" rx="3" opacity={isHovered ? 1 : 0.88}
                style={{ transition: "opacity 0.12s" }}
              />
              <rect
                x={cx + 2} y={printY} width={barWidth} height={Math.max(0, baseline - printY)}
                fill="var(--chart-printing)" rx="3" opacity={isHovered ? 1 : 0.88}
                style={{ transition: "opacity 0.12s" }}
              />
              {isHovered && (
                <rect x={padding.left + groupWidth * i} y={padding.top} width={groupWidth} height={chartH}
                      fill="var(--text)" opacity="0.045" />
              )}
              <text x={cx} y={height - padding.bottom + 14} textAnchor="middle" fontSize="10" fill="var(--text-muted)">{label}</text>
            </g>
          );
        })}
      </svg>

      <div style={{ display: "flex", gap: 16, marginTop: 6, fontSize: 11, color: "var(--text-muted)" }}>
        <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
          <span style={{ width: 10, height: 10, borderRadius: 2, background: "var(--chart-issues)", display: "inline-block" }} /> Issues
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
          <span style={{ width: 10, height: 10, borderRadius: 2, background: "var(--chart-printing)", display: "inline-block" }} /> Printing
        </span>
      </div>

      {hover !== null && (
        <div
          style={{
            position: "absolute",
            left: `${((padding.left + groupWidth * hover + groupWidth / 2) / width) * 100}%`,
            top: `${(Math.min(yFor(issueCounts[hover]), yFor(printCounts[hover])) / height) * 100}%`,
            transform: "translate(-50%, -110%)",
            background: "var(--primary-dark)",
            color: "#fff",
            borderRadius: 8,
            padding: "8px 10px",
            fontSize: 11.5,
            boxShadow: "var(--shadow-md)",
            pointerEvents: "none",
            whiteSpace: "nowrap",
            zIndex: 5,
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: 4 }}>{labels[hover]}</div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ width: 8, height: 2, background: "var(--chart-issues)", display: "inline-block" }} />
            Issues: <strong>{issueCounts[hover]}</strong>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ width: 8, height: 2, background: "var(--chart-printing)", display: "inline-block" }} />
            Printing: <strong>{printCounts[hover]}</strong>
          </div>
        </div>
      )}
    </div>
  );
}

const NOTIF_STYLE = {
  OutOfStock: { border: "var(--danger)", icon: "●" },
  LowStock: { border: "var(--accent)", icon: "▲" },
};

const ACTIVITY_STYLE = [
  { match: /^Issued/, border: "var(--chart-issues)" },
  { match: /^Printing/, border: "var(--chart-printing)" },
  { match: /^Document/, border: "var(--primary)" },
];

function listItemStyle(borderColor, i) {
  return {
    fontSize: 12.5,
    padding: "8px 10px",
    borderTop: i > 0 ? "1px solid var(--border)" : "none",
    borderLeft: `3px solid ${borderColor}`,
    marginLeft: -1,
    transition: "background 0.12s",
  };
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
        <StatCard label="Low Stock Items" value={data.low_stock} color="#A3690A" />
        <StatCard label="Out of Stock Items" value={data.out_of_stock} color="#D64545" />
        <StatCard label="Today's Issued Items" value={data.today_issued} color="#028090" />
        <StatCard label="Today's Returned Items" value={data.today_returned} color="#028090" />
        <StatCard label="Today's Printing Jobs" value={data.today_printing} color="#028090" />
        <StatCard label="Pending Documents" value={data.pending_docs} color="#A3690A" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16, marginBottom: 20 }}>
        <div className="card" style={{ padding: 16 }}>
          <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 8 }}>Monthly Activity Overview</div>
          <MiniBarChart labels={data.monthly_labels} issueCounts={data.monthly_issue_counts} printCounts={data.monthly_print_counts} />
        </div>
        <div className="card" style={{ padding: 4, maxHeight: 280, overflowY: "auto" }}>
          <div style={{ fontWeight: 600, fontSize: 14, padding: "12px 12px 8px" }}>Notifications &amp; Alerts</div>
          {data.notifications.map((n, i) => {
            const style = n.toLowerCase().includes("out of stock") ? NOTIF_STYLE.OutOfStock : NOTIF_STYLE.LowStock;
            return (
              <div key={i} style={listItemStyle(style.border, i)}>
                <span style={{ color: style.border, marginRight: 6 }}>{style.icon}</span>{n}
              </div>
            );
          })}
        </div>
      </div>

      <div className="card" style={{ padding: 4 }}>
        <div style={{ fontWeight: 600, fontSize: 14, padding: "12px 12px 8px" }}>Recent Activities</div>
        {data.recent_activity.map((a, i) => {
          const found = ACTIVITY_STYLE.find((s) => s.match.test(a));
          return (
            <div key={i} style={listItemStyle(found ? found.border : "var(--border)", i)}>{a}</div>
          );
        })}
      </div>
    </div>
  );
}
