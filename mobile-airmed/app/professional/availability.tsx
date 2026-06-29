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
} from "react-native";
import { useFocusEffect } from "expo-router";
import {
  listAvailability,
  deleteAvailability,
  createAvailability,
} from "../../services/availability";
import { Availability } from "../../types";

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

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f5f5f5", padding: 16 },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  addCard: {
    backgroundColor: "#fff",
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  sectionTitle: { fontSize: 18, fontWeight: "bold", marginBottom: 12 },
  pickerRow: { flexDirection: "row", marginBottom: 12, gap: 4 },
  dayBtn: {
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 6,
    backgroundColor: "#f0f0f0",
  },
  selectedDay: { backgroundColor: "#007AFF" },
  dayBtnText: { fontSize: 12, color: "#333" },
  selectedDayText: { color: "#fff" },
  label: { fontSize: 14, color: "#666", marginBottom: 4 },
  input: {
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 12,
  },
  addBtn: {
    backgroundColor: "#007AFF",
    borderRadius: 8,
    padding: 12,
    alignItems: "center",
  },
  addBtnText: { color: "#fff", fontWeight: "600" },
  availCard: {
    backgroundColor: "#fff",
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  availDay: { fontSize: 16, fontWeight: "600" },
  availTime: { fontSize: 14, color: "#666" },
  deleteText: { color: "#FF3B30", fontWeight: "600" },
});
