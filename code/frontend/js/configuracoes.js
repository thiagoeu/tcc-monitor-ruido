// configuracoes.js — lógica da página de Configurações (configuracoes.html)
// Responsabilidade: cadastro de ambiente, scan de sensores RS485,
// e preferências do usuário (dark mode, auto-scroll, alertas de áudio).
// Admin: gestão completa de usuários.

import { logout, requireAdmin, getUser } from "./auth.js";
import {
  criarAmbiente,
  fetchSensoresFisicos,
  fetchUsuarios,
  criarUsuario,
  atualizarUsuario,
  desativarUsuario,
  alterarSenhaUsuario,
} from "./api.js";
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

// ============ GERENCIAMENTO DE USUÁRIOS (admin) ============

/**
 * Injeta a seção de usuários no DOM (abaixo do config-grid principal).
 * O HTML é gerado dinamicamente para manter o HTML base simples.
 */
function injetarSecaoUsuarios() {
  const main = document.querySelector("main.page");
  if (!main) return;

  const section = document.createElement("section");
  section.id = "section-usuarios";
  section.className = "section";
  section.setAttribute("aria-labelledby", "sec-usuarios-title");
  section.style.marginTop = "24px";

  section.innerHTML = `
    <div class="section-header">
      <div class="section-title" id="sec-usuarios-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
          <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>
        Gerenciamento de Usuários
        <span style="font-size:.75rem;font-weight:400;color:var(--text-muted);margin-left:8px;">Somente admin</span>
      </div>
    </div>

    <div class="section-body">
      <!-- Formulário de cadastro -->
      <details id="form-novo-usuario" style="margin-bottom:20px;">
        <summary style="cursor:pointer;font-weight:600;color:var(--accent);user-select:none;list-style:none;display:flex;align-items:center;gap:8px;">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          Cadastrar novo usuário
        </summary>
        <form id="formNovoUsuario" style="margin-top:14px;">
          <div class="input-grid" style="margin-bottom:12px;">
            <div class="form-group">
              <label class="form-label" for="nu-nome">Nome</label>
              <input id="nu-nome" name="nome" placeholder="Nome completo" required />
            </div>
            <div class="form-group">
              <label class="form-label" for="nu-email">E-mail</label>
              <input id="nu-email" name="email" type="email" placeholder="usuario@email.com" required />
            </div>
            <div class="form-group">
              <label class="form-label" for="nu-senha">Senha</label>
              <input id="nu-senha" name="senha" type="password" placeholder="Mín. 6 caracteres" required minlength="6" />
            </div>
            <div class="form-group">
              <label class="form-label" for="nu-papel">Papel</label>
              <select id="nu-papel" name="papel">
                <option value="visualizador">Visualizador</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          </div>
          <div style="display:flex;gap:10px;align-items:center;">
            <button type="submit" class="btn-primary" id="btnSalvarNovoUsuario">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              Cadastrar
            </button>
            <span id="msgNovoUsuario" class="small form-message"></span>
          </div>
        </form>
      </details>

      <!-- Tabela de usuários -->
      <div class="table-wrap">
        <table id="tabelaUsuarios">
          <thead>
            <tr>
              <th>#</th>
              <th>Nome</th>
              <th>E-mail</th>
              <th>Papel</th>
              <th>Status</th>
              <th>Criado em</th>
              <th>Último login</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody id="usuariosBody">
            <tr><td colspan="8" class="empty-state">Carregando usuários…</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal de edição inline -->
    <div id="modalEditarUsuario" style="
      display:none;position:fixed;inset:0;z-index:1000;
      background:rgba(0,0,0,.55);backdrop-filter:blur(4px);
      align-items:center;justify-content:center;">
      <div style="
        background:var(--panel);border:1px solid var(--line);border-radius:12px;
        padding:28px 32px;width:min(440px,90vw);box-shadow:0 24px 64px rgba(0,0,0,.4);">
        <h2 style="margin:0 0 20px;font-size:1.05rem;">Editar Usuário</h2>
        <form id="formEditarUsuario">
          <input type="hidden" id="edit-id" />
          <div class="form-group" style="margin-bottom:12px;">
            <label class="form-label" for="edit-nome">Nome</label>
            <input id="edit-nome" placeholder="Nome completo" required />
          </div>
          <div class="form-group" style="margin-bottom:12px;">
            <label class="form-label" for="edit-email">E-mail</label>
            <input id="edit-email" type="email" required />
          </div>
          <div class="form-group" style="margin-bottom:12px;">
            <label class="form-label" for="edit-papel">Papel</label>
            <select id="edit-papel">
              <option value="visualizador">Visualizador</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div class="form-group" style="margin-bottom:20px;">
            <label class="form-label" for="edit-nova-senha">Nova senha <span style="font-weight:400;color:var(--text-muted)">(deixe vazio para não alterar)</span></label>
            <input id="edit-nova-senha" type="password" placeholder="Mín. 6 caracteres" minlength="6" />
          </div>
          <div style="display:flex;gap:10px;justify-content:flex-end;">
            <button type="button" class="btn-secondary" id="btnCancelarEdicao">Cancelar</button>
            <button type="submit" class="btn-primary" id="btnSalvarEdicao">Salvar alterações</button>
          </div>
          <p id="msgEditarUsuario" class="small form-message" style="margin-top:10px;text-align:center;"></p>
        </form>
      </div>
    </div>
  `;

  // Insere a seção no final do main, antes do footer
  const footer = main.querySelector(".page-footer") || main.querySelector("footer");
  if (footer) {
    main.insertBefore(section, footer);
  } else {
    main.appendChild(section);
  }
}

