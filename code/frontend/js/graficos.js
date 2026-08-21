import { fetchAmbientes, fetchMonitoramento } from "./api.js";
import { formatDb, initDarkMode } from "./utils.js";
import { drawDetailedChart } from "./charts.js";
import { logout, requireAuth } from "./auth.js";

if (!requireAuth()) {
  // sem sessão — já foi redirecionado para /login.html
}

async function loadGraficos() {
  try {
    const statusEl = document.getElementById("status");
    const containerEl = document.getElementById("graficos-container");
    const ambientes = await fetchAmbientes();
    const monitoramento = await fetchMonitoramento(100);

    if (!ambientes.length) {
      statusEl.textContent =
        "Nenhum ambiente cadastrado. Crie um ambiente no dashboard.";
      containerEl.innerHTML = '<div class="card">Sem dados para exibir.</div>';
      return;
    }
    statusEl.textContent = `Exibindo ${ambientes.length} ambiente(s)`;

    const medicoesPorAmbiente = {};
    if (monitoramento.medicoes) {
      monitoramento.medicoes.forEach((med) => {
        const ambId = med.ambiente_id;
        if (!medicoesPorAmbiente[ambId]) medicoesPorAmbiente[ambId] = [];
        medicoesPorAmbiente[ambId].push(med);
      });
      Object.keys(medicoesPorAmbiente).forEach((ambId) => {
        medicoesPorAmbiente[ambId] = medicoesPorAmbiente[ambId]
          .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
          .slice(0, 100)
          .reverse();
      });
    }

    containerEl.innerHTML = ambientes
      .map((amb) => {
        const medicoes = medicoesPorAmbiente[amb.id] || [];
        const canvasId = `grafico-${amb.id}`;
        const statsId = `stats-${amb.id}`;
        return `
        <div class="grafico-card">
          <div class="grafico-header">
            <h3>${amb.nome}</h3>
            <small>${amb.localizacao} • ID: ${amb.sensor_id}</small>
          </div>
          <canvas id="${canvasId}" height="200"></canvas>
          <div id="${statsId}" class="grafico-stats"><span>Carregando...</span></div>
        </div>
      `;
      })
      .join("");

    ambientes.forEach((amb) => {
      const medicoes = medicoesPorAmbiente[amb.id] || [];
      const canvasId = `grafico-${amb.id}`;
      const statsId = `stats-${amb.id}`;
      if (medicoes.length > 0) {
        drawDetailedChart(canvasId, medicoes, amb.limite_db);
        updateGraficoStats(statsId, medicoes);
      } else {
        const canvas = document.getElementById(canvasId);
        if (canvas) {
          const ctx = canvas.getContext("2d");
          ctx.fillStyle = "#444";
          ctx.font = "14px sans-serif";
          ctx.textAlign = "center";
          ctx.fillText(
            "Sem medições disponíveis",
            canvas.width / 2,
            canvas.height / 2,
          );
        }
      }
    });
  } catch (error) {
    document.getElementById("status").textContent = `Erro: ${error.message}`;
  }
}

function updateGraficoStats(statsId, medicoes) {
  const statsEl = document.getElementById(statsId);
  if (!statsEl) return;
  const valores = medicoes.map((m) => m.db);
  const media = valores.reduce((a, b) => a + b, 0) / valores.length;
  const minDb = Math.min(...valores);
  const maxDb = Math.max(...valores);
  const alertas = medicoes.filter((m) => m.excedeu_limite).length;
  const percentualAlerta = ((alertas / medicoes.length) * 100).toFixed(1);
  statsEl.innerHTML = `
    <div class="stat-item">
      <span class="stat-label">Última</span>
      <span class="stat-value">${formatDb(valores[valores.length - 1])} dB</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">Média</span>
      <span class="stat-value">${formatDb(media)} dB</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">Mín/Máx</span>
      <span class="stat-value">${formatDb(minDb)} / ${formatDb(maxDb)} dB</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">Alertas</span>
      <span class="stat-value ${percentualAlerta > 20 ? "alert" : ""}">${percentualAlerta}%</span>
    </div>
  `;
}

document.addEventListener("DOMContentLoaded", () => {
  initDarkMode();
  document
    .getElementById("logoutBtn")
    ?.addEventListener("click", () => logout());
  loadGraficos();
});
setInterval(loadGraficos, 10000);
