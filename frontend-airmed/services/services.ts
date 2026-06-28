import { apiFetch } from "@/lib/api"

export interface ServiceOut {
  id: number
  professional_id: number
  name: string
  description: string | null
  duration_minutes: number
  price: number | null
}

export interface ServiceCreate {
  name: string
  description?: string | null
  duration_minutes: number
  price?: number | null
}

export interface ServiceUpdate {
  name?: string
  description?: string | null
  duration_minutes?: number
  price?: number | null
}

export async function listServices(professionalId?: number): Promise<ServiceOut[]> {
  const params = professionalId ? `?professional_id=${professionalId}` : ""
  return apiFetch<ServiceOut[]>(`/api/v1/services/${params}`)
}

export async function createService(data: ServiceCreate): Promise<ServiceOut> {
  return apiFetch<ServiceOut>("/api/v1/services/", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export async function updateService(
  id: number,
  data: ServiceUpdate
): Promise<ServiceOut> {
  return apiFetch<ServiceOut>(`/api/v1/services/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  })
}

export async function deleteService(id: number) {
  return apiFetch(`/api/v1/services/${id}`, { method: "DELETE" })
}
