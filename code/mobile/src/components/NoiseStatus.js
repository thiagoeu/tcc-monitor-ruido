import { Text, StyleSheet } from "react-native";

export default function NoiseStatus({ label, color }) {
  return (
    <Text
      style={[
        styles.label,
        {
          color,
        },
      ]}
    >
      {label}
    </Text>
  );
}

const styles = StyleSheet.create({
  label: {
    fontSize: 24,
    marginTop: 10,
    fontWeight: "600",
    marginBottom: 40,
  },
});
