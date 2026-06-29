# Mobile App (Expo) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a patient + professional mobile app with Expo, sharing the existing FastAPI backend.

**Architecture:** Fresh Expo scaffold with expo-router for file-based routing. Zustand for auth state, React Query for server state. No monorepo — independent `mobile-airmed/` directory that mirrors the web frontend's API patterns.

**Tech Stack:** Expo SDK 52+, expo-router, TypeScript, @tanstack/react-query, zustand, expo-secure-store, expo-auth-session, Jest, @testing-library/react-native

---

### Task 1: Scaffold + Dependencies

**Files:**
- Create: `mobile-airmed/` (entire directory via npx)

- [ ] **Step 1: Create Expo project**

```bash
cd /home/bjs/Repositories/university/AirMed
npx create-expo-app@latest mobile-airmed --template blank-typescript
```

- [ ] **Step 2: Install core dependencies**

```bash
cd mobile-airmed
npx expo install expo-router expo-linking expo-constants expo-status-bar
npx expo install expo-secure-store expo-auth-session expo-web-browser
npm install @tanstack/react-query zustand
npm install @react-navigation/native @react-navigation/bottom-tabs
npm install --save-dev jest @testing-library/react-native @testing-library/jest-native
```

- [ ] **Step 3: Configure expo-router in `app.json`**

```json
{
  "expo": {
    "scheme": "airmed",
    "plugins": ["expo-router", "expo-secure-store"],
    "experiments": {
      "typedRoutes": true
    }
  }
}
```

Merge with the existing `app.json` that was created by the scaffold.

- [ ] **Step 4: Verify the app runs**

```bash
npx expo start --no-dev --minify 2>&1 | head -20
```
Expected: Metro bundler starts without errors

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: scaffold Expo mobile app"
```

---

### Task 2: Types + API Client

**Files:**
- Create: `mobile-airmed/src/types/index.ts`
- Create: `mobile-airmed/src/api/client.ts`
- Create: `mobile-airmed/src/constants/index.ts`

- [ ] **Step 1: Create type definitions `src/types/index.ts`**

```typescript
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
```

- [ ] **Step 2: Create API constants `src/constants/index.ts`**

```typescript
import Constants from "expo-constants";

const API_BASE = Constants.expoConfig?.extra?.apiUrl ?? "http://localhost:8000";

export const API_URL = `${API_BASE}/api/v1`;
```

- [ ] **Step 3: Create API client `src/api/client.ts`**

```typescript
import * as SecureStore from "expo-secure-store";
import { API_URL } from "../constants";
import { AuthResponse } from "../types";

const TOKEN_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

let refreshPromise: Promise<string | null> | null = null;

async function getToken(): Promise<string | null> {
  return SecureStore.getItemAsync(TOKEN_KEY);
}

async function setTokens(auth: AuthResponse): Promise<void> {
  await SecureStore.setItemAsync(TOKEN_KEY, auth.access_token);
  await SecureStore.setItemAsync(REFRESH_KEY, auth.refresh_token);
}

async function clearTokens(): Promise<void> {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
  await SecureStore.deleteItemAsync(REFRESH_KEY);
}

