export interface User {
  id: number;
  email: string;
  full_name: string | null;
  phone_number: string | null;
  is_professional: boolean;
  is_active: boolean;
  timezone: string;
  google_id: string | null;
}

export interface Appointment {
  id: number;
  professional_id: number;
  patient_id: number;
  start_time: string;
  end_time: string;
  status: "scheduled" | "confirmed" | "completed" | "cancelled";
  notes: string | null;
  is_virtual: boolean;
  location: string | null;
  google_event_id: string | null;
}

export interface AppointmentCreate {
  professional_id: number;
  start_time: string;
  end_time: string;
  notes?: string | null;
  is_virtual?: boolean;
  location?: string | null;
}

export interface AppointmentUpdate {
  status?: string | null;
  notes?: string | null;
}

export interface Availability {
  id: number;
  professional_id: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
  is_active: boolean;
}

export interface AvailabilityCreate {
  day_of_week: number;
  start_time: string;
  end_time: string;
}

export interface ServiceItem {
  id: number;
  professional_id: number;
  name: string;
  description: string | null;
  duration_minutes: number;
  price: number | null;
  is_active: boolean;
}

export interface Slot {
  start: string;
  end: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ProfessionalIntegration {
  id: number;
  professional_id: number;
  provider: string;
  google_email: string | null;
  created_at: string;
  updated_at: string | null;
}
