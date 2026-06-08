# Expo HAS CHANGED

Read the exact versioned docs at https://docs.expo.dev/versions/v54.0.0/ before writing any code.

## shadcn/ui for React Native (Expo)

This project uses **NativeWind** with a shadcn/ui-inspired design system via `react-native-reusables` patterns.

### Setup
- **NativeWind** provides Tailwind CSS for React Native
- **CSS Variables** are defined in `global.css` for theming
- **Components** are in `components/ui/` following shadcn/ui patterns
- **Utilities** (`cn`) are in `lib/utils.ts`

### Key Files
- `tailwind.config.js` - Tailwind configuration with NativeWind preset
- `babel.config.js` - Babel configuration with NativeWind plugin
- `global.css` - CSS variables for light/dark themes
- `components.json` - shadcn/ui project configuration
- `lib/utils.ts` - `cn()` utility for class merging

### Adding Components
Components follow the shadcn/ui pattern using `class-variance-authority` for variants:

```tsx
import { Button } from "@/components/ui/button";
import { Text } from "@/components/ui/text";

<Button variant="default" size="lg">
  <Text>Press me</Text>
</Button>
```

### Theming
The theme supports dark mode automatically via `useColorScheme()` hook and CSS variables.

