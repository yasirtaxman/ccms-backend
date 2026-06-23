"use client";
import { usePermissions } from "@/hooks/usePermissions";
export function PermissionGate({children,roles=[],fallback=null}:{children:React.ReactNode;roles?:string[];fallback?:React.ReactNode}){const {canAccessMenu,loading}=usePermissions();if(loading||!canAccessMenu(roles))return fallback;return children;}