async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    try {
      const refresh = await SecureStore.getItemAsync(REFRESH_KEY);
      if (!refresh) return null;
      const res = await fetch(`${API_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (!res.ok) {
        await clearTokens();
        return null;
      }
      const data: AuthResponse = await res.json();
      await setTokens(data);
      return data.access_token;
    } finally {
      refreshPromise = null;
    }
  })();
  return refreshPromise;
}

export interface ApiError {
  status: number;
  detail: string;
}

export async function api<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = await getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (res.status === 401 && token) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers["Authorization"] = `Bearer ${newToken}`;
      res = await fetch(`${API_URL}${path}`, { ...options, headers });
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw { status: res.status, detail: body.detail ?? "Request failed" } as ApiError;
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export { getToken, setTokens, clearTokens, refreshAccessToken };
```

- [ ] **Step 4: Verify module resolution**

```bash
npx tsc --noEmit 2>&1
```
Expected: No type errors (or minor warnings about unused imports)

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add types, API client, and constants for mobile app"
```

---

### Task 3: Domain Services

**Files:**
- Create: `mobile-airmed/src/services/auth.ts`
- Create: `mobile-airmed/src/services/appointments.ts`
- Create: `mobile-airmed/src/services/professionals.ts`
- Create: `mobile-airmed/src/services/services.ts`
- Create: `mobile-airmed/src/services/availability.ts`

- [ ] **Step 1: Create `src/services/auth.ts`**

```typescript
import { api, setTokens, clearTokens } from "../api/client";
import { AuthResponse, User } from "../types";

export async function login(email: string, password: string): Promise<User> {
  const data = await api<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  await setTokens(data);
  const me = await api<User>("/users/me");
  return me;
}

export async function register(
  email: string,
  password: string,
  fullName?: string,
): Promise<User> {
  const data = await api<AuthResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  await setTokens(data);
  const me = await api<User>("/users/me");
  return me;
}

export async function logout(): Promise<void> {
  await clearTokens();
}

export async function getMe(): Promise<User> {
  return api<User>("/users/me");
}
```

- [ ] **Step 2: Create `src/services/appointments.ts`**

```typescript
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
```

- [ ] **Step 3: Create `src/services/professionals.ts`**

```typescript
import { api } from "../api/client";
import { User } from "../types";

export async function listProfessionals(): Promise<User[]> {
  return api<User[]>("/users/professionals");
}
```

- [ ] **Step 4: Create `src/services/services.ts`**

```typescript
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
```

- [ ] **Step 5: Create `src/services/availability.ts`**

```typescript
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
```

- [ ] **Step 6: Verify no type errors**

```bash
npx tsc --noEmit 2>&1 | head -30
```
Expected: No errors

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: add domain services for mobile app"
```

---

### Task 4: Auth Store + Screen + Root Layout

**Files:**
- Create: `mobile-airmed/src/stores/authStore.ts`
- Create: `mobile-airmed/app/index.tsx`
- Create: `mobile-airmed/app/_layout.tsx`

- [ ] **Step 1: Create auth store `src/stores/authStore.ts`**

```typescript
import { create } from "zustand";
import { User } from "../types";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  setLoading: (isLoading) => set({ isLoading }),
  logout: () => set({ user: null, isAuthenticated: false }),
}));
```

- [ ] **Step 2: Create root layout `app/_layout.tsx`**

```typescript
import { useEffect } from "react";
import { Stack } from "expo-router";
import { ActivityIndicator, View } from "react-native";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAuthStore } from "../src/stores/authStore";
import { getMe } from "../src/services/auth";
import { getToken } from "../src/api/client";

const queryClient = new QueryClient();

function AuthGate({ children }: { children: React.ReactNode }) {
  const { setUser, setLoading, isLoading, isAuthenticated } = useAuthStore();

  useEffect(() => {
    (async () => {
      const token = await getToken();
      if (token) {
        try {
          const user = await getMe();
          setUser(user);
        } catch {
          // Token invalid, stay unauthenticated
        }
      }
      setLoading(false);
    })();
  }, []);

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return <>{children}</>;
}

export default function RootLayout() {
  const { isAuthenticated } = useAuthStore();
  return (
    <QueryClientProvider client={queryClient}>
      <AuthGate>
        <Stack screenOptions={{ headerShown: false }}>
          {!isAuthenticated ? (
            <Stack.Screen name="index" options={{ title: "Login" }} />
          ) : null}
        </Stack>
      </AuthGate>
    </QueryClientProvider>
  );
}
```

- [ ] **Step 3: Create login screen `app/index.tsx`**

```typescript
import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { router } from "expo-router";
import { login } from "../src/services/auth";
import { useAuthStore } from "../src/stores/authStore";

export default function LoginScreen() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const { setUser } = useAuthStore();

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert("Error", "Please enter email and password");
      return;
    }
    setLoading(true);
    try {
      const user = await login(email, password);
      setUser(user);
      router.replace(user.is_professional ? "/professional/appointments" : "/patient/appointments");
    } catch (err: any) {
      Alert.alert("Login Failed", err.detail ?? "Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <View style={styles.content}>
        <Text style={styles.title}>AirMed</Text>
        <Text style={styles.subtitle}>Appointment Scheduling</Text>
        <TextInput
          style={styles.input}
          placeholder="Email"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
        />
        <TextInput
          style={styles.input}
          placeholder="Password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />
        {loading ? (
          <ActivityIndicator size="large" style={{ marginTop: 16 }} />
        ) : (
          <TouchableOpacity style={styles.button} onPress={handleLogin}>
            <Text style={styles.buttonText}>Sign In</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity
          onPress={() => router.push("/register" as any)}
          style={{ marginTop: 16 }}
        >
          <Text style={styles.link}>Don't have an account? Register</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  content: {
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: 24,
  },
  title: {
    fontSize: 32,
    fontWeight: "bold",
    textAlign: "center",
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: "#666",
    textAlign: "center",
    marginBottom: 32,
  },
  input: {
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    padding: 14,
    fontSize: 16,
    marginBottom: 12,
  },
  button: {
    backgroundColor: "#007AFF",
    borderRadius: 8,
    padding: 16,
    alignItems: "center",
    marginTop: 8,
  },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "600" },
  link: { color: "#007AFF", textAlign: "center", fontSize: 14 },
});
```

- [ ] **Step 4: Verify the app builds**

```bash
npx tsc --noEmit 2>&1 | head -30
```
Expected: No type errors

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add auth store, root layout, and login screen"
```

---

### Task 5: Patient Screens

**Files:**
- Create: `mobile-airmed/app/patient/_layout.tsx`
- Create: `mobile-airmed/app/patient/appointments.tsx`
- Create: `mobile-airmed/app/patient/book.tsx`
- Create: `mobile-airmed/app/patient/profile.tsx`

- [ ] **Step 1: Create patient tab layout `app/patient/_layout.tsx`**

```typescript
import { Tabs } from "expo-router";
import { Text } from "react-native";

export default function PatientLayout() {
  return (
    <Tabs>
      <Tabs.Screen
        name="appointments"
        options={{
          title: "Appointments",
          tabBarIcon: () => <Text>📅</Text>,
        }}
      />
      <Tabs.Screen
        name="book"
        options={{
          title: "Book",
          tabBarIcon: () => <Text>➕</Text>,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: "Profile",
          tabBarIcon: () => <Text>👤</Text>,
        }}
      />
    </Tabs>
  );
}
```

- [ ] **Step 2: Create appointments list screen `app/patient/appointments.tsx`**

```typescript
import { useState, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from "react-native";
import { useFocusEffect } from "expo-router";
import { listAppointments, cancelAppointment } from "../../src/services/appointments";
import { Appointment } from "../../src/types";

export default function PatientAppointmentsScreen() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"upcoming" | "past">("upcoming");

  const fetchAppts = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listAppointments();
      setAppointments(data);
    } catch (err: any) {
      Alert.alert("Error", err.detail ?? "Failed to load appointments");
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { fetchAppts(); }, [fetchAppts]));

  const now = new Date().toISOString();
  const filtered = appointments.filter((a) =>
    tab === "upcoming"
      ? a.start_time > now && a.status !== "cancelled"
      : a.start_time <= now || a.status === "cancelled",
  );

  const handleCancel = (id: number) => {
    Alert.alert("Cancel Appointment", "Are you sure?", [
      { text: "No", style: "cancel" },
      {
        text: "Yes",
        style: "destructive",
        onPress: async () => {
          try {
            await cancelAppointment(id);
            fetchAppts();
          } catch (err: any) {
            Alert.alert("Error", err.detail ?? "Cancel failed");
          }
        },
      },
    ]);
  };

  const renderItem = ({ item }: { item: Appointment }) => (
    <View style={styles.card}>
      <Text style={styles.date}>
        {new Date(item.start_time).toLocaleDateString()}{" "}
        {new Date(item.start_time).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        })}
      </Text>
      <Text style={styles.status}>
        Status: {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
      </Text>
      {item.is_virtual && <Text style={styles.virtual}>Virtual</Text>}
      {item.location && <Text>📍 {item.location}</Text>}
      {item.start_time > now && item.status !== "cancelled" && (
        <TouchableOpacity
          style={styles.cancelBtn}
          onPress={() => handleCancel(item.id)}
        >
          <Text style={styles.cancelText}>Cancel</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.tabRow}>
        <TouchableOpacity
          style={[styles.tab, tab === "upcoming" && styles.activeTab]}
          onPress={() => setTab("upcoming")}
        >
          <Text style={[styles.tabText, tab === "upcoming" && styles.activeTabText]}>
            Upcoming
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, tab === "past" && styles.activeTab]}
          onPress={() => setTab("past")}
        >
          <Text style={[styles.tabText, tab === "past" && styles.activeTabText]}>
            Past
          </Text>
        </TouchableOpacity>
      </View>
      <FlatList
        data={filtered}
        renderItem={renderItem}
        keyExtractor={(item) => item.id.toString()}
        ListEmptyComponent={
          <Text style={styles.empty}>No {tab} appointments</Text>
        }
        contentContainerStyle={filtered.length === 0 ? styles.center : undefined}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f5f5f5" },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  tabRow: { flexDirection: "row", backgroundColor: "#fff", paddingTop: 8 },
  tab: { flex: 1, paddingVertical: 12, alignItems: "center" },
  activeTab: { borderBottomWidth: 2, borderBottomColor: "#007AFF" },
  tabText: { fontSize: 16, color: "#666" },
  activeTabText: { color: "#007AFF", fontWeight: "600" },
  card: {
    backgroundColor: "#fff",
    marginHorizontal: 16,
    marginTop: 12,
    padding: 16,
    borderRadius: 12,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  date: { fontSize: 16, fontWeight: "600" },
  status: { fontSize: 14, color: "#666", marginTop: 4 },
  virtual: { fontSize: 14, color: "#007AFF", marginTop: 2 },
  cancelBtn: {
    marginTop: 12,
    backgroundColor: "#FF3B30",
    borderRadius: 8,
    padding: 10,
    alignItems: "center",
  },
  cancelText: { color: "#fff", fontWeight: "600" },
  empty: { textAlign: "center", color: "#999", marginTop: 32 },
});
```

- [ ] **Step 3: Create booking screen `app/patient/book.tsx`**

```typescript
import { useState, useEffect } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from "react-native";
import { router } from "expo-router";
import { listProfessionals } from "../../src/services/professionals";
import { listServices } from "../../src/services/services";
import { getAvailableSlotsByDate } from "../../src/services/availability";
import { createAppointment } from "../../src/services/appointments";
import { User, ServiceItem } from "../../src/types";

