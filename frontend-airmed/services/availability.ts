import { apiFetch } from "@/lib/api"
import type { Availability } from "@/types"

export async function listAvailabilities(): Promise<Availability[]> {
  return apiFetch<Availability[]>("/api/v1/availability/")
}

export async function createAvailability(data: {
  day_of_week: number
  start_time: string
  end_time: string
  is_active?: boolean
}) {
  return apiFetch<Availability>("/api/v1/availability/", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export async function updateAvailability(
  id: number,
  data: {
    day_of_week?: number
    start_time?: string
    end_time?: string
    is_active?: boolean
  }
) {
  return apiFetch<Availability>(`/api/v1/availability/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  })
}

export async function deleteAvailability(id: number) {
  return apiFetch(`/api/v1/availability/${id}`, { method: "DELETE" })
}

export async function getAvailableSlots(
  professionalId: number,
  date: string,
  serviceId?: number
) {
  const params = new URLSearchParams({
    professional_id: String(professionalId),
    date,
  })
  if (serviceId) params.set("service_id", String(serviceId))
  return apiFetch<{ start_time: string; end_time: string }[]>(
    `/api/v1/availability/available-slots?${params}`
  )
}
