import { fetchJson } from "./utils.js";

export async function fetchAmbientes() {
  return fetchJson("/api/ambientes");
}

export async function fetchMonitoramento(limit = 80) {
  return fetchJson(`/api/monitoramento?limit=${limit}`);
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
