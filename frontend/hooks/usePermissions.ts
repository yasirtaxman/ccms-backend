"use client";
import { useAuth } from "./useAuth";
import { canAccessMenu, hasAnyRole, hasRole, isAdmin, isManager, isViewer } from "@/lib/permissions";
export function usePermissions(){const {permissions,loading}=useAuth();return {permissions,loading,hasRole:(r:string)=>hasRole(permissions,r),hasAnyRole:(r:string[])=>hasAnyRole(permissions,r),canAccessMenu:(r:string[]=[],p?:string)=>canAccessMenu(permissions,r,p),isAdmin:()=>isAdmin(permissions),isManager:()=>isManager(permissions),isViewer:()=>isViewer(permissions)};}
