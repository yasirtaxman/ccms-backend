"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CheckCircle2, Download, RefreshCw, Sparkles } from "lucide-react";
import { childrenApi, downloadAuthenticated } from "@/lib/children";
import { developmentApi } from "@/lib/development";
import { apiErrorMessage } from "@/lib/api";
import { usePermissions } from "@/hooks/usePermissions";
import type { Child } from "@/types/children";
import type { DevelopmentAISummary } from "@/types/development";
import { cleanDisplay } from "./DevelopmentIndicatorField";

export function ChildDevelopmentAISummaryPanel({ childId }: { childId:number }) {
  const { hasPermission } = usePermissions();
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [child, setChild] = useState<Child | null>(null);
  const [summary, setSummary] = useState<DevelopmentAISummary | null>(null);
  const [error, setError] = useState("");
  const load = () => {
    setError("");
    Promise.all([childrenApi.get(childId), developmentApi.latestAiSummary(childId).catch(() => null)])
      .then(([c, s]) => { setChild(c); setSummary(s); })
      .catch((e) => setError(apiErrorMessage(e)));
  };
  useEffect(load, [childId]);
  const generate = async () => { setError(""); try { setSummary(await developmentApi.generateAiSummary(childId, { month, year })); } catch(e) { setError(apiErrorMessage(e)); } };
  const approve = async () => { if (!summary) return; setSummary(await developmentApi.approveAiSummary(summary.id)); };
  return <div className="space-y-6">
    <header className="flex flex-col gap-3 md:flex-row md:items-end">
      <div className="flex-1"><p className="eyebrow">Development Profile</p><h1 className="page-title">Child AI-Assisted Development Summary</h1><p className="page-subtitle">Generate and review safe support summaries from recorded observations.</p></div>
      <div className="flex flex-wrap gap-2">
        <button className="secondary-button" onClick={load}><RefreshCw size={16} />Refresh</button>
        {hasPermission("development.ai_summary.generate") && <button className="primary-button" onClick={generate}><Sparkles size={16} />Generate Summary</button>}
        {summary && hasPermission("development.ai_summary.export") && <button className="secondary-button" onClick={() => downloadAuthenticated(`/exports/development-ai-summary/${summary.id}.pdf`, `ccms-development-ai-summary-${summary.id}.pdf`).catch((e) => setError(apiErrorMessage(e)))}><Download size={16} />Export PDF</button>}
        {summary && hasPermission("development.ai_summary.approve") && ["Generated","Reviewed"].includes(summary.approval_status) && <button className="secondary-button" onClick={approve}><CheckCircle2 size={16} />Approve</button>}
      </div>
    </header>
    {error && <div className="notice-error">{error}</div>}
    <section className="panel">
      <div className="grid gap-3 md:grid-cols-4">
        <Metric label="Child Code" value={cleanDisplay(child?.child_id)} />
        <Metric label="Child Name" value={cleanDisplay(child?.full_name)} />
        <Metric label="Status" value={cleanDisplay(child?.status)} />
        <Metric label="District" value={cleanDisplay(child?.district)} />
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-4">
        <label className="form-field"><span>Month</span><input className="field-control" type="number" min={1} max={12} value={month} onChange={(e)=>setMonth(Number(e.target.value))} /></label>
        <label className="form-field"><span>Year</span><input className="field-control" type="number" min={2000} max={2100} value={year} onChange={(e)=>setYear(Number(e.target.value))} /></label>
      </div>
    </section>
    {summary ? <section className="space-y-4">
      <div className="grid gap-3 md:grid-cols-4">
        <Metric label="Approval Status" value={summary.approval_status} />
        <Metric label="Source Observations" value={String(summary.source_observation_count)} />
        <Metric label="Trend" value={summary.trend_status} />
        <Metric label="Next Review" value={cleanDisplay(summary.next_review_date)} />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Card title="Overall Summary" value={summary.overall_summary} />
        <Card title="Positive Strengths" value={summary.positive_strengths_summary} />
        <Card title="Support Needs" value={summary.support_needs_summary} />
        <Card title="Talent / Interests" value={summary.talent_interest_summary} />
        <Card title="Staff Action Suggestions" value={summary.recommended_staff_actions} />
        <Card title="Counselor Action Suggestions" value={summary.recommended_counselor_actions} />
      </div>
      <Link className="secondary-button" href={`/dashboard/development/ai-summaries/${summary.id}`}>Open Full Summary</Link>
    </section> : <div className="empty-card"><h2>No AI-assisted summary available</h2><p>Generate a summary after recording development observations.</p></div>}
  </div>;
}

function Metric({ label, value }: { label:string; value:string }) { return <div className="rounded-xl bg-slate-50 p-4"><p className="text-xs text-slate-500">{label}</p><strong className="mt-1 block">{value}</strong></div>; }
function Card({ title, value }: { title:string; value:string|null }) { return <div className="panel"><h2 className="mb-2 text-base font-bold">{title}</h2><p className="text-sm leading-6 text-slate-700">{cleanDisplay(value)}</p></div>; }
