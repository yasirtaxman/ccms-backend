"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Building2, LayoutDashboard, X } from "lucide-react";
import { navigation } from "@/lib/routes";
import { cn } from "@/lib/utils";
import { usePermissions } from "@/hooks/usePermissions";
export function AppSidebar({open=false,onClose}:{open?:boolean;onClose?:()=>void}){const pathname=usePathname();const {canAccessMenu}=usePermissions();return <>
  {open&&<button aria-label="Close navigation" onClick={onClose} className="fixed inset-0 z-30 bg-slate-950/40 md:hidden"/>}
  <aside className={cn("fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-slate-200 bg-white transition-transform md:translate-x-0",open?"translate-x-0":"-translate-x-full")}>
    <div className="flex h-20 items-center gap-3 border-b border-slate-100 px-6"><div className="grid size-11 place-items-center rounded-xl bg-blue-700 text-white"><Building2/></div><div><div className="text-lg font-bold text-slate-900">CCMS</div><div className="text-xs text-slate-500">Child Care Management</div></div><button onClick={onClose} className="ml-auto md:hidden" aria-label="Close"><X/></button></div>
    <nav className="flex-1 overflow-y-auto px-4 py-5">{navigation.map(group=>{const items=group.items.filter(item=>canAccessMenu(item.roles,item.permission));if(!items.length)return null;return <div key={group.label} className="mb-6"><p className="px-3 text-[11px] font-semibold uppercase tracking-widest text-slate-400">{group.label}</p><div className="mt-2 space-y-1">{items.map(item=>{const active=item.href==="/dashboard"?pathname===item.href:pathname.startsWith(item.href);return <Link onClick={onClose} key={item.href} href={item.href} className={cn("flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium",active?"bg-blue-50 text-blue-700":"text-slate-600 hover:bg-slate-50 hover:text-slate-950")}><LayoutDashboard size={17}/>{item.label}</Link>})}</div></div>})}</nav>
    <div className="border-t border-slate-100 px-6 py-4 text-xs text-slate-400">CCMS API · Secure workspace</div>
  </aside></>}
