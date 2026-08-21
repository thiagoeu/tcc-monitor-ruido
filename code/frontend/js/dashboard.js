// dashboard.js — lógica do Dashboard (index.html)
// Responsabilidade: cards de ambientes em tempo real + mini-gráficos de tendência.
// Medições detalhadas, alertas e relatórios → logs.js
// Cadastro de ambiente e scan de sensores → configuracoes.js

import { logout, requireAuth } from "./auth.js";
import { fetchMonitoramento, fetchRelatorioResumo } from "./api.js";
import { toLocalDate, formatDb, statusTag, initDarkMode } from "./utils.js";
import { drawTrendChart, drawAlertRateChart } from "./charts.js";

// ============ RENDER ============

function renderAmbientes(ambientes, ultimaPorAmbiente, servidorEm) {
  const container = document.getElementById("ambientes");
  if (!ambientes.length) {
    container.innerHTML =
      '<div class="card empty-state">Nenhum ambiente cadastrado.<br>' +
      '<a href="/configuracoes.html" style="color:var(--accent);font-size:.85rem;">Cadastrar ambiente →</a></div>';
    return;
  }

  const referenceTime = servidorEm
    ? new Date(servidorEm).getTime()
    : new Date().getTime();

  container.innerHTML = ambientes
    .map((ambiente) => {
      const ultima =
        ultimaPorAmbiente[String(ambiente.id)] ||
        ultimaPorAmbiente[ambiente.id];

      const hasActiveSession = Boolean(ambiente.em_uso);
      let hasRecentMeasurement = false;
      if (ultima && ultima.created_at) {
        const lastTime = new Date(ultima.created_at).getTime();
        if (Math.abs(referenceTime - lastTime) < 20000) {
          hasRecentMeasurement = true;
        }
      }

      const emUso = hasActiveSession || hasRecentMeasurement;
      const db = ultima && emUso ? formatDb(ultima.db) : "-";
      const excedeu = ultima && emUso ? Boolean(ultima.excedeu_limite) : false;

      let statusHtml = "";
      let horario = "";

      if (emUso) {
        statusHtml = statusTag(excedeu);
        horario = ultima ? toLocalDate(ultima.created_at) : "Sem medições";
      } else {
        statusHtml = '<span class="tag muted-tag">Sem medições</span>';
        horario = "Sem medições";
      }

      return `
        <div class="card">
          <div class="card-head">
            <h3>${ambiente.nome}</h3>
            ${statusHtml}
          </div>
          <div style="font-size:.82rem;color:var(--text-secondary);margin-bottom:6px;">
            📍 ${ambiente.localizacao} &nbsp;·&nbsp; 🔊 ${ambiente.sensor_id}
          </div>
          <div style="font-size:2rem;font-weight:700;color:${excedeu && emUso ? "var(--danger)" : "var(--accent)"};line-height:1.1;">
            ${db !== "-" ? db + " dB" : "—"}
          </div>
          <div style="font-size:.78rem;color:var(--text-muted);margin-top:6px;">
            Limite: ${formatDb(ambiente.limite_db)} dB &nbsp;·&nbsp; ${horario}
          </div>
        </div>
      `;
    })
    .join("");
}

// ============ LOAD ============

async function loadDashboard() {
  try {
    const data = await fetchMonitoramento(80);
    const ambientes = data.ambientes || [];
    renderAmbientes(ambientes, data.ultima_por_ambiente || {}, data.servidor_em);

    const referenceTime = data.servidor_em
      ? new Date(data.servidor_em).getTime()
      : new Date().getTime();

    const activeSensorIds = new Set(
      ambientes
        .filter((a) => {
          const hasActiveSession = Boolean(a.em_uso);
          const ultima =
            (data.ultima_por_ambiente || {})[String(a.id)] ||
            (data.ultima_por_ambiente || {})[a.id];
          let hasRecentMeasurement = false;
          if (ultima && ultima.created_at) {
            const lastTime = new Date(ultima.created_at).getTime();
            if (Math.abs(referenceTime - lastTime) < 20000) {
              hasRecentMeasurement = true;
            }
          }
          return hasActiveSession || hasRecentMeasurement;
        })
        .map((a) => a.sensor_id),
    );

    const activeMedicoes = (data.medicoes || []).filter((med) =>
      activeSensorIds.has(med.sensor_id),
    );
    drawTrendChart(activeMedicoes);

    document.getElementById("status").textContent =
      `Online · Atualizado em ${new Date().toLocaleString("pt-BR")}`;
    setOnlineStatus(true);
  } catch {
    document.getElementById("status").textContent =
      "Offline / rede instável — tentando reconectar...";
    setOnlineStatus(false);
  }
}

async function loadReport() {
  try {
    const report = await fetchRelatorioResumo(24);
    drawAlertRateChart(report);
  } catch {
    drawAlertRateChart({ ambientes: [] });
  }
}

function setOnlineStatus(online) {
  const dot = document.getElementById("status-dot");
  const badge = document.getElementById("badge-online");
  if (dot) dot.classList.toggle("offline", !online);
  if (badge) badge.style.display = online ? "" : "none";
}

// ============ BOOTSTRAP ============

function bootstrap() {
  if (!requireAuth()) return;

  // Dark mode
  initDarkMode();

  // Logout
  document
    .getElementById("logoutBtn")
    ?.addEventListener("click", () => logout());

  // Dados iniciais
  loadDashboard();
  loadReport();

  // Auto-refresh a cada 5s
  setInterval(loadDashboard, 5000);

  // Redraw charts on theme change
  window.addEventListener("themeChanged", () => {
    loadDashboard();
    loadReport();
  });
}

bootstrap();
