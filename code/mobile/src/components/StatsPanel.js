import { View, Text, StyleSheet } from "react-native";

export default function StatsPanel({ minDb, avgDb, maxDb }) {
  const renderValue = (value) => {
    return value ? value.toFixed(1) : "--";
  };

  return (
    <View style={styles.statsContainer}>
      <View style={styles.statBox}>
        <Text style={styles.statLabel}>MIN</Text>

        <Text style={styles.statValue}>{renderValue(minDb)}</Text>
      </View>

      <View style={styles.statBox}>
        <Text style={styles.statLabel}>MÉDIA</Text>

        <Text style={styles.statValue}>{renderValue(avgDb)}</Text>
      </View>

      <View style={styles.statBox}>
        <Text style={styles.statLabel}>MAX</Text>

        <Text style={styles.statValue}>{renderValue(maxDb)}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  statsContainer: {
    flexDirection: "row",
    marginTop: 30,
    gap: 20,
  },

  statBox: {
    alignItems: "center",
    backgroundColor: "#1A1D24",
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 12,
    minWidth: 90,
  },

  statLabel: {
    color: "#888",
    fontSize: 14,
    marginBottom: 6,
  },

  statValue: {
    color: "#fff",
    fontSize: 22,
    fontWeight: "bold",
  },
});
