import * as SecureStore from "expo-secure-store";
import { API_URL } from "../constants";
import { AuthResponse } from "../types";

const TOKEN_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

let refreshPromise: Promise<string | null> | null = null;

async function getToken(): Promise<string | null> {
  return SecureStore.getItemAsync(TOKEN_KEY);
}

async function setTokens(auth: AuthResponse): Promise<void> {
  await SecureStore.setItemAsync(TOKEN_KEY, auth.access_token);
  await SecureStore.setItemAsync(REFRESH_KEY, auth.refresh_token);
}

async function clearTokens(): Promise<void> {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
  await SecureStore.deleteItemAsync(REFRESH_KEY);
}

async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    try {
      const refresh = await SecureStore.getItemAsync(REFRESH_KEY);
      if (!refresh) return null;
      const res = await fetch(`${API_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (!res.ok) {
        await clearTokens();
        return null;
      }
      const data: AuthResponse = await res.json();
      await setTokens(data);
      return data.access_token;
    } finally {
      refreshPromise = null;
    }
  })();
  return refreshPromise;
}

export interface ApiError {
  status: number;
  detail: string;
}

export async function api<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = await getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (res.status === 401 && token) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers["Authorization"] = `Bearer ${newToken}`;
      res = await fetch(`${API_URL}${path}`, { ...options, headers });
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw { status: res.status, detail: body.detail ?? "Request failed" } as ApiError;
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export { getToken, setTokens, clearTokens, refreshAccessToken };
