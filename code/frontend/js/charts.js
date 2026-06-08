//funções de desenho dos gráficos (canvas)

import { formatDb } from "./utils.js";

export function drawEmptyChart(canvas, message) {
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#a8b2c0";
  ctx.font = "13px Arial";
  ctx.fillText(message, 10, Math.max(20, height / 2));
}

export function drawTrendChart(medicoes) {
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
    const x =
      padding +
      (index * (width - padding * 2)) / Math.max(points.length - 1, 1);
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

export function drawAlertRateChart(report) {
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
  const barWidth = Math.max(
    24,
    barAreaWidth / Math.max(ambientes.length * 1.7, 1),
  );
  const gap = barWidth * 0.7;
  ambientes.forEach((ambiente, index) => {
    const percent = Math.max(
      0,
      Math.min(100, Number(ambiente.percentual_alerta || 0)),
    );
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

export function drawDetailedChart(canvasId, medicoes, limiteDb) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const padding = 40;
  const valores = medicoes.map((m) => m.db);
  const minDb = Math.min(...valores);
  const maxDb = Math.max(...valores);
  const range = Math.max(1, maxDb - minDb, 10);
  ctx.fillStyle = "#1a1f27";
  ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = "#444";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padding, padding);
  ctx.lineTo(padding, height - padding);
  ctx.lineTo(width - padding, height - padding);
  ctx.stroke();
  ctx.fillStyle = "#999";
  ctx.font = "12px sans-serif";
  ctx.textAlign = "right";
  ctx.fillText(`${Math.round(minDb)} dB`, padding - 10, height - padding + 15);
  ctx.fillText(`${Math.round(maxDb)} dB`, padding - 10, padding + 15);
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
  const graphWidth = width - 2 * padding;
  const graphHeight = height - 2 * padding;
  ctx.strokeStyle = "#5de08a";
  ctx.lineWidth = 2;
  ctx.beginPath();
  valores.forEach((db, index) => {
    const x = padding + (index / (valores.length - 1 || 1)) * graphWidth;
    const y = height - padding - ((db - minDb) / range) * graphHeight;
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
  ctx.fillStyle = "#5de08a";
  valores.forEach((db, index) => {
    const x = padding + (index / (valores.length - 1 || 1)) * graphWidth;
    const y = height - padding - ((db - minDb) / range) * graphHeight;
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fill();
  });
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
