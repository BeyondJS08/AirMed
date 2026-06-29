import { useEffect } from "react";
import { Stack, router } from "expo-router";
import { ActivityIndicator, View } from "react-native";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAuthStore } from "../stores/authStore";
import { getMe } from "../services/auth";
import { getToken } from "../api/client";

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
