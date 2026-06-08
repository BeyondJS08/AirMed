import * as React from "react";
import { useColorScheme } from "react-native";

interface ThemeProviderProps {
  children: React.ReactNode;
}

function ThemeProvider({ children }: ThemeProviderProps) {
  const colorScheme = useColorScheme();

  React.useEffect(() => {
    // NativeWind handles dark mode through the 'dark' class
    // This is just for any additional theme logic
  }, [colorScheme]);

  return <>{children}</>;
}

export { ThemeProvider };
