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
} from "../../services/appointments";
import { Appointment } from "../../types";

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
