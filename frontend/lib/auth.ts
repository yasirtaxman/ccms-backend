const TOKEN_KEY = "ccms_access_token";
const REMEMBERED_USERNAME_KEY = "ccms_remembered_username";
export const normalizeToken = (token: string | null) => {
  const value = token?.trim();
  if (!value) return null;
  return value.toLowerCase().startsWith("bearer ") ? value.slice(7).trim() : value;
};
export const getToken = () => typeof window === "undefined" ? null : normalizeToken(window.localStorage.getItem(TOKEN_KEY) ?? window.sessionStorage.getItem(TOKEN_KEY));
export const setToken = (token: string) => {
  if (typeof window === "undefined") return;
  const value = normalizeToken(token);
  if (!value) return;
  window.localStorage.setItem(TOKEN_KEY, value);
};
export const clearSession = () => {
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(TOKEN_KEY);
    window.sessionStorage.removeItem(TOKEN_KEY);
  }
};
export const getRememberedUsername = () => typeof window === "undefined" ? "" : window.localStorage.getItem(REMEMBERED_USERNAME_KEY) ?? "";
export const setRememberedUsername = (username: string) => { if (typeof window !== "undefined") window.localStorage.setItem(REMEMBERED_USERNAME_KEY, username); };
export const clearRememberedUsername = () => { if (typeof window !== "undefined") window.localStorage.removeItem(REMEMBERED_USERNAME_KEY); };
