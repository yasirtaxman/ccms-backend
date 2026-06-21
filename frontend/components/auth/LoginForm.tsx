"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { LockKeyhole, UserRound } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { apiErrorMessage } from "@/lib/api";
const schema=z.object({username:z.string().min(1,"Enter your username"),password:z.string().min(1,"Enter your password")});
type Values=z.infer<typeof schema>;
export function LoginForm(){const router=useRouter();const {login,authenticated,loading}=useAuth();const [error,setError]=useState("");const {register,handleSubmit,formState:{errors,isSubmitting}}=useForm<Values>({resolver:zodResolver(schema)});
  useEffect(()=>{if(!loading&&authenticated)router.replace("/dashboard");},[loading,authenticated,router]);
  const submit=async(values:Values)=>{setError("");try{await login(values.username,values.password);router.replace("/dashboard");}catch(e){setError(apiErrorMessage(e));}};
  return <form onSubmit={handleSubmit(submit)} className="space-y-5" noValidate>
    {error&&<div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
    <label className="block text-sm font-medium text-slate-700">Username<div className="input-wrap"><UserRound size={18}/><input autoComplete="username" {...register("username")} placeholder="Enter username"/></div>{errors.username&&<span className="field-error">{errors.username.message}</span>}</label>
    <label className="block text-sm font-medium text-slate-700">Password<div className="input-wrap"><LockKeyhole size={18}/><input type="password" autoComplete="current-password" {...register("password")} placeholder="Enter password"/></div>{errors.password&&<span className="field-error">{errors.password.message}</span>}</label>
    <button disabled={isSubmitting} className="primary-button w-full">{isSubmitting?<><span className="small-spinner"/>Signing in…</>:"Sign in securely"}</button>
  </form>;
}
