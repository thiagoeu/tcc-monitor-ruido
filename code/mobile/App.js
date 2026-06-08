import { useEffect } from "react";
import { View, Text, StyleSheet } from "react-native";
import Constants from "expo-constants";
import { useDecibelMeter } from "./src/hooks/useDecibelMeter";
import MeterDisplay from "./src/components/MeterDisplay";
import NoiseStatus from "./src/components/NoiseStatus";
import MeterBar from "./src/components/MeterBar";
import ControlButton from "./src/components/ControlButton";
import StatsPanel from "./src/components/StatsPanel";
import { getColor, getNoiseLabel, getWidth } from "./src/shared/soundUtils";

// Gera um ID único baseado no dispositivo (ou um fallback)
const getDeviceSensorId = () => {
  try {
    // Tenta obter o deviceId (Android/iOS)
    return (
      Constants.deviceId || Constants.installationId || "soundtracker-mobile"
    );
  } catch {
    return "soundtracker-mobile-default";
  }
};

export default function App() {
  const sensorId = "123";

  const { db, minDb, maxDb, avgDb, isRecording, start, stop } =
    useDecibelMeter(sensorId);
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Decibelímetro</Text>

      <MeterDisplay db={db} color={getColor(db)} />

      <NoiseStatus label={getNoiseLabel(db)} color={getColor(db)} />

      <MeterBar width={getWidth(db)} color={getColor(db)} />

      <StatsPanel minDb={minDb} avgDb={avgDb} maxDb={maxDb} />

      <ControlButton
        isRecording={isRecording}
        onPress={() => {
          if (isRecording) {
            stop();
          } else {
            start();
          }
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0F1115",
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },

  title: {
    color: "#fff",
    fontSize: 34,
    fontWeight: "700",
    marginBottom: 40,
  },
});
