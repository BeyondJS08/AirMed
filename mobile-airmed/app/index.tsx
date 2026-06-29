import { useEffect } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from "react-native";
import * as WebBrowser from "expo-web-browser";
import { useAuthRequest, makeRedirectUri } from "expo-auth-session";
import { router } from "expo-router";
import { loginWithGoogle } from "../services/auth";
import { useAuthStore } from "../stores/authStore";
import { getMe } from "../services/auth";
import { getToken } from "../api/client";

WebBrowser.maybeCompleteAuthSession();

const discovery = {
  authorizationEndpoint: "https://accounts.google.com/o/oauth2/v2/auth",
  tokenEndpoint: "https://oauth2.googleapis.com/token",
};

export default function LoginScreen() {
  const { setUser, setLoading, isLoading, isAuthenticated, user } = useAuthStore();

  const [request, response, promptAsync] = useAuthRequest(
    {
      clientId: "YOUR_GOOGLE_IOS_CLIENT_ID",
      redirectUri: makeRedirectUri({ scheme: "airmed" }),
      scopes: ["openid", "profile", "email"],
    },
    discovery,
  );

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
    if (response?.type === "success") {
      const idToken = response.params.id_token;
      if (idToken) {
        setLoading(true);
        loginWithGoogle(idToken)
          .then((user) => {
            setUser(user);
            router.replace(
              user.is_professional ? "/professional/appointments" : "/patient/appointments",
            );
          })
          .catch((err) => {
            Alert.alert("Login Failed", err.detail ?? "Google sign-in failed");
          })
          .finally(() => setLoading(false));
      }
    }
  }, [response]);

  useEffect(() => {
    if (isLoading) return;
    if (isAuthenticated && user) {
      router.replace(
        user.is_professional ? "/professional/appointments" : "/patient/appointments",
      );
    }
  }, [isLoading, isAuthenticated, user]);

  if (isLoading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" style={{ marginTop: 200 }} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>AirMed</Text>
        <Text style={styles.subtitle}>Appointment Scheduling</Text>
        <TouchableOpacity
          style={styles.googleBtn}
          onPress={() => promptAsync()}
          disabled={!request}
        >
          <Text style={styles.googleBtnText}>Sign in with Google</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  content: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
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
    marginBottom: 48,
  },
  googleBtn: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    padding: 16,
    paddingHorizontal: 32,
    alignItems: "center",
    flexDirection: "row",
  },
  googleBtnText: { color: "#333", fontSize: 16, fontWeight: "600" },
});
