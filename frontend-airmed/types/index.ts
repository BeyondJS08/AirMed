export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_professional: boolean;
}

export interface Appointment {
  id: number;
  professional_id: number;
  patient_id: number;
  start_time: string;
  end_time: string;
  status: string;
  notes: string | null;
  is_virtual: boolean;
  location: string | null;
  google_event_id: string | null;
}

export interface Availability {
  id: number;
  professional_id: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
  is_active: boolean;
}
