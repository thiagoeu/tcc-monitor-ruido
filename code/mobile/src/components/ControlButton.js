import { TouchableOpacity, Text, StyleSheet } from "react-native";

export default function ControlButton({ isRecording, onPress, disabled }) {
  return (
    <TouchableOpacity
      style={[
        styles.button,
        {
          backgroundColor: disabled
            ? "#2D3140"
            : isRecording
            ? "#FF5252"
            : "#00E676",
          opacity: disabled ? 0.6 : 1,
        },
      ]}
      onPress={disabled ? undefined : onPress}
      activeOpacity={disabled ? 1 : 0.75}
    >
      <Text style={[styles.buttonText, disabled && styles.buttonTextDisabled]}>
        {disabled
          ? "Selecione um local"
          : isRecording
          ? "Parar Medição"
          : "Iniciar Medição"}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    marginTop: 40,
    paddingVertical: 15,
    paddingHorizontal: 40,
    borderRadius: 14,
  },

  buttonText: {
    color: "#111",
    fontSize: 20,
    fontWeight: "bold",
  },

  buttonTextDisabled: {
    color: "#6B7280",
  },
});
