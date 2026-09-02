export default function StatCard({ label, value, color = "#028090" }) {
  return (
    <div className="stat-card">
      <div className="bar" style={{ background: color }} />
      <div className="value" style={{ color }}>{value}</div>
      <div className="label">{label}</div>
    </div>
  );
}
