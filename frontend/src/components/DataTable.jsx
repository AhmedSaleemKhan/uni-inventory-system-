import { useEffect, useMemo, useState } from "react";
import { Plus, Search } from "lucide-react";

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100, 200];

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
  const [pageSize, setPageSize] = useState(25);
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    return rows.filter((row) => {
      const matchesQuery = !query || columns.some((c) =>
        String(row[c.key] ?? "").toLowerCase().includes(query.toLowerCase())
      );
      const matchesFilter = filter === "All" || !filterKey || String(row[filterKey]) === filter;
      return matchesQuery && matchesFilter;
    });
  }, [rows, query, filter, columns, filterKey]);

  // A new search/filter/page-size can easily leave the current page past
  // the end of the (now smaller) result set - reset to page 1 instead of
  // rendering an empty page.
  useEffect(() => { setPage(1); }, [query, filter, pageSize]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const safePage = Math.min(page, totalPages);
  const startIdx = filtered.length === 0 ? 0 : (safePage - 1) * pageSize + 1;
  const endIdx = Math.min(safePage * pageSize, filtered.length);
  const pageRows = filtered.slice((safePage - 1) * pageSize, safePage * pageSize);

  return (
    <div>
      <div className="toolbar">
        <h1 className="page-title-heading" style={{ marginBottom: 0, marginRight: 8 }}>{title}</h1>
        <div className="spacer" />
        {extraActions}
        <div className="search-wrap">
          <Search size={14} />
          <input type="text" placeholder="Search..." value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>
        {filterOptions && (
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option>All</option>
            {filterOptions.map((o) => <option key={o}>{o}</option>)}
          </select>
        )}
        {canAdd && onAdd && <button className="btn" onClick={onAdd}><Plus size={15} strokeWidth={2.5} />{addLabel || "Add New"}</button>}
      </div>

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>{columns.map((c) => <th key={c.key}>{c.label}</th>)}</tr>
          </thead>
          <tbody>
            {pageRows.length === 0 && (
              <tr><td colSpan={columns.length}><div className="empty-state">No records found.</div></td></tr>
            )}
            {pageRows.map((row) => (
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
      <div className="table-footer">
        <div className="page-size-control">
          Display
          <select value={pageSize} onChange={(e) => setPageSize(Number(e.target.value))}>
            {PAGE_SIZE_OPTIONS.map((n) => <option key={n} value={n}>{n}</option>)}
          </select>
          records
        </div>
        <div className="pagination-controls">
          <span>
            {filtered.length === 0
              ? "No entries"
              : `Showing ${startIdx} to ${endIdx} of ${filtered.length} entries`}
          </span>
          <div className="pagination-buttons">
            <button disabled={safePage <= 1} onClick={() => setPage(safePage - 1)}>Previous</button>
            <button disabled={safePage >= totalPages} onClick={() => setPage(safePage + 1)}>Next</button>
          </div>
        </div>
      </div>
    </div>
  );
}
