import { api } from "../api/client";
import { ServiceItem } from "../types";

export async function listServices(
  professionalId?: number,
): Promise<ServiceItem[]> {
  const params = professionalId ? `?professional_id=${professionalId}` : "";
  return api<ServiceItem[]>(`/services${params}`);
}

export async function createService(
  data: Omit<ServiceItem, "id" | "professional_id" | "is_active">,
): Promise<ServiceItem> {
  return api<ServiceItem>("/services", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateService(
  id: number,
  data: Partial<ServiceItem>,
): Promise<ServiceItem> {
  return api<ServiceItem>(`/services/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteService(id: number): Promise<void> {
  return api<void>(`/services/${id}`, { method: "DELETE" });
}