type Step = "professional" | "service" | "slot" | "confirm";

export default function BookScreen() {
  const [step, setStep] = useState<Step>("professional");
  const [professionals, setProfessionals] = useState<User[]>([]);
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [slots, setSlots] = useState<{ start: string; end: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPro, setSelectedPro] = useState<User | null>(null);
  const [selectedService, setSelectedService] = useState<ServiceItem | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<{ start: string; end: string } | null>(null);

  useEffect(() => {
    if (step === "professional") {
      setLoading(true);
      listProfessionals()
        .then(setProfessionals)
        .catch(() => Alert.alert("Error", "Failed to load professionals"))
        .finally(() => setLoading(false));
    }
  }, [step]);

  const selectProfessional = (pro: User) => {
    setSelectedPro(pro);
    setStep("service");
    setLoading(true);
    listServices(pro.id)
      .then(setServices)
      .catch(() => Alert.alert("Error", "Failed to load services"))
      .finally(() => setLoading(false));
  };

  const selectService = (svc: ServiceItem) => {
    setSelectedService(svc);
    setStep("slot");
    setLoading(true);
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dateStr = tomorrow.toISOString().split("T")[0];
    getAvailableSlotsByDate(selectedPro!.id, dateStr)
      .then(setSlots)
      .catch(() => Alert.alert("Error", "Failed to load slots"))
      .finally(() => setLoading(false));
  };

  const selectSlot = (slot: { start: string; end: string }) => {
    setSelectedSlot(slot);
    setStep("confirm");
  };

  const confirmBooking = async () => {
    if (!selectedPro || !selectedSlot) return;
    try {
      await createAppointment({
        professional_id: selectedPro.id,
        start_time: selectedSlot.start,
        end_time: selectedSlot.end,
      });
      Alert.alert("Success", "Appointment booked!", [
        { text: "OK", onPress: () => router.back() },
      ]);
    } catch (err: any) {
      Alert.alert("Error", err.detail ?? "Booking failed");
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.stepTitle}>
        {step === "professional"
          ? "Select Professional"
          : step === "service"
            ? "Select Service"
            : step === "slot"
              ? "Select Time"
              : "Confirm Booking"}
      </Text>
      {step === "professional" && (
        <FlatList
          data={professionals}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.itemCard}
              onPress={() => selectProfessional(item)}
            >
              <Text style={styles.itemName}>{item.full_name ?? "Professional"}</Text>
            </TouchableOpacity>
          )}
        />
      )}
      {step === "service" && (
        <FlatList
          data={services}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.itemCard}
              onPress={() => selectService(item)}
            >
              <Text style={styles.itemName}>{item.name}</Text>
              <Text style={styles.itemDetail}>
                {item.duration_minutes} min{item.price ? ` - $${item.price}` : ""}
              </Text>
            </TouchableOpacity>
          )}
        />
      )}
      {step === "slot" && (
        <FlatList
          data={slots}
          keyExtractor={(item) => item.start}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.itemCard}
              onPress={() => selectSlot(item)}
            >
              <Text>
                {new Date(item.start).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}{" "}
                -{" "}
                {new Date(item.end).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </Text>
            </TouchableOpacity>
          )}
        />
      )}
      {step === "confirm" && (
        <View style={styles.confirmCard}>
          <Text style={styles.confirmLabel}>
            Professional: {selectedPro?.full_name}
          </Text>
          <Text style={styles.confirmLabel}>
            Service: {selectedService?.name}
          </Text>
          <Text style={styles.confirmLabel}>
            Time: {selectedSlot?.start} - {selectedSlot?.end}
          </Text>
          <TouchableOpacity style={styles.confirmBtn} onPress={confirmBooking}>
            <Text style={styles.confirmBtnText}>Confirm Booking</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f5f5f5", padding: 16 },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  stepTitle: { fontSize: 20, fontWeight: "bold", marginBottom: 16 },
  itemCard: {
    backgroundColor: "#fff",
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  itemName: { fontSize: 16, fontWeight: "600" },
  itemDetail: { fontSize: 14, color: "#666", marginTop: 4 },
  confirmCard: {
    backgroundColor: "#fff",
    padding: 24,
    borderRadius: 12,
  },
  confirmLabel: { fontSize: 16, marginBottom: 8 },
  confirmBtn: {
    backgroundColor: "#007AFF",
    borderRadius: 8,
    padding: 16,
    alignItems: "center",
    marginTop: 16,
  },
  confirmBtnText: { color: "#fff", fontSize: 16, fontWeight: "600" },
});
```

- [ ] **Step 4: Create profile screen `app/patient/profile.tsx`**

```typescript
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { router } from "expo-router";
import { useAuthStore } from "../../src/stores/authStore";
import { logout } from "../../src/services/auth";

export default function ProfileScreen() {
  const { user, logout: clearUser } = useAuthStore();

  const handleLogout = async () => {
    await logout();
    clearUser();
    router.replace("/");
  };

  return (
    <View style={styles.container}>
      <Text style={styles.name}>{user?.full_name ?? "User"}</Text>
      <Text style={styles.email}>{user?.email}</Text>
      <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
        <Text style={styles.logoutText}>Logout</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff", padding: 24, justifyContent: "center" },
  name: { fontSize: 24, fontWeight: "bold", textAlign: "center" },
  email: { fontSize: 16, color: "#666", textAlign: "center", marginTop: 8 },
  logoutBtn: {
    backgroundColor: "#FF3B30",
    borderRadius: 8,
    padding: 16,
    alignItems: "center",
    marginTop: 32,
  },
  logoutText: { color: "#fff", fontSize: 16, fontWeight: "600" },
});
```

- [ ] **Step 5: Verify the app builds**

```bash
npx tsc --noEmit 2>&1 | head -30
```
Expected: No type errors

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: add patient screens (appointments, book, profile)"
```

---

### Task 6: Professional Screens

**Files:**
- Create: `mobile-airmed/app/professional/_layout.tsx`
- Create: `mobile-airmed/app/professional/appointments.tsx`
- Create: `mobile-airmed/app/professional/availability.tsx`
- Create: `mobile-airmed/app/professional/services.tsx`
- Create: `mobile-airmed/app/professional/integrations.tsx`

- [ ] **Step 1: Create professional tab layout `app/professional/_layout.tsx`**

```typescript
import { Tabs } from "expo-router";
import { Text } from "react-native";

export default function ProfessionalLayout() {
  return (
    <Tabs>
      <Tabs.Screen
        name="appointments"
        options={{ title: "Agenda", tabBarIcon: () => <Text>📅</Text> }}
      />
      <Tabs.Screen
        name="availability"
        options={{ title: "Hours", tabBarIcon: () => <Text>🕐</Text> }}
      />
      <Tabs.Screen
        name="services"
        options={{ title: "Services", tabBarIcon: () => <Text>💼</Text> }}
      />
      <Tabs.Screen
        name="integrations"
        options={{ title: "Integrations", tabBarIcon: () => <Text>🔗</Text> }}
      />
    </Tabs>
  );
}
```

- [ ] **Step 2: Create professional appointments screen `app/professional/appointments.tsx`**

```typescript
import { useState, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from "react-native";
import { useFocusEffect } from "expo-router";
import {
  listAppointments,
  updateAppointmentStatus,
} from "../../src/services/appointments";
import { Appointment } from "../../src/types";

export default function ProAppointmentsScreen() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAppts = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listAppointments();
      setAppointments(data);
    } catch (err: any) {
      Alert.alert("Error", err.detail ?? "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { fetchAppts(); }, [fetchAppts]));

  const handleStatus = async (id: number, status: string) => {
    try {
      await updateAppointmentStatus(id, status);
      fetchAppts();
    } catch (err: any) {
      Alert.alert("Error", err.detail ?? "Update failed");
    }
  };

  const renderItem = ({ item }: { item: Appointment }) => (
    <View style={styles.card}>
      <Text style={styles.date}>
        {new Date(item.start_time).toLocaleDateString()}{" "}
        {new Date(item.start_time).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        })}
      </Text>
      <Text>Patient #{item.patient_id}</Text>
      <Text style={styles.status}>
        Status: {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
      </Text>
      {item.notes && <Text style={styles.notes}>Notes: {item.notes}</Text>}
      <View style={styles.actionRow}>
        {item.status === "scheduled" && (
          <TouchableOpacity
            style={[styles.actionBtn, styles.confirmBtn]}
            onPress={() => handleStatus(item.id, "confirmed")}
          >
            <Text style={styles.actionText}>Confirm</Text>
          </TouchableOpacity>
        )}
        {item.status === "confirmed" && (
          <TouchableOpacity
            style={[styles.actionBtn, styles.completeBtn]}
            onPress={() => handleStatus(item.id, "completed")}
          >
            <Text style={styles.actionText}>Complete</Text>
          </TouchableOpacity>
        )}
        {(item.status === "scheduled" || item.status === "confirmed") && (
          <TouchableOpacity
            style={[styles.actionBtn, styles.cancelBtn]}
            onPress={() => handleStatus(item.id, "cancelled")}
          >
            <Text style={styles.actionText}>Cancel</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={appointments}
        renderItem={renderItem}
        keyExtractor={(item) => item.id.toString()}
        ListEmptyComponent={<Text style={styles.empty}>No appointments</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f5f5f5", padding: 16 },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  card: {
    backgroundColor: "#fff",
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  date: { fontSize: 16, fontWeight: "600" },
  status: { fontSize: 14, color: "#666", marginTop: 4 },
  notes: { fontSize: 14, color: "#333", marginTop: 4, fontStyle: "italic" },
  actionRow: { flexDirection: "row", marginTop: 12, gap: 8 },
  actionBtn: {
    flex: 1,
    padding: 10,
    borderRadius: 8,
    alignItems: "center",
  },
  confirmBtn: { backgroundColor: "#34C759" },
  completeBtn: { backgroundColor: "#007AFF" },
  cancelBtn: { backgroundColor: "#FF3B30" },
  actionText: { color: "#fff", fontWeight: "600" },
  empty: { textAlign: "center", color: "#999", marginTop: 32 },
});
```

- [ ] **Step 3: Create availability screen `app/professional/availability.tsx`**

```typescript
import { useState, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from "react-native";
import { useFocusEffect } from "expo-router";
import {
  listAvailability,
  deleteAvailability,
  createAvailability,
} from "../../src/services/availability";
import { Availability } from "../../src/types";

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export default function AvailabilityScreen() {
  const [avail, setAvail] = useState<Availability[]>([]);
  const [loading, setLoading] = useState(true);
  const [newDay, setNewDay] = useState(1);
  const [newStart, setNewStart] = useState("09:00");
  const [newEnd, setNewEnd] = useState("18:00");

  const fetchAvail = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listAvailability();
      setAvail(data);
    } catch {
      Alert.alert("Error", "Failed to load availability");
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { fetchAvail(); }, [fetchAvail]));

  const handleAdd = async () => {
    try {
      await createAvailability({
        day_of_week: newDay,
        start_time: newStart,
        end_time: newEnd,
      });
      fetchAvail();
    } catch (err: any) {
      Alert.alert("Error", err.detail ?? "Failed to add");
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteAvailability(id);
      fetchAvail();
    } catch {
      Alert.alert("Error", "Failed to delete");
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={avail}
        keyExtractor={(item) => item.id.toString()}
        ListHeaderComponent={
          <View style={styles.addCard}>
            <Text style={styles.sectionTitle}>Add Hours</Text>
            <View style={styles.pickerRow}>
              {DAYS.map((d, i) => (
                <TouchableOpacity
                  key={i}
                  style={[styles.dayBtn, newDay === i && styles.selectedDay]}
                  onPress={() => setNewDay(i)}
                >
                  <Text
                    style={[
                      styles.dayBtnText,
                      newDay === i && styles.selectedDayText,
                    ]}
                  >
                    {d}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
            <Text style={styles.label}>Start (HH:MM)</Text>
            <TextInput
              style={styles.input}
              value={newStart}
              onChangeText={setNewStart}
              placeholder="09:00"
            />
            <Text style={styles.label}>End (HH:MM)</Text>
            <TextInput
              style={styles.input}
              value={newEnd}
              onChangeText={setNewEnd}
              placeholder="18:00"
            />
            <TouchableOpacity style={styles.addBtn} onPress={handleAdd}>
              <Text style={styles.addBtnText}>Add</Text>
            </TouchableOpacity>
          </View>
        }
        renderItem={({ item }) => (
          <View style={styles.availCard}>
            <Text style={styles.availDay}>{DAYS[item.day_of_week]}</Text>
            <Text style={styles.availTime}>
              {item.start_time} - {item.end_time}
            </Text>
            <TouchableOpacity onPress={() => handleDelete(item.id)}>
              <Text style={styles.deleteText}>Delete</Text>
            </TouchableOpacity>
          </View>
        )}
      />
    </View>
  );
}

  const fetchAvail = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listAvailability();
      setAvail(data);
    } catch {
      Alert.alert("Error", "Failed to load availability");
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { fetchAvail(); }, [fetchAvail]));

  const handleAdd = async () => {
    try {
      await createAvailability({
        day_of_week: newDay,
        start_time: newStart,
        end_time: newEnd,
      });
      fetchAvail();
    } catch (err: any) {
      Alert.alert("Error", err.detail ?? "Failed to add");
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteAvailability(id);
      fetchAvail();
    } catch {
      Alert.alert("Error", "Failed to delete");
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={avail}
        keyExtractor={(item) => item.id.toString()}
        ListHeaderComponent={
          <View style={styles.addCard}>
            <Text style={styles.sectionTitle}>Add Hours</Text>
            <View style={styles.pickerRow}>
              {DAYS.map((d, i) => (
                <TouchableOpacity
                  key={i}
                  style={[styles.dayBtn, newDay === i && styles.selectedDay]}
                  onPress={() => setNewDay(i)}
                >
                  <Text
                    style={[
                      styles.dayBtnText,
                      newDay === i && styles.selectedDayText,
                    ]}
                  >
                    {d}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
            <Text style={styles.label}>Start (HH:MM)</Text>
            <TextInput
              style={styles.input}
              value={newStart}
              onChangeText={setNewStart}
              placeholder="09:00"
            />
            <Text style={styles.label}>End (HH:MM)</Text>
            <TextInput
              style={styles.input}
              value={newEnd}
              onChangeText={setNewEnd}
              placeholder="18:00"
            />
            <TouchableOpacity style={styles.addBtn} onPress={handleAdd}>
              <Text style={styles.addBtnText}>Add</Text>
            </TouchableOpacity>
          </View>
        }
        renderItem={({ item }) => (
          <View style={styles.availCard}>
            <Text style={styles.availDay}>{DAYS[item.day_of_week]}</Text>
            <Text style={styles.availTime}>
              {item.start_time} - {item.end_time}
            </Text>
            <TouchableOpacity onPress={() => handleDelete(item.id)}>
              <Text style={styles.deleteText}>Delete</Text>
            </TouchableOpacity>
          </View>
        )}
      />
    </View>
  );
}
```

- [ ] **Step 4: Create services screen `app/professional/services.tsx`**

```typescript
import { useState, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  Switch,
} from "react-native";
import { useFocusEffect } from "expo-router";
import {
  listServices,
  createService,
  updateService,
  deleteService,
} from "../../src/services/services";
import { ServiceItem } from "../../src/types";

export default function ServicesScreen() {
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [duration, setDuration] = useState("30");
  const [price, setPrice] = useState("");

  const fetchSvc = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listServices();
      setServices(data);
    } catch {
      Alert.alert("Error", "Failed to load services");
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { fetchSvc(); }, [fetchSvc]));

  const handleAdd = async () => {
    if (!name.trim()) return;
    try {
      await createService({
        name,
        description: null,
        duration_minutes: parseInt(duration, 10) || 30,
        price: price ? parseFloat(price) : null,
      });
      setName("");
      setDuration("30");
      setPrice("");
      fetchSvc();
    } catch (err: any) {
      Alert.alert("Error", err.detail ?? "Failed to create service");
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteService(id);
      fetchSvc();
    } catch {
      Alert.alert("Error", "Failed to delete");
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={services}
        keyExtractor={(item) => item.id.toString()}
        ListHeaderComponent={
          <View style={styles.addCard}>
            <TextInput
              style={styles.input}
              placeholder="Service name"
              value={name}
              onChangeText={setName}
            />
            <TextInput
              style={styles.input}
              placeholder="Duration (min)"
              value={duration}
              onChangeText={setDuration}
              keyboardType="numeric"
            />
            <TextInput
              style={styles.input}
              placeholder="Price (optional)"
              value={price}
              onChangeText={setPrice}
              keyboardType="decimal-pad"
            />
            <TouchableOpacity style={styles.addBtn} onPress={handleAdd}>
              <Text style={styles.addBtnText}>Add Service</Text>
            </TouchableOpacity>
          </View>
        }
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.serviceName}>{item.name}</Text>
            <Text style={styles.serviceDetail}>
              {item.duration_minutes} min{item.price ? ` - $${item.price}` : ""}
            </Text>
            <TouchableOpacity onPress={() => handleDelete(item.id)}>
              <Text style={styles.deleteText}>Delete</Text>
            </TouchableOpacity>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f5f5f5", padding: 16 },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  addCard: {
    backgroundColor: "#fff",
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  input: {
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 8,
  },
  addBtn: {
    backgroundColor: "#007AFF",
    borderRadius: 8,
    padding: 12,
    alignItems: "center",
  },
  addBtnText: { color: "#fff", fontWeight: "600" },
  card: {
    backgroundColor: "#fff",
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  serviceName: { fontSize: 16, fontWeight: "600" },
  serviceDetail: { fontSize: 14, color: "#666", marginTop: 2 },
  deleteText: { color: "#FF3B30", fontWeight: "600" },
});
```

- [ ] **Step 5: Create integrations screen `app/professional/integrations.tsx`**

```typescript
import { useState, useCallback } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  Linking,
} from "react-native";
import { useFocusEffect } from "expo-router";
import { api } from "../../src/api/client";
import { ProfessionalIntegration } from "../../src/types";

export default function IntegrationsScreen() {
  const [integration, setIntegration] = useState<ProfessionalIntegration | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api<ProfessionalIntegration | null>(
        "/integrations/google/status",
      );
      setIntegration(data);
    } catch {
      // Not linked yet
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { fetchStatus(); }, [fetchStatus]));

  const handleLink = async () => {
    try {
      const data = await api<{ auth_url: string }>(
        "/integrations/google/auth",
      );
      await Linking.openURL(data.auth_url);
    } catch (err: any) {
      Alert.alert("Error", err.detail ?? "Failed to initialize Google sign-in");
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Google Calendar</Text>
      {integration ? (
        <View style={styles.card}>
          <Text style={styles.connected}>✅ Connected</Text>
          <Text style={styles.email}>{integration.google_email}</Text>
        </View>
      ) : (
        <TouchableOpacity style={styles.linkBtn} onPress={handleLink}>
          <Text style={styles.linkBtnText}>Link Google Calendar</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f5f5f5", padding: 24, justifyContent: "center" },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  title: { fontSize: 20, fontWeight: "bold", marginBottom: 16, textAlign: "center" },
  card: {
    backgroundColor: "#fff",
    padding: 24,
    borderRadius: 12,
    alignItems: "center",
  },
  connected: { fontSize: 18, fontWeight: "600", color: "#34C759" },
  email: { fontSize: 14, color: "#666", marginTop: 8 },
  linkBtn: {
    backgroundColor: "#007AFF",
    borderRadius: 8,
    padding: 16,
    alignItems: "center",
  },
  linkBtnText: { color: "#fff", fontSize: 16, fontWeight: "600" },
});
```

- [ ] **Step 6: Verify the app builds**

```bash
npx tsc --noEmit 2>&1 | head -30
```
Expected: No type errors

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: add professional screens (appointments, availability, services, integrations)"
```

---

### Task 7: Update Root Layout for Auth Routing

**Files:**
- Modify: `mobile-airmed/app/_layout.tsx`

- [ ] **Step 1: Update `app/_layout.tsx` to handle auth redirects**

The existing root layout needs to dynamically show the correct initial screen based on auth state and user role. Update the Stack definition:

```typescript
import { useEffect } from "react";
import { Stack, router } from "expo-router";
import { ActivityIndicator, View } from "react-native";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAuthStore } from "../src/stores/authStore";
import { getMe } from "../src/services/auth";
import { getToken } from "../src/api/client";

