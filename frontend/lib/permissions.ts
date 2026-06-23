import type { PermissionSummary } from "@/types/auth";
export const hasRole = (p: PermissionSummary | null, role: string) => Boolean(p?.roles.includes(role));
export const hasAnyRole = (p: PermissionSummary | null, roles: string[]) => roles.length === 0 || roles.some((role) => hasRole(p, role));
export const isAdmin = (p: PermissionSummary | null) => hasRole(p, "Admin");
export const isManager = (p: PermissionSummary | null) => hasRole(p, "Manager");
export const isViewer = (p: PermissionSummary | null) => hasRole(p, "Viewer");
export const hasPermission = (p:PermissionSummary|null,permission:string)=>Boolean(p&&(p.effective_permissions.includes("*")||p.effective_permissions.includes(permission)));
export const canAccessMenu = (p: PermissionSummary | null, roles: string[] = [], permission?: string) => {
  if (!p) return false;
  if (p.effective_permissions.includes("*")) return true;
  return permission ? hasPermission(p,permission) : hasAnyRole(p,roles);
};
