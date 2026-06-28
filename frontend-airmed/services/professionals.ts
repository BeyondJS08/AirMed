import { apiFetch } from "@/lib/api"
import type { User } from "@/types"

export async function listProfessionals(): Promise<User[]> {
  return apiFetch<User[]>("/api/v1/users/professionals", { auth: false })
}
