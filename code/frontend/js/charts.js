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
  const paddingBottom = 20;

  // Legend layout calculation
  ctx.font = "11px sans-serif";
  let legendLines = 1;
  let currentX = paddingLeft;
  activeGroups.forEach((group) => {
    const label = `${group.ambiente_nome} (${group.sensor_id})`;
    const textWidth = ctx.measureText(label).width;
    if (currentX + textWidth + 24 > width - paddingRight) {
      currentX = paddingLeft;
      legendLines++;
    }
    currentX += textWidth + 24;
  });

  const paddingTop = 15 + legendLines * 18;
  const graphWidth = width - paddingLeft - paddingRight;
  const graphHeight = height - paddingTop - paddingBottom;

  // Background
  ctx.fillStyle = "transparent";
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

    // Area fill
    ctx.lineTo(paddingLeft + graphWidth, paddingTop + graphHeight);
    ctx.lineTo(paddingLeft, paddingTop + graphHeight);
    ctx.closePath();
    ctx.globalAlpha = 0.15;
    ctx.fillStyle = group.color;
    ctx.fill();
    ctx.globalAlpha = 1.0;

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
  let legendY = 8;

  activeGroups.forEach((group) => {
    const label = `${group.ambiente_nome} (${group.sensor_id})`;
    const textWidth = ctx.measureText(label).width;

    if (legendX + textWidth + 24 > width - paddingRight) {
      legendX = paddingLeft;
      legendY += 18;
    }

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
  
  // Set sharp resolution
  const width = canvas.clientWidth || canvas.width || 300;
  const height = canvas.clientHeight || canvas.height || 170;
  canvas.width = width;
  canvas.height = height;

  const paddingLeft = 16;
  const paddingRight = 16;
  const paddingTop = 20;
  // Increase bottom padding to accommodate rotated text
  const paddingBottom = 45; 

  ctx.clearRect(0, 0, width, height);

  // Draw horizontal grid lines
  ctx.strokeStyle = "#1f2937";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#9ca3af";
  ctx.font = "10px Arial";
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";

  const gridLines = 4;
  for (let i = 0; i <= gridLines; i++) {
    const y = paddingTop + (i / gridLines) * (height - paddingTop - paddingBottom);
    const val = 100 - (i / gridLines) * 100;
    
    ctx.beginPath();
    ctx.moveTo(paddingLeft + 20, y);
    ctx.lineTo(width - paddingRight, y);
    ctx.stroke();

    ctx.fillText(`${Math.round(val)}%`, paddingLeft + 15, y);
  }

  const barAreaWidth = width - paddingLeft - paddingRight - 20;
  const startX = paddingLeft + 25;
  
  const gapRatio = 0.4;
  const barWidth = Math.min(35, barAreaWidth / (ambientes.length + (ambientes.length - 1) * gapRatio));
  const gap = barWidth * gapRatio;
  
  const totalBarsWidth = ambientes.length * barWidth + (ambientes.length - 1) * gap;
  const offsetX = startX + Math.max(0, (barAreaWidth - totalBarsWidth) / 2);

  ambientes.forEach((ambiente, index) => {
    const percent = Math.max(
      0,
      Math.min(100, Number(ambiente.percentual_alerta || 0)),
    );
    const barHeight = ((height - paddingTop - paddingBottom) * percent) / 100;
    const x = offsetX + index * (barWidth + gap);
    const y = height - paddingBottom - barHeight;
    
    // Gradient for bar
    const gradient = ctx.createLinearGradient(0, y, 0, y + barHeight);
    gradient.addColorStop(0, "#ff8d8d");
    gradient.addColorStop(1, "#ef4444");

    // Draw Bar
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.moveTo(x, y + barHeight);
    ctx.lineTo(x, y + 2);
    ctx.quadraticCurveTo(x, y, x + 2, y);
    ctx.lineTo(x + barWidth - 2, y);
    ctx.quadraticCurveTo(x + barWidth, y, x + barWidth, y + 2);
    ctx.lineTo(x + barWidth, y + barHeight);
    ctx.closePath();
    ctx.fill();
    
    // Draw Percent on top
    ctx.fillStyle = "#e5e7eb";
    ctx.font = "bold 11px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "bottom";
    ctx.fillText(`${percent.toFixed(0)}%`, x + barWidth / 2, y - 4);
    
    // Draw Label rotated
    ctx.save();
    ctx.translate(x + barWidth / 2, height - paddingBottom + 8);
    ctx.rotate(-Math.PI / 4);
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    ctx.fillStyle = "#a8b2c0";
    ctx.font = "11px Arial";
    
    let label = ambiente.ambiente_nome || ambiente.sensor_id;
    if (label && label.length > 12) {
      label = label.substring(0, 10) + "...";
    }
    
    ctx.fillText(label || "-", 0, 0);
    ctx.restore();
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
