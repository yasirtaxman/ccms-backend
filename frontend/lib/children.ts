import { api } from "./api";
import type { Child,ChildCompleteProfile,ChildCreatePayload,ChildDocument,ChildUpdatePayload,ImportCommit,ImportPreview } from "@/types/children";
import type { AttendancePage,BulkAttendanceResult,DailyAttendance,MonthlyAttendance,TodayAttendanceSummary } from "@/types/attendance";
export const childrenApi={
  list:async()=> (await api.get<Child[]>("/children")).data,
  get:async(id:number)=> (await api.get<Child>(`/children/${id}`)).data,
  create:async(payload:ChildCreatePayload)=> (await api.post<Child>("/children",payload)).data,
  update:async(id:number,payload:ChildUpdatePayload)=> (await api.put<Child>(`/children/${id}`,payload)).data,
  summary:async(id:number)=> (await api.get<ChildCompleteProfile>(`/children/${id}/complete-profile-summary`)).data,
  documents:async(id:number)=> (await api.get<ChildDocument[]>(`/children/${id}/documents`)).data,
  uploadDocument:async(id:number,type:string,file:File)=>{const form=new FormData();form.append("child_id",String(id));form.append("document_type",type);form.append("file",file);return (await api.post<ChildDocument>("/documents/upload",form)).data},
  verifyDocument:async(id:number)=>api.post(`/documents/${id}/verify`),deleteDocument:async(id:number)=>api.delete(`/documents/${id}`),
  previewImport:async(file:File)=>{const form=new FormData();form.append("file",file);return (await api.post<ImportPreview>("/imports/children/preview",form)).data},
  commitImport:async(file:File)=>{const form=new FormData();form.append("file",file);return (await api.post<ImportCommit>("/imports/children/commit",form)).data},
  attendance:async(date:string)=> (await api.get<AttendancePage>("/daily-attendance",{params:{date,limit:500}})).data,
  childAttendance:async(id:number)=> (await api.get<DailyAttendance[]>(`/children/${id}/daily-attendance`)).data,
  todayAttendance:async()=> (await api.get<TodayAttendanceSummary>("/daily-attendance/today")).data,
  bulkAttendance:async(attendance_date:string,records:unknown[])=> (await api.post<BulkAttendanceResult>("/daily-attendance/bulk-mark",{attendance_date,records})).data,
  dailyReport:async(params:Record<string,string|number|undefined>)=> (await api.get("/reports/daily-attendance",{params})).data,
  monthlyReport:async(month:number,year:number,child_id?:number)=> (await api.get<MonthlyAttendance[]>("/reports/monthly-child-attendance",{params:{month,year,child_id}})).data,
};
export async function downloadAuthenticated(path:string,fallback:string){const response=await api.get<Blob>(path,{responseType:"blob"});const disposition=response.headers["content-disposition"] as string|undefined;const match=disposition?.match(/filename="?([^";]+)"?/);const filename=match?.[1]||fallback;const url=URL.createObjectURL(response.data);const link=document.createElement("a");link.href=url;link.download=filename;document.body.appendChild(link);link.click();link.remove();URL.revokeObjectURL(url)}
export const ageFromDate=(value:string)=>{const birth=new Date(`${value}T00:00:00`);const now=new Date();let age=now.getFullYear()-birth.getFullYear();if(now.getMonth()<birth.getMonth()||(now.getMonth()===birth.getMonth()&&now.getDate()<birth.getDate()))age--;return age};
