// relatorios.js — lógica da página de Relatórios

import { logout, requireAuth } from "./auth.js";
import {
  fetchRelatorioResumo,
  downloadRelatorioTxt,
  downloadRelatorioPdf,
  downloadRelatorioCsv
} from "./api.js";
import { formatDb, initDarkMode } from "./utils.js";

// ============ STATE ============
let state = {
  reportHours: 24,
};

// ============ RENDER ============

function renderReportSummary(report) {
  const summaryNode = document.getElementById("reportSummary");
  const tbody = document.getElementById("reportAmbientesBody");
  const totalEl = document.getElementById("totalRecords");
  const subtitleEl = document.getElementById("exportSubtitle");

  const geral = report.geral || {};

  if (totalEl) totalEl.textContent = geral.total_medicoes ?? 0;
  if (subtitleEl)
    subtitleEl.textContent = `Últimas ${state.reportHours}h · ${
      Number(geral.percentual_alerta ?? 0).toFixed(1)
    }% em alerta`;

  const items = [
    ["Total medições", geral.total_medicoes ?? 0],
    ["Total alertas", geral.total_alertas ?? 0],
    ["Leq (Nível Equiv.)", `${formatDb(geral.leq_db)} dB(A)`],
    ["Média dB", `${formatDb(geral.media_db)} dB`],
    ["Mediana dB", `${formatDb(geral.mediana_db)} dB`],
    ["Pico dB", `${formatDb(geral.pico_db)} dB`],
  ];

  summaryNode.innerHTML = items
    .map(
      ([label, value]) =>
        `<div class="metric">
          <div class="label">${label}</div>
          <div class="value">${value}</div>
        </div>`,
    )
    .join("");

  const ambientes = report.ambientes || [];
  if (!ambientes.length) {
    tbody.innerHTML =
      '<tr><td colspan="7" class="empty-state">Sem dados para a janela informada.</td></tr>';
    return;
  }

  tbody.innerHTML = ambientes
    .map(
      (a) => `
      <tr>
        <td>${a.nome}<br><small style="color:var(--text-muted)">${a.sensor_id}</small></td>
        <td>${a.total_medicoes}</td>
        <td>${a.total_alertas}</td>
        <td style="font-weight: 600;">${formatDb(a.leq_db)}</td>
        <td>${formatDb(a.media_db)}</td>
        <td>${formatDb(a.mediana_db)}</td>
        <td style="color:var(--danger);font-weight:600;">${formatDb(a.pico_db)} dB</td>
      </tr>`,
    )
    .join("");
}

// ============ LOAD ============

async function loadReport() {
  try {
    const report = await fetchRelatorioResumo(state.reportHours);
    renderReportSummary(report);
  } catch {
    const summaryNode = document.getElementById("reportSummary");
    summaryNode.innerHTML =
      '<div class="metric"><div class="label">Erro</div><div class="value">—</div></div>';
  }
}

// ============ CONTROLES ============

function initControls() {
  const hoursInput = document.getElementById("reportHours");
  const refreshBtn = document.getElementById("refreshReportBtn");
  const downloadTxtBtn = document.getElementById("downloadTxtBtn");
  const downloadPdfBtn = document.getElementById("downloadPdfBtn");
  const downloadCsvBtn = document.getElementById("downloadCsvBtn");

  hoursInput?.addEventListener("change", () => {
    const v = Number(hoursInput.value);
    state.reportHours =
      Number.isFinite(v) && v > 0 ? Math.min(720, v) : 24;
    hoursInput.value = String(state.reportHours);
  });

  refreshBtn?.addEventListener("click", loadReport);
  downloadTxtBtn?.addEventListener("click", () => downloadRelatorioTxt(state.reportHours));
  downloadPdfBtn?.addEventListener("click", () => downloadRelatorioPdf(state.reportHours));
  downloadCsvBtn?.addEventListener("click", () => downloadRelatorioCsv(state.reportHours));

  // Logout
  document.getElementById("logoutBtn")?.addEventListener("click", () => logout());
}

// ============ BOOTSTRAP ============

function bootstrap() {
  if (!requireAuth()) return;
  initDarkMode();
  initControls();
  loadReport();
}

bootstrap();
