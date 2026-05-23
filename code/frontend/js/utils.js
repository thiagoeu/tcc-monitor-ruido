// utils.js - funções utilitárias puras

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
      signal: controller.signal,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.erro || "Falha na requisição");
    }
    return response.json();
  } finally {
    clearTimeout(timeout);
  }
}
