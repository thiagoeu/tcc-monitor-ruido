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
  
  // Set sharp resolution
  const width = canvas.clientWidth || canvas.width || 300;
  const height = canvas.clientHeight || canvas.height || 170;
  canvas.width = width;
  canvas.height = height;
  ctx.clearRect(0, 0, width, height);

  // Group measurements by environment (last 60 readings)
  const recentMedicoes = [...medicoes].reverse().slice(-60);
  const groups = {};
  recentMedicoes.forEach((med) => {
    const key = med.ambiente_id || med.sensor_id;
    if (!groups[key]) {
      groups[key] = {
        id: key,
        sensor_id: med.sensor_id,
        ambiente_nome: med.ambiente_nome || med.sensor_id,
        medicoes: [],
      };
    }
    groups[key].medicoes.push(med);
  });

  const activeGroups = Object.values(groups);
  if (!activeGroups.length) {
    drawEmptyChart(canvas, "Sem medições para exibir.");
    return;
  }

  // Color palette for different sensors
  const palette = ["#5de08a", "#60a5fa", "#fbbf24", "#a78bfa", "#f87171", "#22d3ee", "#e879f9"];
  activeGroups.forEach((group, index) => {
    group.color = palette[index % palette.length];
  });

  // Scale Y-axis
  const allValues = recentMedicoes.map((m) => Number(m.db || 0));
  const minDb = Math.max(30, Math.min(...allValues) - 2);
  const maxDb = Math.max(minDb + 10, Math.max(...allValues) + 2);
  const range = maxDb - minDb;

  const paddingLeft = 45;
  const paddingRight = 15;
  const paddingTop = 35;
  const paddingBottom = 20;

  const graphWidth = width - paddingLeft - paddingRight;
  const graphHeight = height - paddingTop - paddingBottom;

  // Background
  ctx.fillStyle = "#0f1217";
  ctx.fillRect(0, 0, width, height);

  // Horizontal grid lines & Y labels
  ctx.strokeStyle = "#1f2937";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#9ca3af";
  ctx.font = "10px sans-serif";
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";

  const gridLines = 4;
  for (let i = 0; i <= gridLines; i++) {
    const y = paddingTop + (i / gridLines) * graphHeight;
    const val = maxDb - (i / gridLines) * range;
    
    ctx.beginPath();
    ctx.moveTo(paddingLeft, y);
    ctx.lineTo(width - paddingRight, y);
    ctx.stroke();

    ctx.fillText(`${Math.round(val)} dB`, paddingLeft - 8, y);
  }

  // Draw lines & dots
  activeGroups.forEach((group) => {
    const groupMeds = group.medicoes;
    if (!groupMeds.length) return;

    ctx.strokeStyle = group.color;
    ctx.lineWidth = 2;
    ctx.beginPath();

    groupMeds.forEach((med, index) => {
      const x = paddingLeft + (index / Math.max(1, groupMeds.length - 1)) * graphWidth;
      const y = paddingTop + graphHeight - ((Number(med.db) - minDb) / range) * graphHeight;

      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Dots
    ctx.fillStyle = group.color;
    groupMeds.forEach((med, index) => {
      const x = paddingLeft + (index / Math.max(1, groupMeds.length - 1)) * graphWidth;
      const y = paddingTop + graphHeight - ((Number(med.db) - minDb) / range) * graphHeight;
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
    });
  });

  // Draw legend
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  ctx.font = "11px sans-serif";

  let legendX = paddingLeft;
  const legendY = 8;

  activeGroups.forEach((group) => {
    const label = `${group.ambiente_nome} (${group.sensor_id})`;
    const textWidth = ctx.measureText(label).width;

    ctx.fillStyle = group.color;
    ctx.beginPath();
    ctx.arc(legendX + 5, legendY + 6, 4, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#e5e7eb";
    ctx.fillText(label, legendX + 14, legendY);

    legendX += textWidth + 24;
  });
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
  
  // Set sharp resolution
  const width = canvas.clientWidth || canvas.width || 400;
  const height = canvas.clientHeight || canvas.height || 200;
  canvas.width = width;
  canvas.height = height;

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
