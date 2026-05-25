// dashboard.js - lógica da página inicial (index.html)
import {
  fetchMonitoramento,
  fetchSensoresFisicos,
  fetchRelatorioResumo,
  criarAmbiente,
  excluirAmbiente,
  downloadRelatorioTxt,
} from "./api.js";
import { toLocalDate, formatDb, statusTag } from "./utils.js";
import { drawTrendChart, drawAlertRateChart } from "./charts.js";

let state = {
  reportHours: 24,
  scan: {
    port: "/dev/ttyAMA0",
    baudrate: 9600,
    start_id: 1,
    end_id: 32,
    registers: "0,1",
    function_code: 3,
  },
};

function renderSensoresFisicos(scanResult) {
  const tbody = document.getElementById("sensoresBody");
  const resumo = document.getElementById("sensoresResumo");
  const portasResumo = document.getElementById("portasResumo");
  const sensores = scanResult?.sensores || [];
  const portas = scanResult?.portas_detectadas || [];

  resumo.textContent =
    `Varredura em ${scanResult.porta} (${scanResult.baudrate} 8N1): ` +
    `${scanResult.total_encontrados} sensor(es) físico(s) encontrado(s).`;

  if (!sensores.length) {
    tbody.innerHTML = '<tr><td colspan="4">Nenhum ID Modbus respondeu nesta varredura.</td></tr>';
  } else {
    tbody.innerHTML = sensores
    .map(
      (sensor) => `
    <tr>
      <td><strong>${sensor.id_modbus}</strong></td>
      <td>${sensor.register}</td>
      <td>${sensor.raw_value}</td>
      <td>
        <button
          type="button"
          class="ghost-btn"
          data-fill-sensor-id="${sensor.id_modbus}"
        >
          Preencher sensor_id
        </button>
      </td>
    </tr>
  `,
    )
    .join("");
  }

  if (!portas.length) {
    portasResumo.textContent = "Portas detectadas: nenhuma.";
  } else {
    const labels = portas.map((porta) => porta.device).join(", ");
    portasResumo.textContent = `Portas detectadas: ${labels}`;
  }

  attachSensorFillHandlers();
}

function attachSensorFillHandlers() {
  document.querySelectorAll("[data-fill-sensor-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const sensorId = button.getAttribute("data-fill-sensor-id") || "";
      const form = document.getElementById("ambienteForm");
      const field = form?.elements?.sensor_id;
      if (!field) return;

      field.value = sensorId;
      field.focus();

      const formMessage = document.getElementById("formMessage");
      formMessage.textContent = `sensor_id preenchido com '${sensorId}'. Edite se quiser outro nome.`;
    });
  });
}

function getScanParamsFromUI() {
  return {
    port: document.getElementById("scanPort")?.value?.trim() || "/dev/ttyAMA0",
    baudrate: Number(document.getElementById("scanBaudrate")?.value || 9600),
    start_id: Number(document.getElementById("scanStartId")?.value || 1),
    end_id: Number(document.getElementById("scanEndId")?.value || 32),
    registers: document.getElementById("scanRegisters")?.value?.trim() || "0,1",
    function_code: Number(document.getElementById("scanFunctionCode")?.value || 3),
  };
}

async function loadSensoresFisicos() {
  const resumo = document.getElementById("sensoresResumo");
  const button = document.getElementById("scanSensoresBtn");
  const params = getScanParamsFromUI();

  state.scan = params;
  resumo.textContent = "Escaneando sensores físicos na serial...";
  button.disabled = true;

  try {
    const result = await fetchSensoresFisicos(params);
    renderSensoresFisicos(result);
  } catch (error) {
    document.getElementById("sensoresBody").innerHTML =
      `<tr><td colspan="4">Falha ao escanear: ${error.message}</td></tr>`;
    document.getElementById("portasResumo").textContent = "";
    resumo.textContent = "Não foi possível ler os sensores físicos agora.";
  } finally {
    button.disabled = false;
  }
}

function renderAmbientes(ambientes, ultimaPorAmbiente) {
  const container = document.getElementById("ambientes");
  if (!ambientes.length) {
    container.innerHTML = '<div class="card">Nenhum ambiente cadastrado.</div>';
    return;
  }
  container.innerHTML = ambientes
    .map((ambiente) => {
      const ultima =
        ultimaPorAmbiente[String(ambiente.id)] ||
        ultimaPorAmbiente[ambiente.id];
      const db = ultima ? formatDb(ultima.db) : "-";
      const excedeu = ultima ? Boolean(ultima.excedeu_limite) : false;
      const horario = ultima ? toLocalDate(ultima.created_at) : "Sem medições";
      return `
      <div class="card">
        <div class="card-head">
          <h3>${ambiente.nome}</h3>
          <button class="danger-btn" data-delete-id="${ambiente.id}" type="button">Excluir</button>
        </div>
        <div>Local: ${ambiente.localizacao}</div>
        <div>Sensor: ${ambiente.sensor_id}</div>
        <div>Limite: ${formatDb(ambiente.limite_db)} dB</div>
        <div>Último valor: <strong>${db} dB</strong></div>
        <div style="margin-top:6px">${ultima ? statusTag(excedeu) : '<span class="tag ok">Sem leitura</span>'}</div>
        <div class="small" style="margin-top:8px;color:var(--muted)">${horario}</div>
      </div>
    `;
    })
    .join("");
  attachDeleteHandlers();
}

function attachDeleteHandlers() {
  document.querySelectorAll("[data-delete-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const ambienteId = Number(button.getAttribute("data-delete-id"));
      if (!Number.isFinite(ambienteId)) return;
      if (!confirm("Deseja realmente excluir este ambiente/sensor?")) return;
      try {
        await excluirAmbiente(ambienteId);
        await loadDashboard();
        await loadReport();
      } catch (error) {
        document.getElementById("status").textContent =
          `Erro ao excluir: ${error.message}`;
      }
    });
  });
}

