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
import { api } from "../../api/client";
import { ProfessionalIntegration } from "../../types";

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
