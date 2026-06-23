"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
export function ProtectedRoute({children,roles=[]}:{children:React.ReactNode;roles?:string[]}){
  const router=useRouter();const {authenticated,loading,permissions}=useAuth();
  const allowed=roles.length===0||roles.some(role=>permissions?.roles.includes(role));
  useEffect(()=>{if(!loading&&!authenticated)router.replace("/login");else if(!loading&&authenticated&&!allowed)router.replace("/unauthorized");},[loading,authenticated,allowed,router]);
  if(loading||!authenticated||!allowed)return <div className="grid min-h-screen place-items-center bg-slate-50"><div className="loading-ring"/><span className="sr-only">Loading</span></div>;
  return children;
}