const queryClient = new QueryClient();

function AuthGate() {
  const { setUser, setLoading, isLoading, isAuthenticated, user } = useAuthStore();

  useEffect(() => {
    (async () => {
      const token = await getToken();
      if (token) {
        try {
          const me = await getMe();
          setUser(me);
        } catch {
          // Token invalid
        }
      }
      setLoading(false);
    })();
  }, []);

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace("/");
    } else if (user?.is_professional) {
      router.replace("/professional/appointments");
    } else {
      router.replace("/patient/appointments");
    }
  }, [isLoading, isAuthenticated, user]);

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return null;
}

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthGate />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="patient" />
        <Stack.Screen name="professional" />
      </Stack>
    </QueryClientProvider>
  );
}
```

- [ ] **Step 2: Verify the app builds**

```bash
npx tsc --noEmit 2>&1
```
Expected: No type errors

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: update root layout with auth-based routing"
```

---

### Task 8: Tests

**Files:**
- Create: `mobile-airmed/jest.config.js`
- Create: `mobile-airmed/tests/services/auth.test.ts`
- Create: `mobile-airmed/tests/api/client.test.ts`
- Create: `mobile-airmed/tests/stores/authStore.test.ts`

- [ ] **Step 1: Create Jest config `jest.config.js`**

