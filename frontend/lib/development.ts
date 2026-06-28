import { api } from "@/lib/api";
import type { DevelopmentIndicator,DevelopmentObservation,DevelopmentObservationPayload,DevelopmentReport,DevelopmentSummary } from "@/types/development";

export const developmentApi={
  indicators:async(include_inactive=false)=>(await api.get<DevelopmentIndicator[]>("/development-indicators",{params:{include_inactive}})).data,
  createIndicator:async(payload:Partial<DevelopmentIndicator>)=>(await api.post<DevelopmentIndicator>("/development-indicators",payload)).data,
  updateIndicator:async(id:number,payload:Partial<DevelopmentIndicator>)=>(await api.put<DevelopmentIndicator>(`/development-indicators/${id}`,payload)).data,
  activateIndicator:async(id:number)=>(await api.post<DevelopmentIndicator>(`/development-indicators/${id}/activate`)).data,
  deactivateIndicator:async(id:number)=>(await api.post<DevelopmentIndicator>(`/development-indicators/${id}/deactivate`)).data,
  observations:async(params:Record<string,string|number|undefined>={})=>(await api.get<DevelopmentObservation[]>("/child-development-observations",{params})).data,
  createObservation:async(payload:DevelopmentObservationPayload)=>(await api.post<DevelopmentObservation>("/child-development-observations",payload)).data,
  getObservation:async(id:number)=>(await api.get<DevelopmentObservation>(`/child-development-observations/${id}`)).data,
  updateObservation:async(id:number,payload:Partial<DevelopmentObservationPayload>)=>(await api.put<DevelopmentObservation>(`/child-development-observations/${id}`,payload)).data,
  submit:async(id:number)=>(await api.post<DevelopmentObservation>(`/child-development-observations/${id}/submit`)).data,
  review:async(id:number,review_status:"Reviewed"|"Needs Follow-up",recommended_support?:string)=>(await api.post<DevelopmentObservation>(`/child-development-observations/${id}/review`,{review_status,recommended_support})).data,
  close:async(id:number)=>(await api.post<DevelopmentObservation>(`/child-development-observations/${id}/close`)).data,
  archive:async(id:number)=>(await api.post<DevelopmentObservation>(`/child-development-observations/${id}/archive`)).data,
  childSummary:async(id:number)=>(await api.get<DevelopmentSummary>(`/children/${id}/development-summary`)).data,
  childObservations:async(id:number)=>(await api.get<DevelopmentObservation[]>(`/children/${id}/development-observations`)).data,
  dashboard:async()=>(await api.get<Record<string,number>>("/dashboard/development")).data,
  report:async(params:Record<string,string|number|undefined>={})=>(await api.get<DevelopmentReport>("/reports/child-development",{params})).data,
  missing:async(params:Record<string,string|number|undefined>={})=>(await api.get<DevelopmentReport["missing_monthly_observations"]>("/reports/monthly-development-missing",{params})).data,
  talent:async(params:Record<string,string|number|undefined>={})=>(await api.get<DevelopmentReport["talent_summary"]>("/reports/child-talent-summary",{params})).data,
};
