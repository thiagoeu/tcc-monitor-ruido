import { fetchJson } from "./utils.js";

export async function fetchAmbientes() {
  return fetchJson("/api/ambientes");
}

export async function fetchMonitoramento(limit = 80) {
  return fetchJson(`/api/monitoramento?limit=${limit}`);
}

export async function fetchSensoresFisicos(params = {}) {
  const query = new URLSearchParams({
    port: params.port ?? "/dev/ttyAMA0",
    baudrate: String(params.baudrate ?? 9600),
    start_id: String(params.start_id ?? 1),
    end_id: String(params.end_id ?? 32),
    registers: params.registers ?? "0,1",
    function_code: String(params.function_code ?? 3),
    timeout: String(params.timeout ?? 0.25),
  });

  return fetchJson(`/api/sensores/fisicos?${query.toString()}`);
}

export async function fetchRelatorioResumo(hours = 24) {
  return fetchJson(`/api/relatorios/resumo?hours=${hours}`);
}

export async function criarAmbiente(payload) {
  return fetchJson("/api/ambientes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function excluirAmbiente(id) {
  return fetchJson(`/api/ambientes/${id}`, { method: "DELETE" });
}

export async function downloadRelatorioTxt(hours) {
  window.location.href = `/api/relatorios/txt?hours=${hours}`;
}
