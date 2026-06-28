"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Download, Eye, RefreshCw } from "lucide-react";
import { downloadAuthenticated } from "@/lib/children";
import { developmentApi } from "@/lib/development";
import { apiErrorMessage } from "@/lib/api";
import type { BehaviorSupportPlanReport } from "@/types/development";
import { cleanDisplay } from "./DevelopmentIndicatorField";

export function SupportPlanListPanel() {
  const now = new Date();
  const [filters, setFilters] = useState({ child: "", plan_status: "", plan_type: "", priority_level: "", month: String(now.getMonth() + 1), year: String(now.getFullYear()) });
  const [report, setReport] = useState<BehaviorSupportPlanReport | null>(null);
  const [error, setError] = useState("");
  const load = () => {
    setError("");
    developmentApi.supportPlanReport({ child_id: /^\d+$/.test(filters.child) ? Number(filters.child) : undefined, plan_status: filters.plan_status || undefined, plan_type: filters.plan_type || undefined, priority_level: filters.priority_level || undefined, month: Number(filters.month), year: Number(filters.year) }).then(setReport).catch((e) => setError(apiErrorMessage(e)));
  };
  useEffect(load, []);
  const summary = report?.summary || { active_plans: 0, under_review: 0, high_priority: 0, urgent_review: 0, completed_this_month: 0 };
  return <div className="space-y-6">
    <header><p className="eyebrow">Development Profile</p><h1 className="page-title">Behavior Support Plans</h1><p className="page-subtitle">Observation-based staff support and care planning inside Child Development.</p></header>
    {error && <div className="notice-error">{error}</div>}
    <section className="panel">
      <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Field label="Child ID"><input className="field-control" value={filters.child} onChange={(e)=>setFilters({...filters,child:e.target.value})} placeholder="Numeric child ID" /></Field>
        <Field label="Status"><select className="field-control" value={filters.plan_status} onChange={(e)=>setFilters({...filters,plan_status:e.target.value})}><option value="">All</option>{["Draft","Active","Under Review","Completed","Closed","Cancelled","Archived"].map(x=><option key={x}>{x}</option>)}</select></Field>
        <Field label="Type"><select className="field-control" value={filters.plan_type} onChange={(e)=>setFilters({...filters,plan_type:e.target.value})}><option value="">All</option>{["Behavior Support","Emotional Support","Learning Support","Social Support","Safety Support","General Support"].map(x=><option key={x}>{x}</option>)}</select></Field>
        <Field label="Priority"><select className="field-control" value={filters.priority_level} onChange={(e)=>setFilters({...filters,priority_level:e.target.value})}><option value="">All</option>{["Low","Moderate","High","Urgent Review"].map(x=><option key={x}>{x}</option>)}</select></Field>
        <Field label="Month"><input className="field-control" type="number" min={1} max={12} value={filters.month} onChange={(e)=>setFilters({...filters,month:e.target.value})} /></Field>
        <Field label="Year"><input className="field-control" type="number" min={2000} max={2100} value={filters.year} onChange={(e)=>setFilters({...filters,year:e.target.value})} /></Field>
      </div>
      <div className="mt-4 flex flex-wrap gap-2"><button className="secondary-button" onClick={load}><RefreshCw size={16}/>Run Report</button><button className="secondary-button" onClick={()=>downloadAuthenticated("/exports/behavior-support-plans.pdf","ccms-behavior-support-plans.pdf").catch(e=>setError(apiErrorMessage(e)))}><Download size={16}/>Export PDF</button></div>
    </section>
    <section className="grid gap-3 md:grid-cols-5"><Metric label="Active Plans" value={summary.active_plans}/><Metric label="Under Review" value={summary.under_review}/><Metric label="High Priority" value={summary.high_priority}/><Metric label="Urgent Review" value={summary.urgent_review}/><Metric label="Completed This Month" value={summary.completed_this_month}/></section>
    <section className="panel">{report?.plans.length ? <div className="table-shell"><table className="data-table"><thead><tr>{["Plan Code","Child Code","Child Name","Plan Type","Priority","Status","Review Date","Responsible Staff","Actions"].map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{report.plans.map(row=><tr key={row.id}><td>{row.plan_code}</td><td>{cleanDisplay(row.child_code)}</td><td>{cleanDisplay(row.child_name)}</td><td>{row.plan_type}</td><td>{row.priority_level}</td><td>{row.plan_status}</td><td>{cleanDisplay(row.review_date)}</td><td>{cleanDisplay(row.responsible_staff_name)}</td><td><Link className="icon-button" href={`/dashboard/development/support-plans/${row.id}`}><Eye size={16}/></Link></td></tr>)}</tbody></table></div> : <div className="empty-card"><h2>No support plans found</h2><p>No records match the selected filters.</p></div>}</section>
  </div>;
}
function Field({label,children}:{label:string;children:React.ReactNode}){return <label className="form-field"><span>{label}</span>{children}</label>}
function Metric({label,value}:{label:string;value:number}){return <div className="metric-card"><div><p>{label}</p><strong>{value}</strong></div></div>}