```javascript
module.exports = {
  preset: "jest-expo",
  transformIgnorePatterns: [
    "node_modules/(?!(react-native|expo.*|@react-native|@expo|@react-navigation|react-native-.*|@react-native-.*|@unimodules)/)",
  ],
  setupFilesAfterSetup: ["@testing-library/jest-native/extend-expect"],
  moduleDirectories: ["node_modules", "<rootDir>"],
};
```

- [ ] **Step 2: Write auth store test `tests/stores/authStore.test.ts`**

```typescript
import { useAuthStore } from "../../src/stores/authStore";

describe("authStore", () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      isLoading: true,
      isAuthenticated: false,
    });
  });

  it("starts with no user", () => {
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isLoading).toBe(true);
  });

  it("setUser marks as authenticated", () => {
    const user = {
      id: 1,
      email: "test@test.com",
      full_name: "Test",
      is_professional: false,
    } as any;
    useAuthStore.getState().setUser(user);
    const state = useAuthStore.getState();
    expect(state.user).toEqual(user);
    expect(state.isAuthenticated).toBe(true);
  });

  it("logout clears user", () => {
    const user = { id: 1, email: "test@test.com" } as any;
    useAuthStore.getState().setUser(user);
    useAuthStore.getState().logout();
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it("setLoading updates loading state", () => {
    useAuthStore.getState().setLoading(false);
    expect(useAuthStore.getState().isLoading).toBe(false);
  });
});
```

