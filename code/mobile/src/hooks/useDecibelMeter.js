import { useEffect, useRef, useState } from "react";
import { Audio } from "expo-av";
import { enviarMedicao } from "../services/api";

export function useDecibelMeter(sensorId = "soundtracker-mobile-001") {
  const [db, setDb] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [minDb, setMinDb] = useState(null);
  const [maxDb, setMaxDb] = useState(null);
  const [avgDb, setAvgDb] = useState(null);

  const recordingRef = useRef(null);
  const intervalRef = useRef(null);
  const sendIntervalRef = useRef(null);
  const totalRef = useRef(0);
  const countRef = useRef(0);
  const dbRef = useRef(0);
  const isRecordingRef = useRef(false);

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
        await enviarMedicao(sensorId, dbRef.current);
      }
    }, 2000);
  };

  const start = async () => {
    if (isRecording) return;
    console.log("🔴 Solicitando permissão de áudio...");
    try {
      const { granted } = await Audio.requestPermissionsAsync();
      if (!granted) {
        console.log("❌ Permissão negada");
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
      console.log("📡 Gravação ativa, enviando medições...");
    } catch (error) {
      console.log("START ERROR", error);
    }
  };

  const stop = async () => {
    if (!recordingRef.current) return;
    console.log("🛑 Parando gravação...");
    try {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (sendIntervalRef.current) clearInterval(sendIntervalRef.current);
      await recordingRef.current.stopAndUnloadAsync();
      recordingRef.current = null;
      setIsRecording(false);
      setDb(0);
      setMinDb(null);
      setMaxDb(null);
      setAvgDb(null);
      totalRef.current = 0;
      countRef.current = 0;
    } catch (error) {
      console.log("STOP ERROR", error);
    }
  };

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (sendIntervalRef.current) clearInterval(sendIntervalRef.current);
      if (recordingRef.current) {
        recordingRef.current.stopAndUnloadAsync().catch(console.log);
      }
    };
  }, []);

  return { db, isRecording, minDb, maxDb, avgDb, start, stop };
}
