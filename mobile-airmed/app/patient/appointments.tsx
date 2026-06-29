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
import { listAppointments, cancelAppointment } from "../../services/appointments";
import { Appointment } from "../../types";

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
