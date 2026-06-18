import { NavigationContainer } from '@react-navigation/native';import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text } from 'react-native';

import HomeScreen from './src/screens/HomeScreen';
import PerfilScreen from './src/screens/PerfilScreen';

const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Tab.Navigator>
        <Tab.Screen
          name="Inicio"
          component={HomeScreen}
          options={{
            tabBarIcon: () => <Text>🏠</Text>,
          }}
        />
        <Tab.Screen
          name="Perfil"
          component={PerfilScreen}
          options={{
            tabBarIcon: () => <Text>👤</Text>,
          }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
}