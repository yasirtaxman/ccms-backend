const TOKEN_KEY = "ccms_access_token";
const REMEMBERED_USERNAME_KEY = "ccms_remembered_username";
export const getToken = () => typeof window === "undefined" ? null : window.localStorage.getItem(TOKEN_KEY);
export const setToken = (token: string) => window.localStorage.setItem(TOKEN_KEY, token);
export const clearSession = () => { if (typeof window !== "undefined") window.localStorage.removeItem(TOKEN_KEY); };
export const getRememberedUsername = () => typeof window === "undefined" ? "" : window.localStorage.getItem(REMEMBERED_USERNAME_KEY) ?? "";
export const setRememberedUsername = (username: string) => { if (typeof window !== "undefined") window.localStorage.setItem(REMEMBERED_USERNAME_KEY, username); };
export const clearRememberedUsername = () => { if (typeof window !== "undefined") window.localStorage.removeItem(REMEMBERED_USERNAME_KEY); };