function renderMedicoes(medicoes) {
  const tbody = document.getElementById("medicoesBody");
  if (!medicoes.length) {
    tbody.innerHTML = '<tr><td colspan="5">Sem medições.</td></tr>';
    return;
  }
  tbody.innerHTML = medicoes
    .map(
      (medicao) => `
    <tr>
      <td>${toLocalDate(medicao.created_at)}</td>
      <td>${medicao.ambiente_nome}</td>
      <td>${medicao.sensor_id}</td>
      <td>${formatDb(medicao.db)}</td>
      <td>${statusTag(Boolean(medicao.excedeu_limite))}</td>
    </tr>
  `,
    )
    .join("");
}

function renderAlertas(alertas) {
  const tbody = document.getElementById("alertasBody");
  if (!alertas.length) {
    tbody.innerHTML = '<tr><td colspan="3">Sem alertas.</td></tr>';
    return;
  }
  tbody.innerHTML = alertas
    .map(
      (alerta) => `
    <tr>
      <td>${toLocalDate(alerta.created_at)}</td>
      <td>${alerta.ambiente_nome || "-"}</td>
      <td>${alerta.mensagem}</td>
    </tr>
  `,
    )
    .join("");
}

function renderReportSummary(report) {
  const summaryNode = document.getElementById("reportSummary");
  const geral = report.geral || {};
  const items = [
    ["Total medições", geral.total_medicoes ?? 0],
    ["Total alertas", geral.total_alertas ?? 0],
    ["% alerta", `${Number(geral.percentual_alerta ?? 0).toFixed(2)}%`],
    ["Média dB", formatDb(geral.media_db)],
    ["Pico dB", formatDb(geral.pico_db)],
    ["Mínimo dB", formatDb(geral.minimo_db)],
  ];
  summaryNode.innerHTML = items
    .map(
      ([label, value]) => `
    <div class="metric">
      <p class="label">${label}</p>
      <p class="value">${value}</p>
    </div>
  `,
    )
    .join("");
  const tbody = document.getElementById("reportAmbientesBody");
  const ambientes = report.ambientes || [];
  if (!ambientes.length) {
    tbody.innerHTML =
      '<tr><td colspan="6">Sem dados para a janela informada.</td></tr>';
    return;
  }
  tbody.innerHTML = ambientes
    .map(
      (ambiente) => `
    <tr>
      <td>${ambiente.nome} (${ambiente.sensor_id})</td>
      <td>${ambiente.total_medicoes}</td>
      <td>${ambiente.total_alertas}</td>
      <td>${Number(ambiente.percentual_alerta || 0).toFixed(2)}%</td>
      <td>${formatDb(ambiente.media_db)}</td>
      <td>${formatDb(ambiente.pico_db)}</td>
    </tr>
  `,
    )
    .join("");
}

async function loadDashboard() {
  try {
    const data = await fetchMonitoramento(80);
    const ambientes = data.ambientes || [];
    renderAmbientes(ambientes, data.ultima_por_ambiente || {});
    renderMedicoes(data.medicoes || []);
    renderAlertas(data.alertas || []);
    drawTrendChart(data.medicoes || []);
    document.getElementById("status").textContent =
      `Online • Atualizado em ${new Date().toLocaleString("pt-BR")}`;
  } catch (error) {
    document.getElementById("status").textContent =
      `Offline/rede instável: ${error.message}`;
  }
}

async function loadReport() {
  try {
    const report = await fetchRelatorioResumo(state.reportHours);
    renderReportSummary(report);
    drawAlertRateChart(report);
  } catch (error) {
    const summaryNode = document.getElementById("reportSummary");
    summaryNode.innerHTML = `<div class="metric"><p class="label">Erro</p><p class="value">${error.message}</p></div>`;
    drawAlertRateChart({ ambientes: [] });
  }
}

async function submitAmbiente(event) {
  event.preventDefault();
  const form = event.target;
  const formMessage = document.getElementById("formMessage");
  const payload = {
    nome: form.nome.value.trim(),
    localizacao: form.localizacao.value.trim(),
    sensor_id: form.sensor_id.value.trim(),
    limite_db: Number(form.limite_db.value),
  };
  try {
    await criarAmbiente(payload);
    form.reset();
    form.limite_db.value = "65";
    formMessage.textContent = "Ambiente cadastrado com sucesso.";
    await loadDashboard();
    await loadReport();
  } catch (error) {
    formMessage.textContent = error.message;
  }
}

function initReportControls() {
  const hoursInput = document.getElementById("reportHours");
  const refreshBtn = document.getElementById("refreshReportBtn");
  const downloadBtn = document.getElementById("downloadTxtBtn");
  hoursInput.addEventListener("change", () => {
    let value = Number(hoursInput.value);
    state.reportHours =
      Number.isFinite(value) && value > 0 ? Math.min(720, value) : 24;
    hoursInput.value = String(state.reportHours);
  });
  refreshBtn.addEventListener("click", loadReport);
  downloadBtn.addEventListener("click", () =>
    downloadRelatorioTxt(state.reportHours),
  );
}

function initSensorScanControls() {
  document
    .getElementById("scanSensoresBtn")
    .addEventListener("click", loadSensoresFisicos);
}

function bootstrap() {
  document
    .getElementById("ambienteForm")
    .addEventListener("submit", submitAmbiente);
  initReportControls();
  initSensorScanControls();
  loadDashboard();
  loadSensoresFisicos();
  loadReport();
  setInterval(loadDashboard, 5000);
}

bootstrap();
