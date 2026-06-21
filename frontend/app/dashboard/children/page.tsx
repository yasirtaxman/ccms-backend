"use client";
import Link from "next/link";
import { useEffect,useMemo,useState } from "react";
import { FileUp,Plus,Search } from "lucide-react";
import { childrenApi } from "@/lib/children";
import { apiErrorMessage } from "@/lib/api";
import { usePermissions } from "@/hooks/usePermissions";
import type { Child } from "@/types/children";
import { ChildrenTable } from "@/components/children/ChildrenTable";
import { ChildExportButtons } from "@/components/children/ChildExportButtons";

export default function ChildrenPage(){
  const {hasAnyRole}=usePermissions();const canEdit=hasAnyRole(["Admin","Manager","Data Entry Operator"]);
  const [rows,setRows]=useState<Child[]>([]);const [loading,setLoading]=useState(true);const [error,setError]=useState("");
  const [search,setSearch]=useState("");const [status,setStatus]=useState("");const [gender,setGender]=useState("");const [district,setDistrict]=useState("");const [page,setPage]=useState(1);const pageSize=20;
  useEffect(()=>{childrenApi.list().then(setRows).catch(e=>setError(apiErrorMessage(e))).finally(()=>setLoading(false))},[]);
  const filtered=useMemo(()=>rows.filter(child=>{const term=search.toLowerCase();return (!term||[child.full_name,child.child_id,child.admission_file_no].some(v=>v.toLowerCase().includes(term)))&&(!status||child.status===status)&&(!gender||child.gender===gender)&&(!district||child.district===district)}),[rows,search,status,gender,district]);
  const pageCount=Math.max(1,Math.ceil(filtered.length/pageSize));const shown=filtered.slice((page-1)*pageSize,page*pageSize);const districts=[...new Set(rows.map(x=>x.district))].sort();
  const change=(setter:(v:string)=>void)=>(e:React.ChangeEvent<HTMLInputElement|HTMLSelectElement>)=>{setter(e.target.value);setPage(1)};
  return <div className="space-y-6"><div className="flex flex-col gap-4 lg:flex-row lg:items-end"><div className="flex-1"><p className="eyebrow">Child management</p><h1 className="page-title">Children</h1><p className="page-subtitle">Search, maintain, import, and review enrolled child records.</p></div><div className="flex flex-wrap gap-2"><ChildExportButtons/>{canEdit&&<Link href="/dashboard/children/import" className="secondary-button"><FileUp size={16}/>Import Children</Link>}{canEdit&&<Link href="/dashboard/children/new" className="primary-button"><Plus size={16}/>Add Child</Link>}</div></div><section className="panel"><div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4"><label className="input-wrap mt-0"><Search size={17}/><input value={search} onChange={change(setSearch)} placeholder="Name, child ID, admission file"/></label><select className="field-control" value={status} onChange={change(setStatus)}><option value="">All statuses</option>{["Active","Inactive","Discharged","Transferred"].map(x=><option key={x}>{x}</option>)}</select><select className="field-control" value={gender} onChange={change(setGender)}><option value="">All genders</option>{["Male","Female","Other"].map(x=><option key={x}>{x}</option>)}</select><select className="field-control" value={district} onChange={change(setDistrict)}><option value="">All districts</option>{districts.map(x=><option key={x}>{x}</option>)}</select></div><p className="mt-3 text-sm text-slate-500">Showing {shown.length} of {filtered.length} matching children</p></section>{error&&<div className="notice-error">{error}</div>}{loading?<div className="panel">Loading children…</div>:<ChildrenTable rows={shown} canEdit={canEdit}/>} {!loading&&filtered.length>pageSize&&<div className="flex items-center justify-between"><button className="secondary-button" disabled={page===1} onClick={()=>setPage(p=>p-1)}>Previous</button><span className="text-sm text-slate-500">Page {page} of {pageCount}</span><button className="secondary-button" disabled={page===pageCount} onClick={()=>setPage(p=>p+1)}>Next</button></div>}</div>;
}
