import { useEffect, useState } from "react";
import { View, Text, StyleSheet, Alert } from "react-native";
import { useDecibelMeter } from "./src/hooks/useDecibelMeter";
import MeterDisplay from "./src/components/MeterDisplay";
import NoiseStatus from "./src/components/NoiseStatus";
import MeterBar from "./src/components/MeterBar";
import ControlButton from "./src/components/ControlButton";
import StatsPanel from "./src/components/StatsPanel";
import SensorSelector from "./src/components/SensorSelector";
import { getColor, getNoiseLabel, getWidth } from "./src/shared/soundUtils";
import { getSensores } from "./src/services/api";

export default function App() {
  const [sensores, setSensores] = useState([]);
  const [sensorSelecionado, setSensorSelecionado] = useState(null);
  const [loadingSensores, setLoadingSensores] = useState(true);

  // Busca os ambientes ativos do backend (chamada no mount e ao abrir o seletor)
  const carregarSensores = async () => {
    setLoadingSensores(true);
    const data = await getSensores();
    setSensores(data);
    setLoadingSensores(false);
  };

  useEffect(() => {
    carregarSensores();
  }, []);

  const sensorId = sensorSelecionado?.sensor_id ?? null;

  const { db, minDb, maxDb, avgDb, isRecording, start, stop, ocupacaoError } =
    useDecibelMeter(sensorId);

  // Exibe alerta quando o ambiente já está em uso por outro dispositivo
  useEffect(() => {
    if (ocupacaoError) {
      Alert.alert(
        "Ambiente Ocupado 🔒",
        "Este ambiente já está sendo monitorado por outro dispositivo. Selecione outro local de medição.",
        [{ text: "OK" }]
      );
      // Recarrega a lista para mostrar o status atualizado
      carregarSensores();
    }
  }, [ocupacaoError]);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Decibelímetro</Text>

      <SensorSelector
        sensores={sensores}
        sensorSelecionado={sensorSelecionado}
        onSelect={setSensorSelecionado}
        loading={loadingSensores}
        onRefresh={carregarSensores}
        isRecording={isRecording}
      />

      <MeterDisplay db={db} color={getColor(db)} />

      <NoiseStatus label={getNoiseLabel(db)} color={getColor(db)} />

      <MeterBar width={getWidth(db)} color={getColor(db)} />

      <StatsPanel minDb={minDb} avgDb={avgDb} maxDb={maxDb} />

      <ControlButton
        isRecording={isRecording}
        disabled={!sensorSelecionado}
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
