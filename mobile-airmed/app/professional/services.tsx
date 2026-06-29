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
  listServices,
  createService,
  deleteService,
} from "../../services/services";
import { ServiceItem } from "../../types";

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
