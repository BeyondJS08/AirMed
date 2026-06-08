import { apiFetch } from "@/lib/api";
import { User } from "@/types";

export async function login(email: string, password: string) {
  return apiFetch("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function register(data: { email: string; password: string; full_name?: string }) {
  return apiFetch("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getCurrentUser(): Promise<User> {
  return apiFetch("/api/v1/users/me");
}