function formatarData(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("pt-BR", {
      day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function renderTabelaUsuarios(usuarios) {
  const tbody = document.getElementById("usuariosBody");
  if (!tbody) return;

  const meuPapel = getUser()?.papel ?? "visualizador";
  const isMaster = meuPapel === "admin_master";

  if (!usuarios.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="empty-state">Nenhum usuário cadastrado.</td></tr>';
    return;
  }

  tbody.innerHTML = usuarios.map((u) => {
    const ativo = u.ativo
      ? '<span class="tag-ok">Ativo</span>'
      : '<span class="tag-warn">Inativo</span>';

    const papel = u.papel === "admin_master"
      ? '<span class="tag-ok" style="background:rgba(var(--accent-rgb,99,179,237),.15);color:var(--accent)">admin_master</span>'
      : u.papel === "admin"
        ? '<span class="tag-ok" style="background:rgba(var(--accent-rgb,99,179,237),.15);color:var(--accent)">admin</span>'
        : '<span class="tag-muted">visualizador</span>';

    // admin_master (id=1): nenhum botão
    // admin (non-master) sendo editado por admin: nenhum botão
    // visualizador sendo gerenciado por qualquer admin: mostra botões
    const isAdminLevel = u.papel === "admin" || u.papel === "admin_master";
    const podeGerenciar = u.id !== 1 && (isMaster || !isAdminLevel);

    const acoes = !podeGerenciar
      ? '<span style="color:var(--text-muted);font-size:.78rem;">—</span>'
      : `
      <div style="display:flex;gap:6px;flex-wrap:wrap;">
        <button type="button" class="btn-ghost" style="font-size:.78rem;padding:4px 10px;"
          data-editar-id="${u.id}"
          data-editar-nome="${escHtml(u.nome)}"
          data-editar-email="${escHtml(u.email)}"
          data-editar-papel="${u.papel}">
          ✏️ Editar
        </button>
        ${u.ativo ? `
        <button type="button" class="btn-danger" style="font-size:.78rem;padding:4px 10px;"
          data-desativar-id="${u.id}"
          data-desativar-nome="${escHtml(u.nome)}">
          🚫 Desativar
        </button>` : ""}
      </div>`;


    return `
      <tr>
        <td>${u.id}</td>
        <td>${escHtml(u.nome)}</td>
        <td>${escHtml(u.email)}</td>
        <td>${papel}</td>
        <td>${ativo}</td>
        <td style="white-space:nowrap;">${formatarData(u.created_at)}</td>
        <td style="white-space:nowrap;">${formatarData(u.last_login_at)}</td>
        <td>${acoes}</td>
      </tr>`;
  }).join("");

  // Vincular botões de editar
  tbody.querySelectorAll("[data-editar-id]").forEach((btn) => {
    btn.addEventListener("click", () => abrirModalEdicao({
      id: Number(btn.dataset.editarId),
      nome: btn.dataset.editarNome,
      email: btn.dataset.editarEmail,
      papel: btn.dataset.editarPapel,
    }));
  });

  // Vincular botões de desativar
  tbody.querySelectorAll("[data-desativar-id]").forEach((btn) => {
    btn.addEventListener("click", () => confirmarDesativar(
      Number(btn.dataset.desativarId),
      btn.dataset.desativarNome,
    ));
  });
}

function escHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function carregarUsuarios() {
  try {
    const usuarios = await fetchUsuarios();
    renderTabelaUsuarios(usuarios);
  } catch (err) {
    const tbody = document.getElementById("usuariosBody");
    if (tbody) tbody.innerHTML = `<tr><td colspan="8" class="empty-state">Erro ao carregar: ${escHtml(err.message)}</td></tr>`;
  }
}

function abrirModalEdicao(usuario) {
  document.getElementById("edit-id").value = usuario.id;
  document.getElementById("edit-nome").value = usuario.nome;
  document.getElementById("edit-email").value = usuario.email;
  document.getElementById("edit-papel").value = usuario.papel;
  document.getElementById("edit-nova-senha").value = "";
  document.getElementById("msgEditarUsuario").textContent = "";

  const modal = document.getElementById("modalEditarUsuario");
  modal.style.display = "flex";
}

function fecharModalEdicao() {
  document.getElementById("modalEditarUsuario").style.display = "none";
}

async function confirmarDesativar(id, nome) {
  if (!confirm(`Desativar o usuário "${nome}"? O usuário não conseguirá mais fazer login.`)) return;

  try {
    await desativarUsuario(id);
    showToast(`Usuário "${nome}" desativado.`, "success");
    carregarUsuarios();
  } catch (err) {
    showToast(err.message, "error");
  }
}

function initUsuariosSection() {
  injetarSecaoUsuarios();

  // Ocultar opção "Admin" no select de cadastro se o usuário não for admin_master
  const meuPapel = getUser()?.papel ?? "visualizador";
  if (meuPapel !== "admin_master") {
    const optAdmin = document.querySelector("#nu-papel option[value='admin']");
    if (optAdmin) optAdmin.remove();
  }

  // Formulário de novo usuário
  document.getElementById("formNovoUsuario")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("btnSalvarNovoUsuario");
    const msg = document.getElementById("msgNovoUsuario");
    btn.disabled = true;
    msg.textContent = "Cadastrando...";
    msg.style.color = "var(--text-muted)";

    const payload = {
      nome: document.getElementById("nu-nome").value.trim(),
      email: document.getElementById("nu-email").value.trim(),
      senha: document.getElementById("nu-senha").value,
      papel: document.getElementById("nu-papel").value,
    };

    try {
      await criarUsuario(payload);
      e.target.reset();
      msg.textContent = "✓ Usuário cadastrado!";
      msg.style.color = "var(--accent)";
      showToast("Usuário cadastrado.", "success");
      setTimeout(() => { msg.textContent = ""; }, 4000);
      carregarUsuarios();
      document.getElementById("form-novo-usuario").removeAttribute("open");
    } catch (err) {
      msg.textContent = err.message;
      msg.style.color = "var(--danger)";
    } finally {
      btn.disabled = false;
    }
  });

  // Modal de edição
  document.getElementById("btnCancelarEdicao")?.addEventListener("click", fecharModalEdicao);

  document.getElementById("modalEditarUsuario")?.addEventListener("click", (e) => {
    if (e.target === e.currentTarget) fecharModalEdicao();
  });

  document.getElementById("formEditarUsuario")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("btnSalvarEdicao");
    const msg = document.getElementById("msgEditarUsuario");
    btn.disabled = true;
    msg.textContent = "Salvando...";
    msg.style.color = "var(--text-muted)";

    const id = Number(document.getElementById("edit-id").value);
    const payload = {
      nome: document.getElementById("edit-nome").value.trim(),
      email: document.getElementById("edit-email").value.trim(),
      papel: document.getElementById("edit-papel").value,
    };

    const novaSenha = document.getElementById("edit-nova-senha").value.trim();

    try {
      await atualizarUsuario(id, payload);

      if (novaSenha) {
        await alterarSenhaUsuario(id, novaSenha);
      }

      msg.textContent = "✓ Usuário atualizado!";
      msg.style.color = "var(--accent)";
      showToast("Usuário atualizado.", "success");
      setTimeout(() => { fecharModalEdicao(); }, 1200);
      carregarUsuarios();
    } catch (err) {
      msg.textContent = err.message;
      msg.style.color = "var(--danger)";
    } finally {
      btn.disabled = false;
    }
  });

  carregarUsuarios();
}

// ============ BOOTSTRAP ============

async function bootstrap() {
  // Guard: valida role server-side. Redireciona visualizador para "/".
  const isAdmin = await requireAdmin();
  if (!isAdmin) return;

  initDarkMode();
  initPrefsControls();
  initAmbienteForm();
  initScanControls();
  initUsuariosSection();

  document.getElementById("logoutBtn")?.addEventListener("click", () => logout());
}

bootstrap();

