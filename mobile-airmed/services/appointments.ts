import { api } from "../api/client";
import {
  Appointment,
  AppointmentCreate,
  AppointmentUpdate,
  Slot,
} from "../types";

export async function listAppointments(
  status?: string,
): Promise<Appointment[]> {
  const params = status ? `?status=${status}` : "";
  return api<Appointment[]>(`/appointments${params}`);
}

export async function getAppointment(id: number): Promise<Appointment> {
  return api<Appointment>(`/appointments/${id}`);
}

export async function createAppointment(
  data: AppointmentCreate,
): Promise<Appointment> {
  return api<Appointment>("/appointments", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateAppointmentStatus(
  id: number,
  status: string,
): Promise<Appointment> {
  return api<Appointment>(`/appointments/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export async function cancelAppointment(id: number): Promise<void> {
  return api<void>(`/appointments/${id}`, { method: "DELETE" });
}

export async function getAvailableSlots(
  professionalId: number,
  date: string,
  serviceId?: number,
): Promise<Slot[]> {
  let path = `/availability/slots?professional_id=${professionalId}&date=${date}`;
  if (serviceId) path += `&service_id=${serviceId}`;
  return api<Slot[]>(path);
}
