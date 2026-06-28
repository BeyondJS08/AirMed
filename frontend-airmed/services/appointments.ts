import { apiFetch } from "@/lib/api"
import type { Appointment } from "@/types"

export async function createAppointment(data: {
  professional_id: number
  start_time: string
  end_time: string
  notes?: string | null
  is_virtual?: boolean
  location?: string | null
}) {
  return apiFetch<Appointment>("/api/v1/appointments/", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export async function listAppointments(params?: {
  status?: string
  date_from?: string
  date_to?: string
}): Promise<Appointment[]> {
  const searchParams = new URLSearchParams()
  if (params?.status) searchParams.set("status", params.status)
  if (params?.date_from) searchParams.set("date_from", params.date_from)
  if (params?.date_to) searchParams.set("date_to", params.date_to)
  const qs = searchParams.toString()
  return apiFetch<Appointment[]>(`/api/v1/appointments/${qs ? `?${qs}` : ""}`)
}

export async function getAppointment(id: number): Promise<Appointment> {
  return apiFetch<Appointment>(`/api/v1/appointments/${id}`)
}

export async function cancelAppointment(id: number) {
  return apiFetch(`/api/v1/appointments/${id}`, { method: "DELETE" })
}

export async function updateAppointment(
  id: number,
  data: { status?: string; notes?: string | null }
) {
  return apiFetch<Appointment>(`/api/v1/appointments/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  })
}
