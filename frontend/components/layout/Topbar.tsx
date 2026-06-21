"use client";
import { Menu } from "lucide-react";
import { UserMenu } from "./UserMenu";
export function Topbar({onMenu}:{onMenu:()=>void}){return <header className="sticky top-0 z-20 flex h-20 items-center border-b border-slate-200 bg-white/90 px-4 backdrop-blur md:px-8"><button onClick={onMenu} className="mr-4 rounded-lg p-2 text-slate-600 hover:bg-slate-100 md:hidden" aria-label="Open navigation"><Menu/></button><div><h1 className="font-semibold text-slate-900">Child Care Management System</h1><p className="hidden text-sm text-slate-500 sm:block">Operational intelligence and child welfare administration</p></div><div className="ml-auto"><UserMenu/></div></header>}
