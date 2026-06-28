"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CheckCircle2, Download, RefreshCw, ShieldCheck, XCircle } from "lucide-react";
import { downloadAuthenticated } from "@/lib/children";
import { developmentApi } from "@/lib/development";
import { apiErrorMessage } from "@/lib/api";
import { usePermissions } from "@/hooks/usePermissions";
import type { BehaviorSupportPlan, BehaviorSupportPlanNote } from "@/types/development";
import { cleanDisplay } from "./DevelopmentIndicatorField";

export function SupportPlanDetail({ planId }: { planId:number }) {
  const { hasPermission } = usePermissions();
  const [plan, setPlan] = useState<BehaviorSupportPlan | null>(null);
  const [notes, setNotes] = useState<BehaviorSupportPlanNote[]>([]);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");
  const load = () => Promise.all([developmentApi.getSupportPlan(planId), developmentApi.supportPlanNotes(planId).catch(()=>[])]).then(([p,n])=>{setPlan(p);setNotes(n)}).catch(e=>setError(apiErrorMessage(e)));
  useEffect(()=>{void load()},[planId]);
  const act = async(fn:()=>Promise<BehaviorSupportPlan>)=>{setError("");try{setPlan(await fn());await load()}catch(e){setError(apiErrorMessage(e))}};
  const addNote = async()=>{if(!note.trim())return;setError("");try{await developmentApi.createSupportPlanNote(planId,{note_date:new Date().toISOString().slice(0,10),note_type:"Progress Note",progress_note:note,follow_up_required:false});setNote("");await load()}catch(e){setError(apiErrorMessage(e))}};
  if(error)return <div className="notice-error">{error}</div>;
  if(!plan)return <section className="panel">Loading support plan…</section>;
  return <div className="space-y-6">
    <header className="flex flex-col gap-3 md:flex-row md:items-end"><div className="flex-1"><p className="eyebrow">Development Profile</p><h1 className="page-title">Behavior Support Plan</h1><p className="page-subtitle">{plan.plan_code} — {plan.plan_title}</p></div><div className="flex flex-wrap gap-2"><button className="secondary-button" onClick={load}><RefreshCw size={16}/>Refresh</button>{hasPermission("development.support_plan.update")&&<Link className="secondary-button" href={`/dashboard/development/support-plans/${plan.id}/edit`}>Edit</Link>}{hasPermission("development.support_plan.export")&&<button className="secondary-button" onClick={()=>downloadAuthenticated(`/exports/behavior-support-plan/${plan.id}.pdf`,`ccms-behavior-support-plan-${plan.id}.pdf`).catch(e=>setError(apiErrorMessage(e)))}><Download size={16}/>Export PDF</button>}</div></header>
    <section className="grid gap-3 md:grid-cols-4"><Metric label="Child" value={`${cleanDisplay(plan.child_code)} — ${cleanDisplay(plan.child_name)}`}/><Metric label="Type" value={plan.plan_type}/><Metric label="Priority" value={plan.priority_level}/><Metric label="Status" value={plan.plan_status}/><Metric label="Review Date" value={cleanDisplay(plan.review_date)}/><Metric label="Responsible Staff" value={cleanDisplay(plan.responsible_staff_name)}/><Metric label="Start Date" value={cleanDisplay(plan.start_date)}/><Metric label="End Date" value={cleanDisplay(plan.end_date)}/></section>
    <section className="flex flex-wrap gap-2">{hasPermission("development.support_plan.activate")&&plan.plan_status==="Draft"&&<button className="secondary-button" onClick={()=>act(()=>developmentApi.activateSupportPlan(plan.id))}><ShieldCheck size={16}/>Activate</button>}{hasPermission("development.support_plan.review")&&<button className="secondary-button" onClick={()=>act(()=>developmentApi.reviewSupportPlan(plan.id))}>Under Review</button>}{hasPermission("development.support_plan.complete")&&<button className="secondary-button" onClick={()=>act(()=>developmentApi.completeSupportPlan(plan.id))}><CheckCircle2 size={16}/>Complete</button>}{hasPermission("development.support_plan.close")&&<button className="secondary-button" onClick={()=>act(()=>developmentApi.closeSupportPlan(plan.id))}>Close</button>}{hasPermission("development.support_plan.cancel")&&<button className="secondary-button text-red-600" onClick={()=>act(()=>developmentApi.cancelSupportPlan(plan.id))}><XCircle size={16}/>Cancel</button>}</section>
    <section className="grid gap-4 md:grid-cols-2">{["identified_behavior","possible_triggers","replacement_positive_behavior","prevention_strategies","staff_response_plan","de_escalation_steps","positive_reinforcement_plan","counselor_recommendations"].map(key=><Card key={key} title={key.replaceAll("_"," ")} value={plan[key as keyof BehaviorSupportPlan] as string|null}/>)}</section>
    <section className="panel"><h2 className="mb-4 text-lg font-bold">Progress Notes</h2>{hasPermission("development.support_plan.notes.create")&&<div className="mb-4 flex gap-2"><input className="field-control" value={note} onChange={e=>setNote(e.target.value)} placeholder="Progress note" /><button className="secondary-button" onClick={addNote}>Add Note</button></div>}{notes.length?<div className="space-y-3">{notes.map(row=><div key={row.id} className="rounded-xl bg-slate-50 p-4"><div className="text-xs text-slate-500">{row.note_date} • {row.note_type}</div><p className="mt-2 text-sm">{cleanDisplay(row.progress_note)}</p><p className="mt-1 text-xs text-slate-500">Next step: {cleanDisplay(row.next_step)}</p></div>)}</div>:<p className="text-sm text-slate-500">No progress notes recorded.</p>}</section>
    <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">Use observation-based language. Do not enter labels. This plan supports staff care planning.</p>
  </div>
}
function Metric({label,value}:{label:string;value:string}){return <div className="rounded-xl bg-slate-50 p-4"><p className="text-xs text-slate-500">{label}</p><strong className="mt-1 block">{value}</strong></div>}
function Card({title,value}:{title:string;value:string|null}){return <div className="panel"><h2 className="mb-2 text-base font-bold capitalize">{title}</h2><p className="text-sm leading-6 text-slate-700">{cleanDisplay(value)}</p></div>}
