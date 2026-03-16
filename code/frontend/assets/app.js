const state = {
  reportHours: 24,
};

function toLocalDate(isoDate) {
  if (!isoDate) return "-";
  return new Date(isoDate).toLocaleString("pt-BR");
}

function statusTag(excedeu) {
  return excedeu
    ? '<span class="tag warn">Acima do limite</span>'
    : '<span class="tag ok">Normal</span>';
}

async function fetchJson(path, options = {}) {
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

function formatDb(value) {
  if (value === null || value === undefined) return "-";
  return Number(value).toFixed(1);
}

function renderAmbientes(ambientes, ultimaPorAmbiente) {
  const container = document.getElementById("ambientes");
  if (!ambientes.length) {
    container.innerHTML = '<div class="card">Nenhum ambiente cadastrado.</div>';
    return;
  }

  container.innerHTML = ambientes
    .map((ambiente) => {
      const ultima = ultimaPorAmbiente[String(ambiente.id)] || ultimaPorAmbiente[ambiente.id];
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

      const confirmed = window.confirm("Deseja realmente excluir este ambiente/sensor?");
      if (!confirmed) return;

      try {
        await fetchJson(`/api/ambientes/${ambienteId}`, { method: "DELETE" });
        await loadDashboard();
        await loadReport();
      } catch (error) {
        document.getElementById("status").textContent = `Erro ao excluir: ${error.message}`;
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
    `
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
    `
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
    `
    )
    .join("");

  const tbody = document.getElementById("reportAmbientesBody");
  const ambientes = report.ambientes || [];

  if (!ambientes.length) {
    tbody.innerHTML = '<tr><td colspan="6">Sem dados para a janela informada.</td></tr>';
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
    `
    )
    .join("");
}

function drawEmptyChart(canvas, message) {
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#a8b2c0";
  ctx.font = "13px Arial";
  ctx.fillText(message, 10, Math.max(20, height / 2));
}

function drawTrendChart(medicoes) {
  const canvas = document.getElementById("trendChart");
  if (!canvas) return;

  if (!medicoes || !medicoes.length) {
    drawEmptyChart(canvas, "Sem medições para exibir.");
    return;
  }

  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const padding = 24;

  ctx.clearRect(0, 0, width, height);

  const points = [...medicoes].reverse().slice(-25);
  const values = points.map((item) => Number(item.db || 0));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(1, max - min);

  ctx.strokeStyle = "#2a3444";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padding, height - padding);
  ctx.lineTo(width - padding, height - padding);
  ctx.stroke();

  ctx.beginPath();
  points.forEach((point, index) => {
    const x = padding + (index * (width - padding * 2)) / Math.max(points.length - 1, 1);
    const normalized = (Number(point.db) - min) / range;
    const y = height - padding - normalized * (height - padding * 2);
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.strokeStyle = "#5de08a";
  ctx.lineWidth = 2;
  ctx.stroke();

  const last = points[points.length - 1];
  ctx.fillStyle = "#a8b2c0";
  ctx.font = "12px Arial";
  ctx.fillText(`Último: ${formatDb(last.db)} dB`, 10, 14);
}

function drawAlertRateChart(report) {
  const canvas = document.getElementById("alertRateChart");
  if (!canvas) return;

  const ambientes = report?.ambientes || [];
  if (!ambientes.length) {
    drawEmptyChart(canvas, "Sem dados de relatório.");
    return;
  }

  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const padding = 16;

  ctx.clearRect(0, 0, width, height);

  const barAreaWidth = width - padding * 2;
  const barWidth = Math.max(24, barAreaWidth / Math.max(ambientes.length * 1.7, 1));
  const gap = barWidth * 0.7;

  ambientes.forEach((ambiente, index) => {
    const percent = Math.max(0, Math.min(100, Number(ambiente.percentual_alerta || 0)));
    const barHeight = ((height - 42) * percent) / 100;
    const x = padding + index * (barWidth + gap);
    const y = height - 22 - barHeight;

    ctx.fillStyle = "#ff8d8d";
    ctx.fillRect(x, y, barWidth, barHeight);

    ctx.fillStyle = "#a8b2c0";
    ctx.font = "11px Arial";
    ctx.fillText(`${percent.toFixed(0)}%`, x, y - 4);
    ctx.fillText(ambiente.sensor_id, x, height - 6);
  });
}

async function loadDashboard() {
  try {
    const data = await fetchJson("/api/monitoramento?limit=80");
    renderAmbientes(data.ambientes || [], data.ultima_por_ambiente || {});
    renderMedicoes(data.medicoes || []);
    renderAlertas(data.alertas || []);
    drawTrendChart(data.medicoes || []);
    document.getElementById("status").textContent = `Online • Atualizado em ${new Date().toLocaleString("pt-BR")}`;
  } catch (error) {
    document.getElementById("status").textContent = `Offline/rede instável: ${error.message}`;
  }
}

async function loadReport() {
  try {
    const report = await fetchJson(`/api/relatorios/resumo?hours=${state.reportHours}`);
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
    await fetchJson("/api/ambientes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
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

  hoursInput.addEventListener("change", async () => {
    const value = Number(hoursInput.value);
    state.reportHours = Number.isFinite(value) && value > 0 ? Math.min(720, value) : 24;
    hoursInput.value = String(state.reportHours);
  });

  refreshBtn.addEventListener("click", loadReport);

  downloadBtn.addEventListener("click", () => {
    window.location.href = `/api/relatorios/txt?hours=${state.reportHours}`;
  });
}

function bootstrap() {
  document.getElementById("ambienteForm").addEventListener("submit", submitAmbiente);
  initReportControls();
  loadDashboard();
  loadReport();
  setInterval(loadDashboard, 5000);
}

bootstrap();
