import { useState } from "react";
import { X, Check } from "lucide-react";

/**
 * Generic add/edit form modal, driven by a field-spec list - the same
 * pattern as the desktop app's FormDialog/FieldSpec, translated to React.
 * field: { key, label, kind: 'text'|'textarea'|'select'|'date'|'number'|'checkbox', options, required, default }
 */
export default function FormModal({ title, fields, initial, onSave, onClose }) {
  const [values, setValues] = useState(() => {
    const v = {};
    for (const f of fields) {
      // A <select> with no blank placeholder option always shows its first
      // option as selected in the browser, even if the bound value is "".
      // Defaulting to "" here would then silently submit an empty string
      // instead of the option the user sees highlighted - so a new record's
      // untouched dropdown must default to that first real option instead.
      v[f.key] = initial?.[f.key] ?? f.default ?? (
        f.kind === "checkbox" ? false :
        f.kind === "number" ? 0 :
        f.kind === "select" ? (f.options?.[0] ?? "") :
        ""
      );
    }
    return v;
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function set(key, val) {
    setValues((v) => ({ ...v, [key]: val }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    for (const f of fields) {
      if (f.required && !values[f.key] && values[f.key] !== 0) {
        setError(`'${f.label}' is required.`);
        return;
      }
    }
    setError("");
    setSaving(true);
    // An untouched optional date field is "" - the backend's Optional[date]
    // accepts null but rejects an empty string as an invalid date, so send
    // null instead of leaving it as the input's empty-string default.
    const payload = { ...values };
    for (const f of fields) {
      if (f.kind === "date" && payload[f.key] === "") payload[f.key] = null;
    }
    try {
      await onSave(payload);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <h2>{title}</h2>
        {error && <div className="error-banner">{error}</div>}
        <form onSubmit={handleSubmit}>
          {fields.map((f) => (
            <div className="field" key={f.key}>
              <label>
                {f.label}
                {f.required ? " *" : ""}
              </label>
              {f.kind === "select" ? (
                <select value={values[f.key]} onChange={(e) => set(f.key, e.target.value)}>
                  {(f.options || []).map((o) => (
                    <option key={o} value={o}>{o}</option>
                  ))}
                </select>
              ) : f.kind === "textarea" ? (
                <textarea rows={3} value={values[f.key]} onChange={(e) => set(f.key, e.target.value)} />
              ) : f.kind === "date" ? (
                <input type="date" value={values[f.key] || ""} onChange={(e) => set(f.key, e.target.value)} />
              ) : f.kind === "number" ? (
                <input
                  type="number"
                  min={f.min ?? 0}
                  max={f.max ?? 1000000}
                  step={f.step ?? 1}
                  value={values[f.key]}
                  onChange={(e) => set(f.key, f.step ? parseFloat(e.target.value) : parseInt(e.target.value || "0", 10))}
                />
              ) : f.kind === "checkbox" ? (
                <input type="checkbox" checked={!!values[f.key]} onChange={(e) => set(f.key, e.target.checked)} style={{ width: 18, height: 18 }} />
              ) : (
                <input type="text" value={values[f.key]} onChange={(e) => set(f.key, e.target.value)} />
              )}
            </div>
          ))}
          <div className="modal-actions">
            <button type="button" className="btn secondary" onClick={onClose}><X size={14} /> Cancel</button>
            <button type="submit" className="btn" disabled={saving}><Check size={14} /> {saving ? "Saving..." : "Save"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
