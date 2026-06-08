import { Text, StyleSheet } from "react-native";

export default function MeterDisplay({ db, color }) {
  return (
    <Text
      style={[
        styles.db,
        {
          color,
        },
      ]}
    >
      {db.toFixed(1)}
    </Text>
  );
}

const styles = StyleSheet.create({
  db: {
    fontSize: 90,
    fontWeight: "bold",
  },
});
