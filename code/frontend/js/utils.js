// utils.js - funções utilitárias puras
import { authHeaders, clearToken } from "./auth.js";
import { showToast } from "./toast.js";

// ============ FORMATAÇÃO ============

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

// ============ DARK MODE ============

const THEME_KEY = "nr_theme";

/**
 * Inicializa o dark mode em qualquer página.
 * Lê a preferência do localStorage, aplica data-theme no <html>
 * e registra o listener do botão toggle (id="themeToggle").
 */
export function initDarkMode() {
  const saved = localStorage.getItem(THEME_KEY);
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const theme = saved ?? (prefersDark ? "dark" : "light");

  applyTheme(theme);

  const toggle = document.getElementById("themeToggle");
  if (toggle) {
    toggle.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") ?? "dark";
      const next = current === "dark" ? "light" : "dark";
      applyTheme(next);
      localStorage.setItem(THEME_KEY, next);
      window.dispatchEvent(new CustomEvent("themeChanged", { detail: next }));
    });
  }
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  updateToggleUI(theme);
}

function updateToggleUI(theme) {
  const track = document.querySelector(".toggle-track");
  const label = document.querySelector(".theme-label");
  if (track) track.classList.toggle("on", theme === "light");
  if (label) label.textContent = theme === "dark" ? "Dark" : "Light";
}

/**
 * Retorna o tema atual salvo.
 */
export function getTheme() {
  return localStorage.getItem(THEME_KEY) ?? "dark";
}

/**
 * Define o tema diretamente (para uso pela página de Configurações).
 */
export function setTheme(theme) {
  localStorage.setItem(THEME_KEY, theme);
  applyTheme(theme);
}

// ============ FETCH ============

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
