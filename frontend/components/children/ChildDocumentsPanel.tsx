"use client";
import { useCallback,useEffect,useState } from "react";
import { CheckCircle2,FileUp,ShieldCheck,Trash2 } from "lucide-react";
import { childrenApi } from "@/lib/children";
import { apiErrorMessage } from "@/lib/api";
import { usePermissions } from "@/hooks/usePermissions";
import type { ChildDocument } from "@/types/children";
const types=["Admission Form","Affidavit","Death Certificate","Father CNIC","Guardian CNIC","Birth Certificate","Child Photo"];

export function ChildDocumentsPanel({childId}:{childId:number}){
  const {hasAnyRole,isAdmin,isViewer}=usePermissions();const canWrite=hasAnyRole(["Admin","Manager","Data Entry Operator"]);
  const [documents,setDocuments]=useState<ChildDocument[]>([]);const [type,setType]=useState(types[0]);const [file,setFile]=useState<File|null>(null);const [loading,setLoading]=useState(true);const [busy,setBusy]=useState(false);const [error,setError]=useState("");
  const load=useCallback(()=>childrenApi.documents(childId).then(setDocuments).catch(e=>setError(apiErrorMessage(e))).finally(()=>setLoading(false)),[childId]);useEffect(()=>{void load()},[load]);
  const upload=async()=>{if(!file)return;setBusy(true);setError("");try{await childrenApi.uploadDocument(childId,type,file);setFile(null);await load()}catch(e){setError(apiErrorMessage(e))}finally{setBusy(false)}};
  const verify=async(id:number)=>{setBusy(true);try{await childrenApi.verifyDocument(id);await load()}catch(e){setError(apiErrorMessage(e))}finally{setBusy(false)}};
  const remove=async(id:number)=>{if(!confirm("Delete this document?"))return;setBusy(true);try{await childrenApi.deleteDocument(id);await load()}catch(e){setError(apiErrorMessage(e))}finally{setBusy(false)}};
  return <section className="panel"><div className="panel-title"><div><h2>Admission documents</h2><p className="mt-1 text-sm text-slate-500">{documents.length} of {types.length} required document types uploaded</p></div></div>{error&&<div className="notice-error mb-4">{error}</div>}{canWrite&&<div className="mb-5 grid gap-3 rounded-xl bg-slate-50 p-4 md:grid-cols-[1fr_1fr_auto]"><select className="field-control" value={type} onChange={e=>setType(e.target.value)}>{types.map(item=><option key={item}>{item}</option>)}</select><input className="field-control" type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={e=>setFile(e.target.files?.[0]||null)}/><button disabled={!file||busy} onClick={upload} className="primary-button"><FileUp size={16}/>Upload</button></div>}{loading?<p className="text-sm text-slate-500">Loading documents…</p>:documents.length?<div className="space-y-2">{documents.map(doc=><div key={doc.id} className="flex flex-col gap-3 rounded-lg border border-slate-200 p-3 sm:flex-row sm:items-center"><div className="flex-1"><p className="font-medium">{doc.document_type}</p>{!isViewer()&&<p className="text-xs text-slate-500">{doc.original_filename}</p>}</div><span className={doc.is_verified?"badge-success":"badge"}>{doc.is_verified?"Verified":"Pending verification"}</span>{canWrite&&!doc.is_verified&&<button disabled={busy} className="icon-button" title="Verify" onClick={()=>verify(doc.id)}><ShieldCheck size={17}/></button>}{isAdmin()&&<button disabled={busy} className="icon-button text-red-600" title="Delete" onClick={()=>remove(doc.id)}><Trash2 size={17}/></button>}</div>)}</div>:<div className="empty-inline"><CheckCircle2/><span>No admission documents uploaded yet.</span></div>}</section>;
}
