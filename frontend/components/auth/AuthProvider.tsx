"use client";
import { createContext, useCallback, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { clearSession, getToken, setToken } from "@/lib/auth";
import type { AuthState, LoginResponse, PermissionSummary, User } from "@/types/auth";

interface AuthContextValue extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}
export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user,setUser]=useState<User|null>(null); const [permissions,setPermissions]=useState<PermissionSummary|null>(null); const [loading,setLoading]=useState(true);
  const logout=useCallback(()=>{clearSession();setUser(null);setPermissions(null);},[]);
  const refresh=useCallback(async()=>{
    if(!getToken()){logout();setLoading(false);return;}
    try { const [me,p]=await Promise.all([api.get<User>("/auth/me"),api.get<PermissionSummary>("/users/me/permissions")]); setUser(me.data);setPermissions(p.data); }
    catch { logout(); } finally { setLoading(false); }
  },[logout]);
  useEffect(()=>{
    if(!getToken()){queueMicrotask(()=>setLoading(false));return;}
    void Promise.all([api.get<User>("/auth/me"),api.get<PermissionSummary>("/users/me/permissions")])
      .then(([me,p])=>{setUser(me.data);setPermissions(p.data);})
      .catch(()=>logout())
      .finally(()=>setLoading(false));
  },[logout]);
  const login=useCallback(async(username:string,password:string)=>{
    const form=new URLSearchParams({username,password});
    const response=await api.post<LoginResponse>("/auth/token",form,{headers:{"Content-Type":"application/x-www-form-urlencoded"}});
    setToken(response.data.access_token); setLoading(true); await refresh();
  },[refresh]);
  const value=useMemo(()=>({user,permissions,loading,authenticated:Boolean(user),login,logout,refresh}),[user,permissions,loading,login,logout,refresh]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
