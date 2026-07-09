import Constants from "expo-constants";

const API_BASE_URL = Constants.expoConfig?.extra?.apiBaseUrl; // substitua pelo IP do PC

export async function getSensores() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/ambientes?ativo=1`, {
      headers: { "bypass-tunnel-reminder": "true" },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.erro || "Erro ao buscar sensores");
    return data; // array de { id, nome, localizacao, sensor_id, limite_db, em_uso, ... }
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
      headers: {
        "Content-Type": "application/json",
        "bypass-tunnel-reminder": "true",
      },
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

/**
 * Tenta reservar o ambiente para este dispositivo.
 * Retorna { ok: true } em caso de sucesso.
 * Lança Error com a mensagem do servidor em caso de conflito (409).
 */
export async function ocuparAmbiente(sensorId, deviceId) {
  const response = await fetch(`${API_BASE_URL}/api/sessoes`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "bypass-tunnel-reminder": "true",
    },
    body: JSON.stringify({ sensor_id: sensorId, device_id: deviceId }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.erro || "Erro ao reservar ambiente");
  return data;
}

/**
 * Libera o ambiente reservado por este dispositivo.
 */
export async function liberarAmbiente(sensorId, deviceId) {
  try {
    await fetch(`${API_BASE_URL}/api/sessoes/${encodeURIComponent(sensorId)}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        "bypass-tunnel-reminder": "true",
      },
      body: JSON.stringify({ device_id: deviceId }),
    });
  } catch (error) {
    console.error("❌ Falha ao liberar ambiente:", error);
  }
}

/**
 * Renova o TTL da sessão ativa (heartbeat).
 */
export async function heartbeatSessao(sensorId, deviceId) {
  try {
    await fetch(
      `${API_BASE_URL}/api/sessoes/${encodeURIComponent(sensorId)}/heartbeat`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "bypass-tunnel-reminder": "true",
        },
        body: JSON.stringify({ device_id: deviceId }),
      }
    );
  } catch (error) {
    console.error("❌ Falha no heartbeat:", error);
  }
}

