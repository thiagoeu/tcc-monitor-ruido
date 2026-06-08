import { View, StyleSheet } from "react-native";

export default function MeterBar({ width, color }) {
  return (
    <View style={styles.container}>
      <View
        style={[
          styles.bar,
          {
            width,
            backgroundColor: color,
          },
        ]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: "90%",
    height: 30,
    backgroundColor: "#222",
    borderRadius: 20,
    overflow: "hidden",
  },

  bar: {
    height: "100%",
    borderRadius: 20,
  },
});
