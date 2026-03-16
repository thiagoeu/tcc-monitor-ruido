/**
 * Página de Gráficos - Renderiza gráficos detalhados por ambiente
 */

async function loadGraficos() {
  try {
    const statusEl = document.getElementById("status");
    const containerEl = document.getElementById("graficos-container");

    // Busca ambientes e medições
    const ambientes = await fetchJson("/api/ambientes");
    const monitoramento = await fetchJson("/api/monitoramento?limit=100");

    if (!ambientes.length) {
      statusEl.textContent =
        "Nenhum ambiente cadastrado. Crie um ambiente no dashboard.";
      containerEl.innerHTML = '<div class="card">Sem dados para exibir.</div>';
      return;
    }

    statusEl.textContent = `Exibindo ${ambientes.length} ambiente(s)`;

    // Agrupa medições por ambiente
    const medicoesPorAmbiente = {};
    if (monitoramento.medicoes) {
      monitoramento.medicoes.forEach((med) => {
        const ambId = med.ambiente_id;
        if (!medicoesPorAmbiente[ambId]) {
          medicoesPorAmbiente[ambId] = [];
        }
        medicoesPorAmbiente[ambId].push(med);
      });

      // Ordena cada lista por data (mais recente primeiro) e pega as últimas 100
      Object.keys(medicoesPorAmbiente).forEach((ambId) => {
        medicoesPorAmbiente[ambId] = medicoesPorAmbiente[ambId]
          .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
          .slice(0, 100)
          .reverse(); // Inverte para ordena temporal crescente para o gráfico
      });
    }

    // Renderiza um card de gráfico para cada ambiente
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
            
            <div id="${statsId}" class="grafico-stats">
              <span>Carregando...</span>
            </div>
          </div>
        `;
      })
      .join("");

    // Desenha gráfen cada ambiente
    ambientes.forEach((amb) => {
      const medicoes = medicoesPorAmbiente[amb.id] || [];
      const canvasId = `grafico-${amb.id}`;
      const statsId = `stats-${amb.id}`;

      if (medicoes.length > 0) {
        drawDetailedChart(canvasId, medicoes, amb.limite_db);
        updateGraficoStats(statsId, medicoes, amb.limite_db);
      } else {
        const canvas = document.getElementById(canvasId);
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "#444";
        ctx.font = "14px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("Sem medições disponíveis", canvas.width / 2, canvas.height / 2);
      }
    });
  } catch (error) {
    document.getElementById("status").textContent = `Erro: ${error.message}`;
  }
}

function drawDetailedChart(canvasId, medicoes, limiteDb) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const padding = 40;

  // Valores
  const valores = medicoes.map((m) => m.db);
  const minDb = Math.min(...valores);
  const maxDb = Math.max(...valores);
  const range = Math.max(1, maxDb - minDb, 10); // Mínimo de 10 dB de range

  ctx.fillStyle = "#1a1f27";
  ctx.fillRect(0, 0, width, height);

  // Eixo X e Y
  ctx.strokeStyle = "#444";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padding, padding);
  ctx.lineTo(padding, height - padding);
  ctx.lineTo(width - padding, height - padding);
  ctx.stroke();

  // Labels dos eixos
  ctx.fillStyle = "#999";
  ctx.font = "12px sans-serif";
  ctx.textAlign = "right";
  ctx.fillText(`${Math.round(minDb)} dB`, padding - 10, height - padding + 15);
  ctx.fillText(`${Math.round(maxDb)} dB`, padding - 10, padding + 15);

  // Linha de limite
  if (limiteDb) {
    const limitY =
      height - padding - ((limiteDb - minDb) / range) * (height - 2 * padding);
    ctx.strokeStyle = "#ff8d8d";
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(padding, limitY);
    ctx.lineTo(width - padding, limitY);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = "#ff8d8d";
    ctx.font = "11px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText(`Limite: ${limiteDb} dB`, padding + 5, limitY - 5);
  }

  // Pontos e linha de tendência
  const graphWidth = width - 2 * padding;
  const graphHeight = height - 2 * padding;

  ctx.strokeStyle = "#5de08a";
  ctx.lineWidth = 2;
  ctx.beginPath();

  valores.forEach((db, index) => {
    const x = padding + (index / (valores.length - 1 || 1)) * graphWidth;
    const y = height - padding - ((db - minDb) / range) * graphHeight;

    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.stroke();

  // Círculos nos pontos
  ctx.fillStyle = "#5de08a";
  valores.forEach((db, index) => {
    const x = padding + (index / (valores.length - 1 || 1)) * graphWidth;
    const y = height - padding - ((db - minDb) / range) * graphHeight;
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fill();
  });

  // Grid de fundo
  ctx.strokeStyle = "#222";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 5; i++) {
    const y = padding + (i / 5) * (height - 2 * padding);
    ctx.beginPath();
    ctx.moveTo(padding, y);
    ctx.lineTo(width - padding, y);
    ctx.stroke();
  }
}

function updateGraficoStats(statsId, medicoes, limiteDb) {
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

// Carrega gráficos ao abrir a página
document.addEventListener("DOMContentLoaded", loadGraficos);

// Recarrega a cada 10 segundos
setInterval(loadGraficos, 10000);
