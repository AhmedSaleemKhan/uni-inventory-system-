import { useMemo, useState } from "react";

/**
 * Generic "title + search + filter + add button + table" page shell -
 * the React equivalent of the desktop app's TablePage widget.
 */
export default function DataTable({
  title, columns, rows, addLabel, onAdd, canAdd = true,
  filterOptions, filterKey, extraActions, selectedId, onSelectRow,
}) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("All");

  const filtered = useMemo(() => {
    return rows.filter((row) => {
      const matchesQuery = !query || columns.some((c) =>
        String(row[c.key] ?? "").toLowerCase().includes(query.toLowerCase())
      );
      const matchesFilter = filter === "All" || !filterKey || String(row[filterKey]) === filter;
      return matchesQuery && matchesFilter;
    });
  }, [rows, query, filter, columns, filterKey]);

  return (
    <div>
      <div className="toolbar">
        <h1 className="page-title-heading" style={{ marginBottom: 0, marginRight: 8 }}>{title}</h1>
        <div className="spacer" />
        {extraActions}
        <input type="text" placeholder="Search..." value={query} onChange={(e) => setQuery(e.target.value)} />
        {filterOptions && (
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option>All</option>
            {filterOptions.map((o) => <option key={o}>{o}</option>)}
          </select>
        )}
        {canAdd && onAdd && <button className="btn" onClick={onAdd}>{addLabel || "+ Add New"}</button>}
      </div>

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>{columns.map((c) => <th key={c.key}>{c.label}</th>)}</tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr><td colSpan={columns.length}><div className="empty-state">No records found.</div></td></tr>
            )}
            {filtered.map((row) => (
              <tr
                key={row.id}
                className={selectedId === row.id ? "selected" : ""}
                onClick={() => onSelectRow && onSelectRow(row)}
                style={onSelectRow ? { cursor: "pointer" } : undefined}
              >
                {columns.map((c) => (
                  <td key={c.key}>{c.render ? c.render(row) : row[c.key]}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
