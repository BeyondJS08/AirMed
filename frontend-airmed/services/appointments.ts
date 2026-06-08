import { apiFetch } from "@/lib/api";
import { Appointment } from "@/types";

export async function createAppointment(data: Partial<Appointment>) {
  return apiFetch("/api/v1/appointments/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function listAppointments(): Promise<Appointment[]> {
  return apiFetch("/api/v1/appointments/");
}

export async function cancelAppointment(id: number) {
  return apiFetch(`/api/v1/appointments/${id}`, {
    method: "DELETE",
  });
}
