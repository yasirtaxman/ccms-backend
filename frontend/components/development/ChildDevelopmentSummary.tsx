"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Download, Eye, Plus, Sparkles } from "lucide-react";
import { developmentApi } from "@/lib/development";
import { downloadAuthenticated } from "@/lib/children";
import { apiErrorMessage } from "@/lib/api";
import { usePermissions } from "@/hooks/usePermissions";
import type { DevelopmentSummary } from "@/types/development";
import { cleanDisplay } from "./DevelopmentIndicatorField";

export function ChildDevelopmentSummary({ childId }: { childId: number }) {
  const { hasPermission } = usePermissions();
  const [summary, setSummary] = useState<DevelopmentSummary | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { developmentApi.childSummary(childId).then(setSummary).catch((e) => setError(apiErrorMessage(e))); }, [childId]);
  if (error) return <div className="notice-error">{error}</div>;
  if (!summary) return <section className="panel">Loading development summary…</section>;
  const empty = summary.observation_count === 0;
  return <section className="panel">
    <div className="panel-title">
      <div><h2>Development, Behavior & Talent Summary</h2><p className="mt-1 text-sm text-slate-500">Safe child-wise summary for support and guidance.</p></div>
      <div className="flex flex-wrap gap-2">
        {hasPermission("development.create") && <Link className="secondary-button" href={`/dashboard/development/observations/new?child_id=${childId}`}><Plus size={16} />Add Observation</Link>}
        {hasPermission("development.ai_summary.view") && <Link className="secondary-button" href={`/dashboard/children/${childId}/development/ai-summary`}><Sparkles size={16} />AI Summary</Link>}
        {hasPermission("development.support_plan.view") && <Link className="secondary-button" href={`/dashboard/children/${childId}/development/support-plans`}>Support Plans</Link>}
        <Link className="secondary-button" href={`/dashboard/children/${childId}/development`}><Eye size={16} />View Full Development Profile</Link>
        {hasPermission("development.export") && <button className="secondary-button" onClick={() => downloadAuthenticated(`/exports/child-development-profile/${childId}.pdf`, `ccms-child-development-${childId}.pdf`)}><Download size={16} />Export PDF</button>}
      </div>
    </div>
    {empty ? <div className="empty-card"><h2>No development observation has been recorded yet.</h2><p>Add the first monthly, weekly, or as-needed observation when ready.</p></div> : <>
      <div className="grid gap-3 md:grid-cols-3">
        <Metric label="Latest observation" value={cleanDisplay(summary.latest_observation_date)} />
        <Metric label="Latest review status" value={cleanDisplay(summary.review_status)} />
        <Metric label="Monthly status" value={cleanDisplay(summary.monthly_review_status)} />
        <Metric label="Next review" value={cleanDisplay(summary.next_review_date)} />
        <Metric label="Follow-up summary" value={cleanDisplay(summary.urgent_flag_safe_summary)} />
        <Metric label="Recommended support" value={cleanDisplay(summary.recommended_support)} />
      </div>
      <div className="mt-4 grid gap-4 md:grid-cols-3">
        <List title="Positive strengths" items={summary.positive_strengths} />
        <List title="Support needs" items={summary.support_needs} />
        <List title="Possible areas of interest" items={summary.possible_areas_of_interest} />
      </div>
      <p className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-700">{summary.summary_text}</p>
    </>}
  </section>;
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-xl bg-slate-50 p-4"><p className="text-xs text-slate-500">{label}</p><strong className="mt-1 block">{value}</strong></div>; }
function List({ title, items }: { title: string; items: string[] }) { return <div><h3 className="font-semibold text-slate-800">{title}</h3><p className="mt-2 text-sm text-slate-600">{items.length ? items.join(", ") : "Not recorded"}</p></div>; }
