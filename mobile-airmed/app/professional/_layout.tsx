import { Tabs } from "expo-router";
import { Text } from "react-native";

export default function ProfessionalLayout() {
  return (
    <Tabs>
      <Tabs.Screen
        name="appointments"
        options={{ title: "Agenda", tabBarIcon: () => <Text>📅</Text> }}
      />
      <Tabs.Screen
        name="availability"
        options={{ title: "Hours", tabBarIcon: () => <Text>🕐</Text> }}
      />
      <Tabs.Screen
        name="services"
        options={{ title: "Services", tabBarIcon: () => <Text>💼</Text> }}
      />
      <Tabs.Screen
        name="integrations"
        options={{ title: "Integrations", tabBarIcon: () => <Text>🔗</Text> }}
      />
    </Tabs>
  );
}
