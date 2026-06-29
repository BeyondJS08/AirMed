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
