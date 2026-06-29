import { api } from "../api/client";
import { Availability, AvailabilityCreate } from "../types";

export async function listAvailability(): Promise<Availability[]> {
  return api<Availability[]>("/availability");
}

export async function createAvailability(
  data: AvailabilityCreate,
): Promise<Availability> {
  return api<Availability>("/availability", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateAvailability(
  id: number,
  data: Partial<Availability>,
): Promise<Availability> {
  return api<Availability>(`/availability/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteAvailability(id: number): Promise<void> {
  return api<void>(`/availability/${id}`, { method: "DELETE" });
}

export async function getAvailableSlotsByDate(
  professionalId: number,
  date: string,
): Promise<{ start: string; end: string }[]> {
  return api<{ start: string; end: string }[]>(
    `/availability/slots?professional_id=${professionalId}&date=${date}`,
  );
}
