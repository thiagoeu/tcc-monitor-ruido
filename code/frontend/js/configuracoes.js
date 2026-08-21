// configuracoes.js — lógica da página de Configurações (configuracoes.html)
// Responsabilidade: cadastro de ambiente, scan de sensores RS485,
// e preferências do usuário (dark mode, auto-scroll, alertas de áudio).

import { logout, requireAuth } from "./auth.js";
import { criarAmbiente, fetchSensoresFisicos } from "./api.js";
import { initDarkMode, setTheme, getTheme } from "./utils.js";
import { showToast } from "./toast.js";

// ============ KEYS DE PREFERÊNCIAS ============

const PREFS_KEY = "nr_prefs";

const DEFAULT_PREFS = {
  darkMode: true,
  autoScroll: true,
  audioAlerts: false,
};

function loadPrefs() {
  try {
    const saved = localStorage.getItem(PREFS_KEY);
    return saved ? { ...DEFAULT_PREFS, ...JSON.parse(saved) } : { ...DEFAULT_PREFS };
  } catch {
    return { ...DEFAULT_PREFS };
  }
}

function savePrefs(prefs) {
  localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
}

// ============ PREFERÊNCIAS — UI ============

function applyPrefsToUI(prefs) {
  const darkEl = document.getElementById("pref-dark-mode");
  const scrollEl = document.getElementById("pref-autoscroll");
  const audioEl = document.getElementById("pref-audio");

  if (darkEl) darkEl.checked = prefs.darkMode;
  if (scrollEl) scrollEl.checked = prefs.autoScroll;
  if (audioEl) audioEl.checked = prefs.audioAlerts;
}

function initPrefsControls() {
  const prefs = loadPrefs();
  applyPrefsToUI(prefs);

  // Sincroniza o toggle de dark mode do topbar com a preferência
  const darkEl = document.getElementById("pref-dark-mode");
  if (darkEl) {
    darkEl.checked = getTheme() === "dark";
    darkEl.addEventListener("change", () => {
      setTheme(darkEl.checked ? "dark" : "light");
    });
  }

  // Salvar preferências
  document.getElementById("savePrefsBtn")?.addEventListener("click", () => {
    const newPrefs = {
      darkMode: document.getElementById("pref-dark-mode")?.checked ?? true,
      autoScroll: document.getElementById("pref-autoscroll")?.checked ?? true,
      audioAlerts: document.getElementById("pref-audio")?.checked ?? false,
    };
    savePrefs(newPrefs);
    setTheme(newPrefs.darkMode ? "dark" : "light");
    const msg = document.getElementById("prefsMessage");
    if (msg) {
      msg.textContent = "Preferências salvas com sucesso!";
      msg.style.color = "var(--accent)";
      setTimeout(() => { msg.textContent = ""; }, 3000);
    }
    showToast("Preferências salvas.", "success");
  });

  // Restaurar padrões
  document.getElementById("resetPrefsBtn")?.addEventListener("click", () => {
    savePrefs({ ...DEFAULT_PREFS });
    applyPrefsToUI({ ...DEFAULT_PREFS });
    setTheme("dark");
    const msg = document.getElementById("prefsMessage");
    if (msg) {
      msg.textContent = "Padrões restaurados.";
      msg.style.color = "var(--text-muted)";
      setTimeout(() => { msg.textContent = ""; }, 3000);
    }
  });
}

// ============ CADASTRO DE AMBIENTE ============

function initAmbienteForm() {
  const form = document.getElementById("ambienteForm");
  const msg = document.getElementById("formMessage");
  const btn = document.getElementById("submitAmbienteBtn");

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    btn.disabled = true;
    if (msg) { msg.textContent = "Salvando..."; msg.style.color = "var(--text-muted)"; }

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
      if (msg) { msg.textContent = "✓ Ambiente cadastrado com sucesso!"; msg.style.color = "var(--accent)"; }
      showToast("Ambiente cadastrado.", "success");
      setTimeout(() => { if (msg) msg.textContent = ""; }, 4000);
    } catch (err) {
      if (msg) { msg.textContent = err.message; msg.style.color = "var(--danger)"; }
    } finally {
      btn.disabled = false;
    }
  });
}

// ============ SCAN DE SENSORES FÍSICOS ============

function getScanParams() {
  return {
    port: document.getElementById("scanPort")?.value?.trim() || "/dev/ttyUSB0",
    baudrate: Number(document.getElementById("scanBaudrate")?.value || 9600),
    start_id: Number(document.getElementById("scanStartId")?.value || 1),
    end_id: Number(document.getElementById("scanEndId")?.value || 10),
    registers: document.getElementById("scanRegisters")?.value?.trim() || "0,1",
    function_code: Number(document.getElementById("scanFunctionCode")?.value || 3),
  };
}

function renderSensoresFisicos(result) {
  const tbody = document.getElementById("sensoresBody");
  const resumo = document.getElementById("sensoresResumo");
  const portasResumo = document.getElementById("portasResumo");

  const sensores = result?.sensores || [];
  const portas = result?.portas_detectadas || [];

  resumo.textContent =
    `Varredura em ${result.porta} (${result.baudrate} baud): ` +
    `${result.total_encontrados} sensor(es) físico(s) encontrado(s).`;

  if (!sensores.length) {
    tbody.innerHTML =
      '<tr><td colspan="4" class="empty-state">Nenhum ID Modbus respondeu nesta varredura.</td></tr>';
  } else {
    tbody.innerHTML = sensores
      .map(
        (s) => `
        <tr>
          <td><strong>${s.id_modbus}</strong></td>
          <td>${s.register}</td>
          <td>${s.raw_value}</td>
          <td>
            <button type="button" class="btn-ghost" style="font-size:.8rem;padding:5px 10px;"
              data-fill-sensor-id="${s.id_modbus}">
              Usar como Sensor ID
            </button>
          </td>
        </tr>`,
      )
      .join("");

    // Handler para preencher o campo sensor_id do formulário de ambiente
    document.querySelectorAll("[data-fill-sensor-id]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-fill-sensor-id") || "";
        const field = document.getElementById("campo-sensor-id");
        if (field) {
          field.value = id;
          field.focus();
          const msg = document.getElementById("formMessage");
          if (msg) {
            msg.textContent = `Sensor ID preenchido com '${id}'.`;
            msg.style.color = "var(--accent)";
          }
        }
      });
    });
  }

  portasResumo.textContent = portas.length
    ? `Portas detectadas: ${portas.map((p) => p.device).join(", ")}`
    : "Portas detectadas: nenhuma.";
}

function initScanControls() {
  const btn = document.getElementById("scanSensoresBtn");
  const resumo = document.getElementById("sensoresResumo");

  btn?.addEventListener("click", async () => {
    btn.disabled = true;
    resumo.textContent = "Escaneando sensores na porta serial...";

    try {
      const result = await fetchSensoresFisicos(getScanParams());
      renderSensoresFisicos(result);
    } catch {
      document.getElementById("sensoresBody").innerHTML =
        '<tr><td colspan="4" class="empty-state">Falha ao escanear. Verifique a conexão serial.</td></tr>';
      document.getElementById("portasResumo").textContent = "";
      resumo.textContent = "Não foi possível ler os sensores físicos.";
    } finally {
      btn.disabled = false;
    }
  });
}

// ============ BOOTSTRAP ============

function bootstrap() {
  if (!requireAuth()) return;
  initDarkMode();
  initPrefsControls();
  initAmbienteForm();
  initScanControls();
  document.getElementById("logoutBtn")?.addEventListener("click", () => logout());
}

bootstrap();
