// utils.js - funções utilitárias puras
import { authHeaders, clearToken } from "./auth.js";
import { showToast } from "./toast.js";

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
      const error = new Error("Sessão expirada. Faça login novamente.");
      showToast(error.message, "warning");
      throw error;
    }
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const error = new Error(body.erro || "Falha na requisição");
      showToast(error.message);
      throw error;
    }
    return response.json();
  } catch (error) {
    if (error.name === "AbortError") {
      const msg = "Tempo de requisição esgotado.";
      showToast(msg);
      throw new Error(msg);
    }
    if (error.name === "TypeError") {
      const msg = "Falha de rede ao contactar o servidor.";
      showToast(msg);
      throw new Error(msg);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
