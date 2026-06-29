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
import { listProfessionals } from "../../services/professionals";
import { listServices } from "../../services/services";
import { getAvailableSlotsByDate } from "../../services/availability";
import { createAppointment } from "../../services/appointments";
import { User, ServiceItem } from "../../types";

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