- [ ] **Step 3: Write API client test `tests/api/client.test.ts`**

```typescript
import { api } from "../../src/api/client";

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe("api client", () => {
  beforeEach(() => {
    mockFetch.mockClear();
    // Clear SecureStore
    jest.resetModules();
  });

  it("makes GET request with correct headers", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ id: 1, name: "test" }),
    });

    const result = await api("/test");
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/test"),
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      }),
    );
    expect(result).toEqual({ id: 1, name: "test" });
  });

  it("throws ApiError on non-ok response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: "Not found" }),
    });

    await expect(api("/notfound")).rejects.toEqual({
      status: 404,
      detail: "Not found",
    });
  });
});
```

- [ ] **Step 4: Run tests**

```bash
npx jest --passWithNoTests 2>&1 | tail -20
```
Expected: Tests pass

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add Jest config and initial tests"
```

---

### Task 9: Final Verification

- [ ] **Step 1: Type check**

```bash
npx tsc --noEmit 2>&1
```
Expected: No type errors

- [ ] **Step 2: Run tests**

```bash
npx jest 2>&1 | tail -20
```
Expected: All tests pass

- [ ] **Step 3: Verify full file tree exists**

```bash
ls -R mobile-airmed/app/ mobile-airmed/src/
```
Expected: All screens and services present

- [ ] **Step 4: Final commit if any fixes needed**

```bash
git add -A && git commit -m "fix: address verification issues"
```
