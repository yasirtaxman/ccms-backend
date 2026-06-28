"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Download, RefreshCw, ShieldCheck, XCircle } from "lucide-react";
import { downloadAuthenticated } from "@/lib/children";
import { developmentApi } from "@/lib/development";
import { apiErrorMessage } from "@/lib/api";
import { usePermissions } from "@/hooks/usePermissions";
import type { DevelopmentAISummary } from "@/types/development";
import { cleanDisplay } from "./DevelopmentIndicatorField";

export function DevelopmentAISummaryDetail({ summaryId }: { summaryId:number }) {
  const { hasPermission } = usePermissions();
  const [row, setRow] = useState<DevelopmentAISummary | null>(null);
  const [error, setError] = useState("");
  const load = () => developmentApi.getAiSummary(summaryId).then(setRow).catch((e) => setError(apiErrorMessage(e)));
  useEffect(() => { void load(); }, [summaryId]);
  const action = async (fn:()=>Promise<DevelopmentAISummary>) => { setError(""); try { setRow(await fn()); } catch(e) { setError(apiErrorMessage(e)); } };
  if (error) return <div className="notice-error">{error}</div>;
  if (!row) return <section className="panel">Loading AI-assisted summary…</section>;
  return <div className="space-y-6">
    <header className="flex flex-col gap-3 md:flex-row md:items-end">
      <div className="flex-1"><p className="eyebrow">Development Profile</p><h1 className="page-title">AI-Assisted Child Development Summary</h1><p className="page-subtitle">Human-reviewable support summary based on recorded observations.</p></div>
      <div className="flex flex-wrap gap-2">
        <button className="secondary-button" onClick={load}><RefreshCw size={16} />Refresh</button>
        {hasPermission("development.ai_summary.export") && <button className="secondary-button" onClick={() => downloadAuthenticated(`/exports/development-ai-summary/${row.id}.pdf`, `ccms-development-ai-summary-${row.id}.pdf`).catch((e) => setError(apiErrorMessage(e)))}><Download size={16} />Export PDF</button>}
        {hasPermission("development.ai_summary.review") && row.approval_status === "Generated" && <button className="secondary-button" onClick={() => action(() => developmentApi.reviewAiSummary(row.id, "Reviewed by authorized staff."))}><ShieldCheck size={16} />Review</button>}
        {hasPermission("development.ai_summary.approve") && ["Generated","Reviewed"].includes(row.approval_status) && <button className="secondary-button" onClick={() => action(() => developmentApi.approveAiSummary(row.id))}><CheckCircle2 size={16} />Approve</button>}
        {hasPermission("development.ai_summary.reject") && row.approval_status !== "Rejected" && <button className="secondary-button text-red-600" onClick={() => action(() => developmentApi.rejectAiSummary(row.id, "Rejected for correction."))}><XCircle size={16} />Reject</button>}
      </div>
    </header>
    <section className="grid gap-3 md:grid-cols-4">
      <Metric label="Child" value={`${cleanDisplay(row.child_code)} — ${cleanDisplay(row.child_name)}`} />
      <Metric label="Period" value={`${row.summary_period_month}/${row.summary_period_year}`} />
      <Metric label="Status" value={row.approval_status} />
      <Metric label="Source Observations" value={String(row.source_observation_count)} />
      <Metric label="Trend" value={row.trend_status} />
      <Metric label="Attention" value={row.is_sensitive ? "Restricted" : row.attention_level} />
      <Metric label="Source Period" value={`${cleanDisplay(row.source_date_from)} to ${cleanDisplay(row.source_date_to)}`} />
      <Metric label="Next Review" value={cleanDisplay(row.next_review_date)} />
    </section>
    <section className="grid gap-4 md:grid-cols-2">
      <Card title="Overall Summary" value={row.overall_summary} />
      <Card title="Positive Strengths" value={row.positive_strengths_summary} />
      <Card title="Support Needs" value={row.support_needs_summary} />
      <Card title="Talent / Interests" value={row.talent_interest_summary} />
      <Card title="Behavior Trend" value={row.behavior_trend_summary} />
      <Card title="Emotional Wellbeing" value={row.emotional_wellbeing_summary} />
      <Card title="Learning Behavior" value={row.learning_behavior_summary} />
      <Card title="Social Behavior" value={row.social_behavior_summary} />
      <Card title="Risk Attention" value={row.risk_attention_summary} />
      <Card title="Staff Actions" value={row.recommended_staff_actions} />
      <Card title="Counselor Actions" value={row.recommended_counselor_actions} />
      <Card title="Internal Notes" value={row.internal_notes} />
    </section>
    <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">This summary is based on recorded observations and is intended to support staff review. It is not a medical or psychological diagnosis.</p>
  </div>;
}

function Metric({ label, value }: { label:string; value:string }) { return <div className="rounded-xl bg-slate-50 p-4"><p className="text-xs text-slate-500">{label}</p><strong className="mt-1 block">{value}</strong></div>; }
function Card({ title, value }: { title:string; value:string|null }) { return <div className="panel"><h2 className="mb-2 text-base font-bold">{title}</h2><p className="text-sm leading-6 text-slate-700">{cleanDisplay(value)}</p></div>; }
