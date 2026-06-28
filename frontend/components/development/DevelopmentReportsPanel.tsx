"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Download, Play, RefreshCw } from "lucide-react";
import { downloadAuthenticated } from "@/lib/children";
import { developmentApi } from "@/lib/development";
import { apiErrorMessage } from "@/lib/api";
import { cleanDisplay } from "./DevelopmentIndicatorField";

export function DevelopmentReportsPanel() {
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [child, setChild] = useState("");
  const [reviewStatus, setReviewStatus] = useState("");
  const [frequency, setFrequency] = useState("");
  const [district, setDistrict] = useState("");
  const [dashboard, setDashboard] = useState<Record<string, number>>({});
  const [missing, setMissing] = useState<Record<string, unknown>[]>([]);
  const [talent, setTalent] = useState<Record<string, unknown>[]>([]);
  const [error, setError] = useState("");

  const load = () => {
    setError("");
    const childNumber = child && /^\d+$/.test(child) ? Number(child) : undefined;
    developmentApi.report({ month, year, child_id: childNumber, review_status: reviewStatus || undefined, observation_frequency: frequency || undefined, district: district || undefined })
      .then((report) => { setDashboard(report.summary); setMissing(report.missing_monthly_observations); setTalent(report.talent_summary); })
      .catch(() => setError("Development report endpoint is not available or returned an error."));
  };
  useEffect(load, [month, year]);

  const filteredMissing = useMemo(() => filterRows(missing, { child, reviewStatus, frequency, district }), [missing, child, reviewStatus, frequency, district]);
  const filteredTalent = useMemo(() => filterRows(talent, { child, reviewStatus, frequency, district }), [talent, child, reviewStatus, frequency, district]);
  const get = (path: string, name: string) => downloadAuthenticated(path, name).catch((e) => setError(apiErrorMessage(e)));

  return <div className="space-y-6">
    <header><p className="eyebrow">Development Profile</p><h1 className="page-title">Development Reports</h1><p className="page-subtitle">Monitor monthly review gaps, support needs, and possible areas of interest.</p></header>
    {error && <div className="notice-error">{error}</div>}
    <section className="panel">
      <h2 className="mb-4 text-lg font-bold">Filters</h2>
      <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Field label="Month"><input className="field-control" type="number" min={1} max={12} value={month} onChange={(e) => setMonth(Number(e.target.value))} /></Field>
        <Field label="Year"><input className="field-control" type="number" min={2000} max={2100} value={year} onChange={(e) => setYear(Number(e.target.value))} /></Field>
        <Field label="Child optional"><input className="field-control" value={child} onChange={(e) => setChild(e.target.value)} placeholder="Child ID/name" /></Field>
        <Field label="Review Status"><select className="field-control" value={reviewStatus} onChange={(e) => setReviewStatus(e.target.value)}><option value="">All</option>{["Draft", "Submitted", "Reviewed", "Needs Follow-up", "Closed", "Archived"].map((x) => <option key={x}>{x}</option>)}</select></Field>
        <Field label="Frequency"><select className="field-control" value={frequency} onChange={(e) => setFrequency(e.target.value)}><option value="">All</option>{["Monthly", "Weekly", "As Needed", "Incident Based", "Counselor Review", "Teacher Review", "Warden Review"].map((x) => <option key={x}>{x}</option>)}</select></Field>
        <Field label="District"><input className="field-control" value={district} onChange={(e) => setDistrict(e.target.value)} placeholder="District" /></Field>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <button className="primary-button" onClick={load}><Play size={16} />Run Report</button>
        <button className="secondary-button" onClick={load}><RefreshCw size={16} />Refresh</button>
      </div>
    </section>
    <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
      <Metric label="Reviewed This Month" value={dashboard.reviewed_this_month || 0} />
      <Metric label="Missing Monthly" value={dashboard.missing_monthly || 0} />
      <Metric label="Needs Follow-up" value={dashboard.needs_follow_up || 0} />
      <Metric label="Urgent Flags" value={dashboard.urgent_flags || 0} />
      <Metric label="Support Needs" value={dashboard.support_needs || 0} />
      <Metric label="Talent Indicators" value={dashboard.talent_indicators || 0} />
    </section>
    <section className="panel">
      <h2 className="mb-4 text-lg font-bold">PDF Exports</h2>
      <div className="flex flex-wrap gap-2">
        <button className="secondary-button" onClick={() => get(`/exports/monthly-development-summary.pdf?month=${month}&year=${year}`, `ccms-monthly-development-${year}-${month}.pdf`)}><Download size={16} />Monthly Summary PDF</button>
        <button className="secondary-button" onClick={() => get("/exports/child-development-observations.pdf", "ccms-development-observations.pdf")}><Download size={16} />Observations PDF</button>
        <button className="secondary-button" onClick={() => get("/exports/child-talent-summary.pdf", "ccms-child-talent-summary.pdf")}><Download size={16} />Talent Summary PDF</button>
      </div>
    </section>
    <section className="grid gap-4 xl:grid-cols-2">
      <ReportCard title="Missing Monthly Observations" rows={filteredMissing} columns={["child_code", "full_name", "district", "status", "last_observation_date"]} action="add" />
      <ReportCard title="Talent / Interest Summary" rows={filteredTalent} columns={["child_code", "full_name", "possible_areas_of_interest", "positive_strengths", "support_needs", "last_observation_date"]} action="view" />
    </section>
  </div>;
}

function filterRows(rows: Record<string, unknown>[], filters: Record<string, string>) {
  return rows.filter((row) => (!filters.child || JSON.stringify(row).toLowerCase().includes(filters.child.toLowerCase())) && (!filters.district || cleanDisplay(row.district).toLowerCase().includes(filters.district.toLowerCase())));
}
function Field({ label, children }: { label: string; children: React.ReactNode }) { return <label className="form-field"><span>{label}</span>{children}</label>; }
function Metric({ label, value }: { label: string; value: number }) { return <div className="metric-card"><div><p>{label}</p><strong>{value}</strong></div></div>; }
function ReportCard({ title, rows, columns, action }: { title: string; rows: Record<string, unknown>[]; columns: string[]; action: "add" | "view" }) {
  return <div className="panel"><h2 className="mb-4 text-lg font-bold">{title}</h2>{rows.length ? <div className="table-shell"><table className="data-table"><thead><tr>{columns.map((column) => <th key={column}>{column.replaceAll("_", " ")}</th>)}<th>Action</th></tr></thead><tbody>{rows.slice(0, 30).map((row, index) => <tr key={index}>{columns.map((column) => <td key={column}>{cleanDisplay(row[column])}</td>)}<td>{action === "add" ? <Link className="secondary-button px-2 py-1 text-xs" href={`/dashboard/development/observations/new?child_id=${row.child_id}`}>Add Observation</Link> : <Link className="secondary-button px-2 py-1 text-xs" href={`/dashboard/children/${row.child_id || ""}`}>View Child</Link>}</td></tr>)}</tbody></table></div> : <div className="empty-card"><h2>No report rows</h2><p>No records match the selected filters.</p></div>}</div>;
}
