"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Download, Eye, RefreshCw } from "lucide-react";
import { downloadAuthenticated } from "@/lib/children";
import { developmentApi } from "@/lib/development";
import { apiErrorMessage } from "@/lib/api";
import type { DevelopmentAISummary } from "@/types/development";
import { cleanDisplay } from "./DevelopmentIndicatorField";

export function DevelopmentAISummariesPanel() {
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [child, setChild] = useState("");
  const [trend, setTrend] = useState("");
  const [attention, setAttention] = useState("");
  const [status, setStatus] = useState("");
  const [rows, setRows] = useState<DevelopmentAISummary[]>([]);
  const [error, setError] = useState("");
  const load = () => {
    setError("");
    developmentApi.aiSummaryReport({ month, year, child: child || undefined, trend_status: trend || undefined, attention_level: attention || undefined, approval_status: status || undefined })
      .then(setRows)
      .catch((e) => setError(apiErrorMessage(e)));
  };
  useEffect(load, [month, year]);
  const cards = useMemo(() => ({
    generated: rows.length,
    approved: rows.filter((row) => row.approval_status === "Approved").length,
    needs: rows.filter((row) => row.trend_status === "Needs Attention").length,
    urgent: rows.filter((row) => row.attention_level === "Urgent Review").length,
    notEnough: rows.filter((row) => row.trend_status === "Not Enough Data").length,
  }), [rows]);
  return <div className="space-y-6">
    <header><p className="eyebrow">Development Profile</p><h1 className="page-title">AI-Assisted Development Summaries</h1><p className="page-subtitle">Safe, rule-based summaries generated from recorded observations for human review.</p></header>
    {error && <div className="notice-error">{error}</div>}
    <section className="panel">
      <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Field label="Month"><input className="field-control" type="number" min={1} max={12} value={month} onChange={(e) => setMonth(Number(e.target.value))} /></Field>
        <Field label="Year"><input className="field-control" type="number" min={2000} max={2100} value={year} onChange={(e) => setYear(Number(e.target.value))} /></Field>
        <Field label="Child"><input className="field-control" value={child} onChange={(e) => setChild(e.target.value)} placeholder="Code or name" /></Field>
        <Field label="Trend"><select className="field-control" value={trend} onChange={(e) => setTrend(e.target.value)}><option value="">All</option>{["Improving","Stable","Needs Attention","Mixed","Not Enough Data"].map((x)=><option key={x}>{x}</option>)}</select></Field>
        <Field label="Attention"><select className="field-control" value={attention} onChange={(e) => setAttention(e.target.value)}><option value="">All</option>{["Low","Moderate","High","Urgent Review"].map((x)=><option key={x}>{x}</option>)}</select></Field>
        <Field label="Status"><select className="field-control" value={status} onChange={(e) => setStatus(e.target.value)}><option value="">All</option>{["Draft","Generated","Reviewed","Approved","Rejected","Archived"].map((x)=><option key={x}>{x}</option>)}</select></Field>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <button className="secondary-button" onClick={load}><RefreshCw size={16} />Refresh</button>
        <button className="secondary-button" onClick={() => downloadAuthenticated("/exports/development-ai-summaries.pdf", "ccms-development-ai-summaries.pdf").catch((e) => setError(apiErrorMessage(e)))}><Download size={16} />Export PDF</button>
      </div>
    </section>
    <section className="grid gap-3 md:grid-cols-5">
      <Metric label="Generated summaries" value={cards.generated} />
      <Metric label="Approved summaries" value={cards.approved} />
      <Metric label="Needs attention" value={cards.needs} />
      <Metric label="Urgent review" value={cards.urgent} />
      <Metric label="Not enough data" value={cards.notEnough} />
    </section>
    <section className="panel">
      {rows.length ? <div className="table-shell"><table className="data-table"><thead><tr>{["Child Code","Child Name","Month/Year","Trend","Attention Level","Approval Status","Source Observations","Last Generated","Actions"].map((h)=><th key={h}>{h}</th>)}</tr></thead><tbody>{rows.map((row)=><tr key={row.id}><td>{cleanDisplay(row.child_code)}</td><td>{cleanDisplay(row.child_name)}</td><td>{row.summary_period_month}/{row.summary_period_year}</td><td>{row.trend_status}</td><td>{row.is_sensitive ? "Restricted" : row.attention_level}</td><td>{row.approval_status}</td><td>{row.source_observation_count}</td><td>{cleanDisplay(row.generated_at)}</td><td><Link className="icon-button" href={`/dashboard/development/ai-summaries/${row.id}`}><Eye size={16} /></Link></td></tr>)}</tbody></table></div> : <div className="empty-card"><h2>No summaries found</h2><p>Generate a child AI-assisted summary from the child development page.</p></div>}
    </section>
  </div>;
}

function Field({ label, children }: { label:string; children:React.ReactNode }) { return <label className="form-field"><span>{label}</span>{children}</label>; }
function Metric({ label, value }: { label:string; value:number }) { return <div className="metric-card"><div><p>{label}</p><strong>{value}</strong></div></div>; }
