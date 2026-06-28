import { apiFetch } from "@/lib/api"
import type { User } from "@/types"

export async function login(email: string, password: string) {
  return apiFetch<{ access_token: string; refresh_token: string }>(
    "/api/v1/auth/login",
    {
      method: "POST",
      body: JSON.stringify({ email, password }),
      auth: false,
    }
  )
}

export async function register(data: {
  email: string
  password: string
  full_name?: string
  is_professional?: boolean
}) {
  return apiFetch("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
    auth: false,
  })
}

export async function getCurrentUser(token?: string): Promise<User> {
  const headers: Record<string, string> = {}
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }
  return apiFetch<User>("/api/v1/users/me", { headers, auth: !!token })
}

export async function refresh(refreshToken: string) {
  return apiFetch<{ access_token: string; refresh_token: string }>(
    "/api/v1/auth/refresh",
    {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
      auth: false,
    }
  )
}
