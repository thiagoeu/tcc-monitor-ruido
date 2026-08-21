export default {
  expo: {
    name: "soundtracker",
    slug: "soundtracker",
    version: "1.0.0",
    orientation: "portrait",
    icon: "./assets/icon.png",
    userInterfaceStyle: "light",
    newArchEnabled: true,
    splash: {
      image: "./assets/splash-icon.png",
      resizeMode: "contain",
      backgroundColor: "#ffffff",
    },
    ios: {
      supportsTablet: true,
    },
    android: {
      package: "com.soundtracker.app",
      adaptiveIcon: {
        foregroundImage: "./assets/adaptive-icon.png",
        backgroundColor: "#ffffff",
      },
      edgeToEdgeEnabled: true,
      usesCleartextTraffic: true,
    },
    web: {
      favicon: "./assets/favicon.png",
    },
    plugins: ["expo-av"],
    extra: {
      apiBaseUrl: process.env.API_BASE_URL || "http://192.168.0.4:5000",
      eas: {
        projectId: "9c51d266-1d0e-4fc5-802d-83661bad359c",
      },
    },
  },
};
