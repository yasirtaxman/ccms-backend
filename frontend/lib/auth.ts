const TOKEN_KEY = "ccms_access_token";
export const getToken = () => typeof window === "undefined" ? null : window.localStorage.getItem(TOKEN_KEY);
export const setToken = (token: string) => window.localStorage.setItem(TOKEN_KEY, token);
export const clearSession = () => { if (typeof window !== "undefined") window.localStorage.removeItem(TOKEN_KEY); };
