"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Plus, Sparkles } from "lucide-react";
import { childrenApi } from "@/lib/children";
import { developmentApi } from "@/lib/development";
import { apiErrorMessage } from "@/lib/api";
import { usePermissions } from "@/hooks/usePermissions";
import type { Child } from "@/types/children";
import type { BehaviorSupportPlan } from "@/types/development";
import { cleanDisplay } from "./DevelopmentIndicatorField";

export function ChildSupportPlansPanel({ childId }: { childId:number }) {
  const { hasPermission } = usePermissions();
  const [child, setChild] = useState<Child | null>(null);
  const [rows, setRows] = useState<BehaviorSupportPlan[]>([]);
  const [error, setError] = useState("");
  const load = () => Promise.all([childrenApi.get(childId), developmentApi.childSupportPlans(childId)]).then(([c,p])=>{setChild(c);setRows(p)}).catch(e=>setError(apiErrorMessage(e)));
  useEffect(()=>{void load()},[childId]);
  const generate = async()=>{setError("");try{await developmentApi.generateSupportPlan(childId);await load()}catch(e){setError(apiErrorMessage(e))}};
  const active = rows.find(row=>row.plan_status==="Active");
  return <div className="space-y-6">
    <header className="flex flex-col gap-3 md:flex-row md:items-end"><div className="flex-1"><p className="eyebrow">Development Profile</p><h1 className="page-title">Child Behavior Support Plans</h1><p className="page-subtitle">Observation-based support plans for staff care planning.</p></div><div className="flex flex-wrap gap-2">{hasPermission("development.support_plan.generate")&&<button className="primary-button" onClick={generate}><Sparkles size={16}/>Generate Draft Support Plan</button>}{hasPermission("development.support_plan.create")&&<Link className="secondary-button" href={`/dashboard/children/${childId}/development/support-plans/new`}><Plus size={16}/>Create Manual Plan</Link>}</div></header>
    {error&&<div className="notice-error">{error}</div>}
    <section className="panel"><div className="grid gap-3 md:grid-cols-4"><Metric label="Child Code" value={cleanDisplay(child?.child_id)}/><Metric label="Child Name" value={cleanDisplay(child?.full_name)}/><Metric label="Status" value={cleanDisplay(child?.status)}/><Metric label="District" value={cleanDisplay(child?.district)}/></div></section>
    {active&&<section className="panel border-l-4 border-l-blue-600"><h2 className="mb-3 text-lg font-bold">Active Behavior Support Plan</h2><div className="grid gap-3 md:grid-cols-4"><Metric label="Priority level" value={active.priority_level}/><Metric label="Review date" value={cleanDisplay(active.review_date)}/><Metric label="Support focus" value={cleanDisplay(active.plan_title)}/><Metric label="Latest progress note" value={cleanDisplay(active.latest_progress_note)}/></div><Link className="secondary-button mt-4" href={`/dashboard/development/support-plans/${active.id}`}>Open Full Plan</Link></section>}
    <section className="panel">{rows.length?<div className="table-shell"><table className="data-table"><thead><tr>{["Plan Code","Title","Type","Priority","Status","Review Date","Actions"].map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{rows.map(row=><tr key={row.id}><td>{row.plan_code}</td><td>{row.plan_title}</td><td>{row.plan_type}</td><td>{row.priority_level}</td><td>{row.plan_status}</td><td className={row.review_date&&new Date(row.review_date)<new Date()&&["Active","Under Review"].includes(row.plan_status)?"text-red-600 font-semibold":""}>{cleanDisplay(row.review_date)}</td><td><Link className="secondary-button px-2 py-1 text-xs" href={`/dashboard/development/support-plans/${row.id}`}>View</Link></td></tr>)}</tbody></table></div>:<div className="empty-card"><h2>No support plans recorded</h2><p>Generate a draft or create a manual plan using observation-based language.</p></div>}</section>
  </div>
}
function Metric({label,value}:{label:string;value:string}){return <div className="rounded-xl bg-slate-50 p-4"><p className="text-xs text-slate-500">{label}</p><strong className="mt-1 block">{value}</strong></div>}
