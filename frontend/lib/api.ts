import axios, { AxiosError } from "axios";
import { clearSession, getToken } from "./auth";

export const api = axios.create({ baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000", timeout: 20000 });
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use((response) => response, (error: AxiosError) => {
  if (error.response?.status === 401 && typeof window !== "undefined") {
    clearSession();
    if (window.location.pathname !== "/login") window.location.assign("/login");
  }
  return Promise.reject(error);
});
export function apiErrorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) return "Something went wrong. Please try again.";
  const body = error.response?.data as { message?: string; detail?: string; errors?: { message: string }[] } | undefined;
  return body?.message || body?.detail || body?.errors?.[0]?.message || "Unable to complete the request.";
}
