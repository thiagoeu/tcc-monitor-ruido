import Constants from "expo-constants";

const API_BASE_URL = Constants.expoConfig?.extra?.apiBaseUrl; // substitua pelo IP do PC

export async function getSensores() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/ambientes?ativo=1`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.erro || "Erro ao buscar sensores");
    return data; // array de { id, nome, localizacao, sensor_id, limite_db, ... }
  } catch (error) {
    console.error("❌ Falha ao buscar sensores:", error);
    return [];
  }
}

export async function enviarMedicao(sensorId, db) {
  try {
    const roundedDb = parseFloat(db.toFixed(2));
    const response = await fetch(`${API_BASE_URL}/api/medicoes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sensor_id: sensorId,
        db: roundedDb,
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.erro || "Erro no servidor");
    console.log("✅ Medição enviada:", { sensorId, db: roundedDb });
    return data;
  } catch (error) {
    console.error("❌ Falha ao enviar medição:", error);
  }
}
