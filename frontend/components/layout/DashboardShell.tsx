"use client";
import { useState } from "react";
import { AppSidebar } from "./AppSidebar";
import { Topbar } from "./Topbar";
export function DashboardShell({children}:{children:React.ReactNode}){const [open,setOpen]=useState(false);return <div className="min-h-screen bg-slate-50"><AppSidebar open={open} onClose={()=>setOpen(false)}/><div className="md:pl-72"><Topbar onMenu={()=>setOpen(true)}/><main className="p-4 md:p-8">{children}</main></div></div>}
