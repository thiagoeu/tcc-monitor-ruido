export function getColor(db) {
  if (db < 50) {
    return "#00E676";
  }

  if (db < 75) {
    return "#FFD600";
  }

  return "#FF5252";
}

export function getNoiseLabel(db) {
  if (db < 40) {
    return "Silencioso";
  }

  if (db < 60) {
    return "Moderado";
  }

  if (db < 80) {
    return "Alto";
  }

  return "Perigoso";
}

export function getWidth(db) {
  return `${Math.min((db / 120) * 100, 100)}%`;
}
