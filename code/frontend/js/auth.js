// auth.js - gerenciamento de autenticação no cliente

const TOKEN_KEY = "noiseradar_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function isAuthenticated() {
  return Boolean(getToken());
}

export function authHeaders(extra = {}) {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}`, ...extra } : { ...extra };
}

export async function login(email, senha) {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, senha }),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.erro || "Falha no login");
  }
  setToken(body.token);
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

export function redirectIfAuthenticated() {
  if (isAuthenticated()) {
    window.location.href = "/";
    return true;
  }
  return false;
}