import { useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  Modal,
  FlatList,
  StyleSheet,
  ActivityIndicator,
} from "react-native";

export default function SensorSelector({ sensores, sensorSelecionado, onSelect, loading, onRefresh }) {
  const [modalVisible, setModalVisible] = useState(false);

  const label = sensorSelecionado
    ? `${sensorSelecionado.nome} — ${sensorSelecionado.localizacao}`
    : "Selecionar local de medição";

  return (
    <View style={styles.wrapper}>
      <Text style={styles.label}>Local de Medição</Text>

      <TouchableOpacity
        style={[styles.selector, sensorSelecionado && styles.selectorActive]}
        onPress={() => {
          if (onRefresh) onRefresh();
          setModalVisible(true);
        }}
        activeOpacity={0.75}
      >
        {loading ? (
          <ActivityIndicator color="#7C6FF7" />
        ) : (
          <>
            <Text
              style={[styles.selectorText, !sensorSelecionado && styles.placeholder]}
              numberOfLines={1}
            >
              {label}
            </Text>
            <Text style={styles.chevron}>▾</Text>
          </>
        )}
      </TouchableOpacity>

      <Modal
        visible={modalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setModalVisible(false)}
      >
        <TouchableOpacity
          style={styles.overlay}
          activeOpacity={1}
          onPress={() => setModalVisible(false)}
        >
          <View style={styles.sheet} onStartShouldSetResponder={() => true}>
            <Text style={styles.sheetTitle}>Escolha o local</Text>

            {sensores.length === 0 ? (
              <Text style={styles.empty}>Nenhum ambiente ativo encontrado.</Text>
            ) : (
              <FlatList
                data={sensores}
                keyExtractor={(item) => String(item.id)}
                ItemSeparatorComponent={() => <View style={styles.separator} />}
                renderItem={({ item }) => {
                  const isSelected = sensorSelecionado?.id === item.id;
                  return (
                    <TouchableOpacity
                      style={[styles.option, isSelected && styles.optionSelected]}
                      onPress={() => {
                        onSelect(item);
                        setModalVisible(false);
                      }}
                      activeOpacity={0.7}
                    >
                      <View style={styles.optionInfo}>
                        <Text style={[styles.optionName, isSelected && styles.optionNameSelected]}>
                          {item.nome}
                        </Text>
                        <Text style={styles.optionSub}>{item.localizacao}</Text>
                      </View>
                      {isSelected && <Text style={styles.checkmark}>✓</Text>}
                    </TouchableOpacity>
                  );
                }}
              />
            )}
          </View>
        </TouchableOpacity>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    width: "100%",
    marginBottom: 24,
  },
  label: {
    color: "#9CA3AF",
    fontSize: 12,
    fontWeight: "600",
    letterSpacing: 1,
    textTransform: "uppercase",
    marginBottom: 8,
  },
  selector: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "#1C1F26",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#2D3140",
    paddingHorizontal: 16,
    paddingVertical: 14,
    minHeight: 52,
  },
  selectorActive: {
    borderColor: "#7C6FF7",
  },
  selectorText: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "500",
    flex: 1,
  },
  placeholder: {
    color: "#6B7280",
  },
  chevron: {
    color: "#7C6FF7",
    fontSize: 18,
    marginLeft: 8,
  },
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.65)",
    justifyContent: "flex-end",
  },
  sheet: {
    backgroundColor: "#1C1F26",
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingTop: 20,
    paddingBottom: 32,
    paddingHorizontal: 16,
    maxHeight: "60%",
  },
  sheetTitle: {
    color: "#FFFFFF",
    fontSize: 17,
    fontWeight: "700",
    marginBottom: 16,
    textAlign: "center",
  },
  empty: {
    color: "#6B7280",
    textAlign: "center",
    marginTop: 20,
    fontSize: 14,
  },
  separator: {
    height: 1,
    backgroundColor: "#2D3140",
  },
  option: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 14,
    paddingHorizontal: 8,
    borderRadius: 10,
  },
  optionSelected: {
    backgroundColor: "rgba(124, 111, 247, 0.12)",
  },
  optionInfo: {
    flex: 1,
  },
  optionName: {
    color: "#E5E7EB",
    fontSize: 15,
    fontWeight: "600",
  },
  optionNameSelected: {
    color: "#7C6FF7",
  },
  optionSub: {
    color: "#6B7280",
    fontSize: 13,
    marginTop: 2,
  },
  checkmark: {
    color: "#7C6FF7",
    fontSize: 18,
    fontWeight: "700",
    marginLeft: 8,
  },
});
