import axios, { AxiosError, AxiosHeaders } from "axios";
import { clearSession, getToken, normalizeToken } from "./auth";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const development = process.env.NODE_ENV === "development";
if (development) console.info("[CCMS API] configuration", { baseURL: API_BASE_URL });

export const api = axios.create({ baseURL: API_BASE_URL, timeout: 20000 });
const publicPaths = ["/auth/token", "/auth/login", "/auth/register", "/health", "/health/readiness", "/openapi.json", "/"];
const isPublicRequest = (url?: string) => {
  if (!url) return false;
  const path = url.startsWith("http") ? new URL(url).pathname : url.split("?")[0];
  return publicPaths.some((item) => path === item || (item !== "/" && path.startsWith(`${item}/`)));
};
class SessionExpiredError extends Error {
  constructor() {
    super("Your session has expired. Please sign in again.");
    this.name = "SessionExpiredError";
  }
}
const expireSession = () => {
  if (typeof window === "undefined") return;
  clearSession();
  setAuthTokenHeader(null);
  if (window.location.pathname !== "/login") window.location.assign("/login");
};
export function setAuthTokenHeader(token: string | null) {
  const value = normalizeToken(token);
  if (value) api.defaults.headers.common["Authorization"] = `Bearer ${value}`;
  else delete api.defaults.headers.common.Authorization;
}
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    const headers = AxiosHeaders.from(config.headers);
    headers.set("Authorization", `Bearer ${token}`);
    if (!headers.has("Content-Type") && config.data && !(config.data instanceof FormData)) headers.set("Content-Type", "application/json");
    config.headers = headers;
  } else if (!isPublicRequest(config.url)) {
    expireSession();
    return Promise.reject(new SessionExpiredError());
  }
  if (development) {
    const headers = AxiosHeaders.from(config.headers);
    console.info("[CCMS API] request", {
      method: config.method,
      url: config.url,
      hasAuthHeader: headers.has("Authorization"),
      category: "request",
    });
  }
  return config;
});
api.interceptors.response.use((response) => {
  if (development) console.info("[CCMS API] response", { status: response.status, category: "success" });
  return response;
}, (error: AxiosError) => {
  const category = !error.response ? "network" : error.response.status >= 500 ? "server" : error.response.status === 422 ? "validation" : error.response.status === 401 ? "authentication" : "http";
  if (development) console.info("[CCMS API] request failed", { status: error.response?.status ?? null, category });
  if (error.response?.status === 401 && typeof window !== "undefined") {
    expireSession();
  }
  return Promise.reject(error);
});
export function apiErrorMessage(error: unknown): string {
  if (error instanceof SessionExpiredError) return error.message;
  if (!axios.isAxiosError(error)) return "Something went wrong. Please try again.";
  const body = error.response?.data as { message?: string; detail?: string | { msg?: string }[]; errors?: { message: string }[] } | undefined;
  const endpoint = error.config?.url || "requested endpoint";
  const detail = Array.isArray(body?.detail) ? body?.detail.map(item => item.msg).filter(Boolean).join("; ") : body?.detail;
  const backendMessage = body?.errors?.[0]?.message || detail || body?.message;
  if (!error.response) {
    if (error.code === "ECONNABORTED") return `The request to ${endpoint} timed out. The backend may be busy; please retry.`;
    return `Backend server is not reachable at ${API_BASE_URL}.`;
  }
  if (error.response.status === 401) return "Your session has expired. Please sign in again.";
  if (error.response.status === 403) return "You do not have permission to view this page.";
  if (error.response.status === 404) return backendMessage || "This page endpoint is not available.";
  if (error.response.status === 422) return backendMessage || "The request data is invalid for this endpoint.";
  if (error.response.status >= 500) return backendMessage || "This page returned a server error. Please check backend logs.";
  return backendMessage || `The request to ${endpoint} failed with status ${error.response.status}.`;
}

export function loginErrorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) return "Login request failed. Please check backend logs.";
  if (!error.response) return `Backend server is not reachable. Please start backend at ${API_BASE_URL}`;
  const status = error.response.status;
  const body = error.response.data as { message?: string; detail?: string; errors?: { message: string }[] } | undefined;
  if (status === 401 || status === 403) return "Invalid username or password";
  if (status === 422) return body?.errors?.[0]?.message || body?.detail || body?.message || "Login details are invalid.";
  if (status >= 500) return "Login request failed. Please check backend logs.";
  return body?.errors?.[0]?.message || body?.detail || body?.message || "Login request failed. Please check backend logs.";
}

export async function changePassword(currentPassword: string, newPassword: string) {
  const response = await api.post<{ message: string }>("/auth/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
    confirm_password: newPassword,
  });
  return response.data;
}
