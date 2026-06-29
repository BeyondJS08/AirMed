module.exports = {
  preset: "jest-expo",
  transformIgnorePatterns: [
    "node_modules/(?!(react-native|expo.*|@react-native|@expo|@react-navigation|react-native-.*|@react-native-.*|@unimodules)/)",
  ],
  moduleDirectories: ["node_modules", "<rootDir>"],
};
