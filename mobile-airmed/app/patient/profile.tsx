import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { router } from "expo-router";
import { useAuthStore } from "../../stores/authStore";
import { logout } from "../../services/auth";

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
