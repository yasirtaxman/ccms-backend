"use client";

import { useEffect, useMemo, useState } from "react";
import { Eye, Pencil, Plus, RefreshCw } from "lucide-react";
import { developmentApi } from "@/lib/development";
import { apiErrorMessage } from "@/lib/api";
import { usePermissions } from "@/hooks/usePermissions";
import type { DevelopmentIndicator } from "@/types/development";
import { cleanDisplay } from "./DevelopmentIndicatorField";

export function DevelopmentIndicatorsAdmin() {
  const { hasPermission } = usePermissions();
  const canManage = hasPermission("development.indicators.manage");
  const [rows, setRows] = useState<DevelopmentIndicator[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [inputType, setInputType] = useState("");
  const [status, setStatus] = useState("All");
  const [sensitive, setSensitive] = useState("All");
  const [required, setRequired] = useState("All");
  const [view, setView] = useState<DevelopmentIndicator | null>(null);
  const [edit, setEdit] = useState<DevelopmentIndicator | null>(null);

  const load = () => {
    setError("");
    return developmentApi.indicators(true).then((items) => {
      setRows(items);
      setError("");
    }).catch((e) => setError(apiErrorMessage(e)));
  };
  useEffect(() => { void load(); }, []);

  const categories = Array.from(new Set(rows.map((row) => row.category))).sort();
  const inputTypes = Array.from(new Set(rows.map((row) => row.input_type))).sort();
  const filtered = useMemo(() => rows.filter((row) => {
    const q = search.toLowerCase();
    return (!q || `${row.indicator_name} ${row.indicator_code}`.toLowerCase().includes(q)) && (!category || row.category === category) && (!inputType || row.input_type === inputType) && (status === "All" || (status === "Active" ? row.is_active : !row.is_active)) && (sensitive === "All" || (sensitive === "Sensitive" ? row.is_sensitive : !row.is_sensitive)) && (required === "All" || (required === "Required" ? row.is_required : !row.is_required));
  }), [rows, search, category, inputType, status, sensitive, required]);

  const toggle = async (row: DevelopmentIndicator) => {
    if (!confirm(`${row.is_active ? "Deactivate" : "Activate"} ${row.indicator_name}?`)) return;
    setError(""); setMessage("");
    try {
      row.is_active ? await developmentApi.deactivateIndicator(row.id) : await developmentApi.activateIndicator(row.id);
      setMessage(`${row.indicator_name} ${row.is_active ? "deactivated" : "activated"}.`);
      await load();
    } catch (e) { setError(apiErrorMessage(e)); }
  };

  return <div className="space-y-5">
    <header className="flex flex-col gap-3 xl:flex-row xl:items-end">
      <div className="flex-1"><p className="eyebrow">Administration</p><h1 className="page-title">Development Indicators</h1><p className="page-subtitle">System-defined observation indicators. Existing saved observations are not changed when labels/options are edited.</p></div>
      <button className="secondary-button" onClick={load}><RefreshCw size={16} />Refresh</button>
      {canManage && <button className="primary-button" onClick={() => setEdit({ id: 0, indicator_code: "", indicator_name: "", category: categories[0] || "Personal Hygiene & Cleanliness", description: "", input_type: "dropdown", options_json: [], is_required: false, is_active: true, is_sensitive: false, sort_order: rows.length + 1, created_at: "", updated_at: "" })}><Plus size={16} />Add Indicator</button>}
    </header>
    {error && <div className="notice-error">{error}</div>}
    {message && <div className="notice-success">{message}</div>}

    <section className="grid gap-3 md:grid-cols-5">
      <Card label="Total Indicators" value={rows.length} />
      <Card label="Active" value={rows.filter((row) => row.is_active).length} />
      <Card label="Inactive" value={rows.filter((row) => !row.is_active).length} />
      <Card label="Sensitive" value={rows.filter((row) => row.is_sensitive).length} />
      <Card label="Required" value={rows.filter((row) => row.is_required).length} />
    </section>

    <section className="panel">
      <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <label className="form-field"><span>Search</span><input className="field-control" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Name or code" /></label>
        <Select label="Category" value={category} onChange={setCategory} options={["", ...categories]} />
        <Select label="Input Type" value={inputType} onChange={setInputType} options={["", ...inputTypes]} />
        <Select label="Status" value={status} onChange={setStatus} options={["All", "Active", "Inactive"]} />
        <Select label="Sensitive" value={sensitive} onChange={setSensitive} options={["All", "Sensitive", "Non-sensitive"]} />
        <Select label="Required" value={required} onChange={setRequired} options={["All", "Required", "Optional"]} />
      </div>
    </section>

    <section className="panel">
      <div className="table-shell">
        <table className="data-table">
          <thead><tr><th>Indicator</th><th>Code</th><th>Category</th><th>Input Type</th><th>Required</th><th>Sensitive</th><th>Status</th><th>Options Preview</th><th>Actions</th></tr></thead>
          <tbody>{filtered.map((row) => <tr key={row.id}><td>{row.indicator_name}</td><td>{row.indicator_code}</td><td>{row.category}</td><td>{formatInputType(row.input_type)}</td><td>{row.is_required ? "Yes" : "No"}</td><td>{row.is_sensitive ? "Yes" : "No"}</td><td>{row.is_active ? "Active" : "Inactive"}</td><td>{Array.isArray(row.options_json) ? row.options_json.slice(0, 3).join(", ") : "Not recorded"}</td><td><div className="flex flex-wrap gap-1"><button className="icon-button" title="View" onClick={() => setView(row)}><Eye size={15} /></button>{canManage && <button className="icon-button" title="Edit" onClick={() => setEdit(row)}><Pencil size={15} /></button>}{canManage && <button className="secondary-button px-2 py-1 text-xs" onClick={() => toggle(row)}>{row.is_active ? "Deactivate" : "Activate"}</button>}</div></td></tr>)}</tbody>
        </table>
      </div>
    </section>
    {view && <Details row={view} onClose={() => setView(null)} />}
    {edit && <EditIndicator row={edit} onClose={() => setEdit(null)} onSaved={async () => { setEdit(null); setMessage("Indicator saved."); await load(); }} />}
  </div>;
}

function Card({ label, value }: { label: string; value: number }) { return <div className="metric-card"><div><p>{label}</p><strong>{value}</strong></div></div>; }
function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: string[] }) { return <label className="form-field"><span>{label}</span><select className="field-control" value={value} onChange={(e) => onChange(e.target.value)}>{options.map((option) => <option key={option} value={option}>{option || "All"}</option>)}</select></label>; }
function formatInputType(value: string) { return value === "rating_1_to_5" ? "Rating 1 to 5" : value.replaceAll("_", " "); }
function Details({ row, onClose }: { row: DevelopmentIndicator; onClose: () => void }) { return <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4"><section className="w-full max-w-2xl rounded-2xl bg-white p-6"><div className="flex justify-between gap-3"><h2 className="text-xl font-bold">{row.indicator_name}</h2><button className="secondary-button" onClick={onClose}>Close</button></div><dl className="mt-5 grid gap-3 sm:grid-cols-2">{Object.entries(row).map(([key, value]) => <div className="rounded-lg bg-slate-50 p-3" key={key}><dt className="text-xs font-semibold uppercase text-slate-400">{key.replaceAll("_", " ")}</dt><dd className="mt-1 break-words text-sm font-medium">{Array.isArray(value) ? value.join(", ") : cleanDisplay(value)}</dd></div>)}</dl></section></div>; }
function EditIndicator({ row, onClose, onSaved }: { row: DevelopmentIndicator; onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState(row);
  const [error, setError] = useState("");
  const save = async () => { setError(""); try { const options = typeof form.options_json === "string" ? String(form.options_json).split(",").map((x) => x.trim()).filter(Boolean) : form.options_json; row.id ? await developmentApi.updateIndicator(row.id, { indicator_name: form.indicator_name, description: form.description, options_json: options, is_required: form.is_required, is_sensitive: form.is_sensitive, sort_order: form.sort_order }) : await developmentApi.createIndicator({ ...form, options_json: options }); onSaved(); } catch (e) { setError(apiErrorMessage(e)); } };
  return <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4"><section className="w-full max-w-2xl rounded-2xl bg-white p-6"><div className="flex justify-between"><h2 className="text-xl font-bold">{row.id ? "Edit Indicator" : "Add Indicator"}</h2><button className="secondary-button" onClick={onClose}>Close</button></div>{error && <div className="notice-error mt-4">{error}</div>}<div className="mt-4 rounded-xl bg-amber-50 p-3 text-sm text-amber-800">Changing input type/options may affect future observations. Existing saved observations will not be changed.</div><div className="mt-5 grid gap-4 md:grid-cols-2"><label className="form-field"><span>Code</span><input className="field-control" value={form.indicator_code} disabled={Boolean(row.id)} onChange={(e) => setForm({ ...form, indicator_code: e.target.value })} /></label><label className="form-field"><span>Name</span><input className="field-control" value={form.indicator_name} onChange={(e) => setForm({ ...form, indicator_name: e.target.value })} /></label><label className="form-field"><span>Description</span><input className="field-control" value={form.description || ""} onChange={(e) => setForm({ ...form, description: e.target.value })} /></label><label className="form-field"><span>Options comma separated</span><input className="field-control" value={Array.isArray(form.options_json) ? form.options_json.join(", ") : ""} onChange={(e) => setForm({ ...form, options_json: e.target.value.split(",").map((x) => x.trim()).filter(Boolean) })} /></label><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_required} onChange={(e) => setForm({ ...form, is_required: e.target.checked })} />Required</label><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_sensitive} onChange={(e) => setForm({ ...form, is_sensitive: e.target.checked })} />Sensitive</label></div><div className="mt-6 flex justify-end gap-2"><button className="secondary-button" onClick={onClose}>Cancel</button><button className="primary-button" onClick={save}>Save Indicator</button></div></section></div>;
}
