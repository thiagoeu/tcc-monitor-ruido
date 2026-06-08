import { TouchableOpacity, Text, StyleSheet } from "react-native";

export default function ControlButton({ isRecording, onPress }) {
  return (
    <TouchableOpacity
      style={[
        styles.button,
        {
          backgroundColor: isRecording ? "#FF5252" : "#00E676",
        },
      ]}
      onPress={onPress}
    >
      <Text style={styles.buttonText}>
        {isRecording ? "Parar Medição" : "Iniciar Medição"}
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
});
