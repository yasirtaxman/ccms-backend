import axios, { AxiosError } from "axios";
import { clearSession, getToken } from "./auth";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const development = process.env.NODE_ENV === "development";
if (development) console.info("[CCMS API] configuration", { baseURL: API_BASE_URL });

export const api = axios.create({ baseURL: API_BASE_URL, timeout: 20000 });
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use((response) => {
  if (development) console.info("[CCMS API] response", { status: response.status, category: "success" });
  return response;
}, (error: AxiosError) => {
  const category = !error.response ? "network" : error.response.status >= 500 ? "server" : error.response.status === 422 ? "validation" : error.response.status === 401 ? "authentication" : "http";
  if (development) console.info("[CCMS API] request failed", { status: error.response?.status ?? null, category });
  if (error.response?.status === 401 && typeof window !== "undefined") {
    clearSession();
    if (window.location.pathname !== "/login") window.location.assign("/login");
  }
  return Promise.reject(error);
});
export function apiErrorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) return "Something went wrong. Please try again.";
  const body = error.response?.data as { message?: string; detail?: string; errors?: { message: string }[] } | undefined;
  if (!error.response) return `Backend server is not reachable at ${API_BASE_URL}.`;
  if (error.response.status === 403) return "You do not have permission to perform this action.";
  return body?.errors?.[0]?.message || body?.detail || body?.message || "Unable to complete the request.";
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
