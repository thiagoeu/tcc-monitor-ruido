import { useEffect, useRef, useState } from "react";
import { Audio } from "expo-av";
import { enviarMedicao, ocuparAmbiente, liberarAmbiente, heartbeatSessao } from "../services/api";
import { Platform } from "react-native";

// Gera um ID único por instância do app (mantido em memória durante a sessão)
const DEVICE_ID = `device-${Platform.OS}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

export function useDecibelMeter(sensorId = "soundtracker-mobile-001") {
  const [db, setDb] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [minDb, setMinDb] = useState(null);
  const [maxDb, setMaxDb] = useState(null);
  const [avgDb, setAvgDb] = useState(null);
  const [ocupacaoError, setOcupacaoError] = useState(null);

  const recordingRef = useRef(null);
  const intervalRef = useRef(null);
  const sendIntervalRef = useRef(null);
  const heartbeatRef = useRef(null);
  const totalRef = useRef(0);
  const countRef = useRef(0);
  const dbRef = useRef(0);
  const isRecordingRef = useRef(false);
  const sensorIdRef = useRef(sensorId);

  // Mantém sensorIdRef atualizado com o sensor atual
  useEffect(() => {
    sensorIdRef.current = sensorId;
  }, [sensorId]);

  useEffect(() => {
    dbRef.current = db;
  }, [db]);

  useEffect(() => {
    isRecordingRef.current = isRecording;
  }, [isRecording]);

  const startMetering = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    console.log("📊 Iniciando intervalo de leitura do metering...");
    intervalRef.current = setInterval(async () => {
      if (!recordingRef.current || !isRecordingRef.current) return;
      try {
        const status = await recordingRef.current.getStatusAsync();
        if (status.isRecording && status.metering !== undefined) {
          const dbSPL = Math.max(35, Math.min(100, 90 + status.metering));
          setDb((prev) => {
            const smoothValue = prev * 0.7 + dbSPL * 0.3;
            setMinDb((prevMin) => {
              if (smoothValue < 32) return prevMin;
              if (prevMin === null) return smoothValue;
              return Math.min(prevMin, smoothValue);
            });
            setMaxDb((prevMax) => {
              if (prevMax === null) return smoothValue;
              return Math.max(prevMax, smoothValue);
            });
            totalRef.current += smoothValue;
            countRef.current += 1;
            setAvgDb(totalRef.current / countRef.current);
            return smoothValue;
          });
        }
      } catch (error) {
        console.log("METER ERROR", error);
      }
    }, 150);
  };

  const startSending = () => {
    if (sendIntervalRef.current) clearInterval(sendIntervalRef.current);
    sendIntervalRef.current = setInterval(async () => {
      if (isRecordingRef.current && dbRef.current > 0) {
        await enviarMedicao(sensorIdRef.current, dbRef.current);
      }
    }, 2000);
  };

  const startHeartbeat = () => {
    if (heartbeatRef.current) clearInterval(heartbeatRef.current);
    heartbeatRef.current = setInterval(async () => {
      if (isRecordingRef.current) {
        await heartbeatSessao(sensorIdRef.current, DEVICE_ID);
      }
    }, 10000); // a cada 10s
  };

  const start = async () => {
    if (isRecording) return;
    setOcupacaoError(null);

    // Tenta reservar o ambiente antes de iniciar a gravação
    try {
      await ocuparAmbiente(sensorId, DEVICE_ID);
    } catch (err) {
      console.log("🔒 Ambiente ocupado:", err.message);
      setOcupacaoError(err.message);
      return;
    }

    console.log("🔴 Solicitando permissão de áudio...");
    try {
      const { granted } = await Audio.requestPermissionsAsync();
      if (!granted) {
        console.log("❌ Permissão negada");
        // Libera o ambiente se não conseguiu permissão
        await liberarAmbiente(sensorId, DEVICE_ID);
        return;
      }
      console.log("✅ Permissão concedida");
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });
      console.log("🎤 Iniciando gravação...");
      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY,
        undefined,
        true,
      );
      recordingRef.current = recording;
      setIsRecording(true);
      startMetering();
      startSending();
      startHeartbeat();
      console.log("📡 Gravação ativa, enviando medições...");
    } catch (error) {
      console.log("START ERROR", error);
      // Libera o ambiente em caso de erro ao iniciar
      await liberarAmbiente(sensorId, DEVICE_ID);
    }
  };

  const stop = async () => {
    if (!recordingRef.current) return;
    console.log("🛑 Parando gravação...");
    try {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (sendIntervalRef.current) clearInterval(sendIntervalRef.current);
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
      await recordingRef.current.stopAndUnloadAsync();
      recordingRef.current = null;
      setIsRecording(false);
      setDb(0);
      setMinDb(null);
      setMaxDb(null);
      setAvgDb(null);
      totalRef.current = 0;
      countRef.current = 0;

      // Libera o ambiente ao parar
      await liberarAmbiente(sensorIdRef.current, DEVICE_ID);
      console.log("🔓 Ambiente liberado.");
    } catch (error) {
      console.log("STOP ERROR", error);
    }
  };

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (sendIntervalRef.current) clearInterval(sendIntervalRef.current);
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
      if (recordingRef.current) {
        recordingRef.current.stopAndUnloadAsync().catch(console.log);
      }
      // Libera o ambiente ao desmontar o componente
      if (isRecordingRef.current) {
        liberarAmbiente(sensorIdRef.current, DEVICE_ID).catch(console.log);
      }
    };
  }, []);

  return { db, isRecording, minDb, maxDb, avgDb, start, stop, ocupacaoError };
}
