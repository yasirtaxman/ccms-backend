"use client";
import Link from "next/link";
import { useCallback,useEffect,useMemo,useState } from "react";
import { Download,ExternalLink,RefreshCw,Search } from "lucide-react";
import { api,apiErrorMessage } from "@/lib/api";
import { downloadAuthenticated } from "@/lib/children";
import { usePermissions } from "@/hooks/usePermissions";

type Config={title:string;description:string;endpoint?:string;secondary?:string;action?:{label:string;href:string};admin?:boolean};
const configs:Record<string,Config>={
  sponsors:{title:"Sponsors",description:"Review the sponsor directory and current status.",endpoint:"/sponsors",action:{label:"Export sponsors",href:"/exports/sponsors.xlsx"}},
  sponsorships:{title:"Sponsorships",description:"Monitor active child sponsorship arrangements.",endpoint:"/reports/active-sponsorships",action:{label:"Export sponsorships",href:"/exports/sponsorships.xlsx"}},
  buildings:{title:"Buildings",description:"Accommodation buildings and their operational status.",endpoint:"/buildings",secondary:"/reports/occupancy"},
  "rooms-beds":{title:"Rooms & Beds",description:"Room inventory and bed availability.",endpoint:"/beds",secondary:"/reports/occupancy"},
  "bed-allocations":{title:"Bed Allocations",description:"Current and historical child bed allocations.",endpoint:"/bed-allocations",secondary:"/reports/occupancy"},
  "medical-profiles":{title:"Medical Profiles",description:"Safe child medical profile overview.",endpoint:"/reports/medical-profiles"},
  "medical-visits":{title:"Medical Visits",description:"Recent medical visits and follow-up records.",endpoint:"/reports/medical-visits"},
  medications:{title:"Medications",description:"Active medication register.",endpoint:"/reports/active-medications"},
  vaccinations:{title:"Vaccinations",description:"Upcoming vaccination schedule.",endpoint:"/reports/upcoming-vaccinations"},
  schools:{title:"Schools",description:"Education institution directory.",endpoint:"/schools"},
  "education-records":{title:"Education Records",description:"Current student enrollment records.",endpoint:"/reports/students"},
  results:{title:"Exam Results",description:"Recorded academic examination results.",endpoint:"/reports/exam-results"},
  attendance:{title:"Education Attendance",description:"Academic attendance requiring attention.",endpoint:"/reports/low-attendance"},
  "case-profiles":{title:"Case Profiles",description:"Child welfare case profiles and risk status.",endpoint:"/reports/case-profiles"},
  "case-notes":{title:"Case Follow-ups",description:"Case notes with pending follow-up actions.",endpoint:"/reports/pending-follow-ups"},
  counseling:{title:"Counseling",description:"Upcoming counseling sessions.",endpoint:"/reports/upcoming-counseling-sessions"},
  incidents:{title:"Incidents",description:"Critical incidents requiring review.",endpoint:"/reports/critical-incidents"},
  "care-plans":{title:"Care Plans",description:"Active child care plans.",endpoint:"/reports/active-care-plans"},
  "case-reviews":{title:"Case Reviews",description:"Upcoming case review schedule.",endpoint:"/reports/upcoming-case-reviews"},
  reports:{title:"Consolidated Reports",description:"Cross-module operational reporting.",endpoint:"/reports/consolidated/children"},
  exports:{title:"Exports",description:"Download approved CCMS operational reports."},
  imports:{title:"Imports",description:"Preview and commit validated child Excel or CSV files.",action:{label:"Open children import",href:"/dashboard/children/import"}},
  users:{title:"Users",description:"System users, roles, and account status.",endpoint:"/users",admin:true},
  roles:{title:"Roles",description:"Configured access-control roles.",endpoint:"/roles",admin:true},
  "audit-logs":{title:"Audit Logs",description:"Chronological record of security and operational activity.",endpoint:"/audit-logs",admin:true},
  "system-status":{title:"System Status",description:"Live API health, readiness, and deployment information.",endpoint:"/system/readiness",secondary:"/system/info",admin:true},
};
const exportFiles=["children.xlsx","children.pdf","sponsors.xlsx","sponsors.pdf","sponsorships.xlsx","accommodation.xlsx","accommodation.pdf","medical.xlsx","medical.pdf","education.xlsx","education.pdf","case-management.xlsx","case-management.pdf"];
const blocked=/password|token|cnic|passport|mobile|address|diagnosis|treatment|confidential|restricted|note_text/i;
const label=(value:string)=>value.replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase());
function rowsFrom(value:unknown):Record<string,unknown>[] {if(Array.isArray(value))return value as Record<string,unknown>[];if(value&&typeof value==="object"){const object=value as Record<string,unknown>;for(const key of ["data","items","checks"]){if(Array.isArray(object[key]))return object[key] as Record<string,unknown>[];}return Object.entries(object).map(([key,item])=>typeof item==="object"&&item!==null?{name:key,...item as Record<string,unknown>}:{name:key,value:item});}return []}
export function ModuleWorkspace({moduleKey}:{moduleKey:string}){
 const config=configs[moduleKey]||{title:label(moduleKey),description:"Operational CCMS records.",endpoint:"/dashboard/operational"};const {isViewer}=usePermissions();const [rows,setRows]=useState<Record<string,unknown>[]>([]);const [summary,setSummary]=useState<Record<string,unknown>[]>([]);const [loading,setLoading]=useState(Boolean(config.endpoint));const [error,setError]=useState("");const [query,setQuery]=useState("");const [busy,setBusy]=useState("");
 const load=useCallback(async()=>{if(!config.endpoint)return;setLoading(true);setError("");try{const [primary,secondary]=await Promise.all([api.get(config.endpoint),config.secondary?api.get(config.secondary):Promise.resolve(null)]);setRows(rowsFrom(primary.data));setSummary(secondary?rowsFrom(secondary.data):[])}catch(e){setError(apiErrorMessage(e))}finally{setLoading(false)}},[config.endpoint,config.secondary]);useEffect(()=>{void load()},[load]);
 const filtered=useMemo(()=>rows.filter(row=>JSON.stringify(row).toLowerCase().includes(query.toLowerCase())),[rows,query]);const columns=useMemo(()=>Array.from(new Set(filtered.flatMap(Object.keys))).filter(key=>!blocked.test(key)).slice(0,9),[filtered]);
 const download=async(path:string)=>{setBusy(path);setError("");try{await downloadAuthenticated(`/exports/${path}`,`ccms-${path}`)}catch(e){setError(apiErrorMessage(e))}finally{setBusy("")}};
 return <div className="space-y-6"><header className="flex flex-col gap-4 lg:flex-row lg:items-end"><div className="flex-1"><p className="eyebrow">CCMS workspace</p><h1 className="page-title">{config.title}</h1><p className="page-subtitle">{config.description}</p></div><div className="flex gap-2">{config.endpoint&&<button className="secondary-button" onClick={load} disabled={loading}><RefreshCw size={16}/>Refresh</button>}{config.action&&(config.action.href.startsWith("/exports/")?<button className="primary-button" onClick={()=>download(config.action!.href.replace("/exports/",""))}><Download size={16}/>{config.action.label}</button>:<Link className="primary-button" href={config.action.href}><ExternalLink size={16}/>{config.action.label}</Link>)}</div></header>{error&&<div className="notice-error">{error}</div>}{moduleKey==="imports"&&<Info text="Use the children import workspace to download the approved template, preview validation results, correct errors, and commit a valid file. Direct Google Sheets synchronization is not supported."/>}{moduleKey==="exports"&&<section className="panel"><h2 className="text-lg font-bold">Available downloads</h2><div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{exportFiles.map(path=><button key={path} disabled={busy===path} className="secondary-button justify-start" onClick={()=>download(path)}><Download size={16}/>{label(path.replace("."," "))}</button>)}</div></section>}{summary.length>0&&<section className="grid gap-3 md:grid-cols-3">{summary.slice(0,6).map((item,index)=><div className="metric-card" key={index}><div><p>{String(item.name||`Metric ${index+1}`)}</p><strong>{String(item.value??item.status??Object.values(item)[1]??"-")}</strong></div></div>)}</section>}{config.endpoint&&<section className="panel"><div className="mb-4 flex items-center justify-between gap-4"><label className="input-wrap mt-0 max-w-md"><Search size={17}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder={`Search ${config.title.toLowerCase()}`}/></label><span className="text-sm text-slate-500">{filtered.length} records</span></div>{loading?<p className="text-sm text-slate-500">Loading {config.title.toLowerCase()}…</p>:filtered.length?<div className="table-shell"><table className="data-table"><thead><tr>{columns.map(column=><th key={column}>{label(column)}</th>)}</tr></thead><tbody>{filtered.map((row,index)=><tr key={String(row.id??index)}>{columns.map(column=><td key={column}>{format(row[column],isViewer())}</td>)}</tr>)}</tbody></table></div>:<div className="empty-card"><h2>No records found</h2><p>No {config.title.toLowerCase()} match the current view.</p></div>}</section>}{config.admin&&<p className="text-xs text-slate-500">This workspace is restricted to administrators.</p>}</div>;
}
function format(value:unknown,viewer:boolean){if(value===null||value===undefined||value==="")return "-";if(typeof value==="boolean")return value?"Yes":"No";if(typeof value==="object")return viewer?"Summary available":JSON.stringify(value);return String(value)}
function Info({text}:{text:string}){return <section className="panel"><h2 className="text-lg font-bold">Workflow</h2><p className="mt-2 text-sm leading-6 text-slate-600">{text}</p></section>}
