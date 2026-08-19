// utils.js - funções utilitárias puras
import { authHeaders, clearToken } from "./auth.js";

export function toLocalDate(isoDate) {
  if (!isoDate) return "-";
  return new Date(isoDate).toLocaleString("pt-BR");
}

export function formatDb(value) {
  if (value === null || value === undefined) return "-";
  return Number(value).toFixed(1);
}

export function statusTag(excedeu) {
  return excedeu
    ? '<span class="tag warn">Acima do limite</span>'
    : '<span class="tag ok">Normal</span>';
}

export async function fetchJson(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 7000);
  try {
    const response = await fetch(path, {
      cache: "no-store",
      ...options,
      headers: authHeaders(options.headers),
      signal: controller.signal,
    });
    if (response.status === 401) {
      clearToken();
      window.location.href = "/login.html";
      throw new Error("Sessão expirada. Faça login novamente.");
    }
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.erro || "Falha na requisição");
    }
    return response.json();
  } finally {
    clearTimeout(timeout);
  }
}
