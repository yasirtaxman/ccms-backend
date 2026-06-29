"use client";
import { createContext, useCallback, useEffect, useMemo, useState } from "react";
import { api, setAuthTokenHeader } from "@/lib/api";
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
  const logout=useCallback(()=>{clearSession();setAuthTokenHeader(null);setUser(null);setPermissions(null);},[]);
  const refresh=useCallback(async()=>{
    const token=getToken(); if(!token){logout();setLoading(false);return;}
    setAuthTokenHeader(token);
    try { const [me,p]=await Promise.all([api.get<User>("/auth/me"),api.get<PermissionSummary>("/users/me/permissions")]); setUser(me.data);setPermissions(p.data); }
    catch (error) { logout(); throw error; } finally { setLoading(false); }
  },[logout]);
  useEffect(()=>{
    const token=getToken(); if(!token){queueMicrotask(()=>setLoading(false));return;}
    setAuthTokenHeader(token);
    void Promise.all([api.get<User>("/auth/me"),api.get<PermissionSummary>("/users/me/permissions")])
      .then(([me,p])=>{setUser(me.data);setPermissions(p.data);})
      .catch(()=>logout())
      .finally(()=>setLoading(false));
  },[logout]);
  const login=useCallback(async(username:string,password:string)=>{
    const form=new URLSearchParams({username,password});
    const response=await api.post<LoginResponse>("/auth/token",form,{headers:{"Content-Type":"application/x-www-form-urlencoded"}});
    if(!response.data.access_token||response.data.token_type.toLowerCase()!=="bearer")throw new Error("Invalid login response");
    setToken(response.data.access_token); setAuthTokenHeader(response.data.access_token); setLoading(true); await refresh();
  },[refresh]);
  const value=useMemo(()=>({user,permissions,loading,authenticated:Boolean(user),login,logout,refresh}),[user,permissions,loading,login,logout,refresh]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
