import { api, setTokens, clearTokens } from "../api/client";
import { AuthResponse, User } from "../types";

export async function login(email: string, password: string): Promise<User> {
  const data = await api<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  await setTokens(data);
  const me = await api<User>("/users/me");
  return me;
}

export async function loginWithGoogle(idToken: string): Promise<User> {
  const data = await api<AuthResponse>("/auth/google", {
    method: "POST",
    body: JSON.stringify({ id_token: idToken }),
  });
  await setTokens(data);
  const me = await api<User>("/users/me");
  return me;
}

export async function register(
  email: string,
  password: string,
  fullName?: string,
): Promise<User> {
  const data = await api<AuthResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  await setTokens(data);
  const me = await api<User>("/users/me");
  return me;
}

export async function logout(): Promise<void> {
  await clearTokens();
}

export async function getMe(): Promise<User> {
  return api<User>("/users/me");
}
