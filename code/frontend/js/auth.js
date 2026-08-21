// auth.js - gerenciamento de autenticação no cliente
import { showToast } from "./toast.js";

const TOKEN_KEY = "noiseradar_token";
const USER_KEY  = "noiseradar_user";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isAuthenticated() {
  return Boolean(getToken());
}

export function authHeaders(extra = {}) {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}`, ...extra } : { ...extra };
}

/**
 * Retorna o objeto usuario salvo no localStorage, ou null.
 * @returns {{ id, nome, email, papel, ativo }|null}
 */
export function getUser() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

/**
 * Retorna o papel do usuário logado ("admin" | "visualizador" | null).
 */
export function getUserPapel() {
  return getUser()?.papel ?? null;
}

export async function login(email, senha) {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, senha }),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(body.erro || "Falha no login");
    showToast(error.message);
    throw error;
  }
  setToken(body.token);
  // Persiste o objeto usuario para decisões de UI sem roundtrip extra
  if (body.usuario) {
    localStorage.setItem(USER_KEY, JSON.stringify(body.usuario));
  }
  return body.usuario;
}

export async function logout() {
  const response = await fetch("/api/auth/logout", {
    method: "POST",
    headers: authHeaders(),
  });
  clearToken();
  if (!response.ok) {
    throw new Error("Falha ao encerrar sessão");
  }
  window.location.href = "/login.html";
}

export function requireAuth() {
  if (!isAuthenticated()) {
    window.location.href = "/login.html";
    return false;
  }
  return true;
}

/**
 * Verifica server-side se o usuário é admin.
 * Redireciona para "/" se for visualizador, para "/login.html" se não autenticado.
 * @returns {Promise<boolean>} true se admin
 */
export async function requireAdmin() {
  if (!isAuthenticated()) {
    window.location.href = "/login.html";
    return false;
  }
  try {
    const response = await fetch("/api/auth/me", { headers: authHeaders() });
    if (response.status === 401) {
      clearToken();
      window.location.href = "/login.html";
      return false;
    }
    const usuario = await response.json();
    // Atualiza o cache local com dados frescos do servidor
    localStorage.setItem(USER_KEY, JSON.stringify(usuario));
    if (usuario.papel !== "admin" && usuario.papel !== "admin_master") {
      window.location.href = "/";
      return false;
    }
    return true;
  } catch {
    window.location.href = "/login.html";
    return false;
  }
}

export function redirectIfAuthenticated() {
  if (isAuthenticated()) {
    window.location.href = "/";
    return true;
  }
  return false;
}