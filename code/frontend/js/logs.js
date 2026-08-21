// logs.js — lógica da página de Logs (logs.html)
// Responsabilidade: tabela de medições recentes, tabela de alertas.

import { logout, requireAuth } from "./auth.js";
import { fetchMonitoramento } from "./api.js";
import { toLocalDate, formatDb, statusTag, initDarkMode } from "./utils.js";

// ============ STATE ============

let state = {
  filtroStatus: "", // "" | "alerta" | "normal"
  medicoes: [],
  alertas: [],
};

// ============ RENDER — MEDIÇÕES ============

function renderMedicoes() {
  const tbody = document.getElementById("medicoesBody");
  const countEl = document.getElementById("medicoes-count");

  let items = state.medicoes;

  // Filtro por status
  if (state.filtroStatus === "alerta") {
    items = items.filter((m) => Boolean(m.excedeu_limite));
  } else if (state.filtroStatus === "normal") {
    items = items.filter((m) => !m.excedeu_limite);
  }

  if (countEl) countEl.textContent = `${items.length} registros`;

  if (!items.length) {
    tbody.innerHTML =
      '<tr><td colspan="5" class="empty-state">Nenhuma medição encontrada.</td></tr>';
    return;
  }

  tbody.innerHTML = items
    .map(
      (m) => `
      <tr>
        <td>${toLocalDate(m.created_at)}</td>
        <td>${m.ambiente_nome || "-"}</td>
        <td><code style="font-size:.82rem;color:var(--text-secondary);">${m.sensor_id}</code></td>
        <td style="font-weight:600;color:${m.excedeu_limite ? "var(--danger)" : "var(--accent)"};">${formatDb(m.db)} dB</td>
        <td>${statusTag(Boolean(m.excedeu_limite))}</td>
      </tr>`,
    )
    .join("");
}

// ============ RENDER — ALERTAS ============

function renderAlertas() {
  const tbody = document.getElementById("alertasBody");
  const countEl = document.getElementById("alertas-count");
  const alertas = state.alertas;

  if (countEl) {
    countEl.textContent = `${alertas.length} alerta${alertas.length !== 1 ? "s" : ""}`;
  }

  if (!alertas.length) {
    tbody.innerHTML =
      '<tr><td colspan="3" class="empty-state">Nenhum alerta recente.</td></tr>';
    return;
  }

  tbody.innerHTML = alertas
    .map(
      (a) => `
      <tr>
        <td>${toLocalDate(a.created_at)}</td>
        <td>${a.ambiente_nome || "-"}</td>
        <td>${a.mensagem}</td>
      </tr>`,
    )
    .join("");
}

// ============ LOAD ============

async function loadData() {
  try {
    const data = await fetchMonitoramento(200);
    state.medicoes = data.medicoes || [];
    state.alertas = data.alertas || [];
    renderMedicoes();
    renderAlertas();

    const lastUpdate = document.getElementById("last-update");
    if (lastUpdate) {
      lastUpdate.textContent = `Atualizado em ${new Date().toLocaleString("pt-BR")}`;
    }
  } catch {
    // erros exibidos via showToast em utils.js
  }
}

// ============ CONTROLES ============

function initControls() {
  // Filtro status
  const filtroStatus = document.getElementById("filtroStatus");
  filtroStatus?.addEventListener("change", () => {
    state.filtroStatus = filtroStatus.value;
    renderMedicoes();
  });

  // Logout
  document.getElementById("logoutBtn")?.addEventListener("click", () => logout());
}

// ============ BOOTSTRAP ============

function bootstrap() {
  if (!requireAuth()) return;
  initDarkMode();
  initControls();
  loadData();
  // Atualização automática menos agressiva que o dashboard
  setInterval(loadData, 10_000);
}

bootstrap();
