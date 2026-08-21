import { fetchJson } from "./utils.js";
import { authHeaders } from "./auth.js";
import { showToast } from "./toast.js";

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export async function fetchMe() {
  return fetchJson("/api/auth/me");
}

// ---------------------------------------------------------------------------
// Ambientes
// ---------------------------------------------------------------------------

export async function fetchAmbientes() {
  return fetchJson("/api/ambientes");
}

export async function fetchMonitoramento(limit = 80) {
  return fetchJson(`/api/monitoramento?limit=${limit}`);
}

export async function fetchSensoresFisicos(params = {}) {
  const query = new URLSearchParams({
    port: params.port ?? "/dev/ttyAMA0",
    baudrate: String(params.baudrate ?? 9600),
    start_id: String(params.start_id ?? 1),
    end_id: String(params.end_id ?? 32),
    registers: params.registers ?? "0,1",
    function_code: String(params.function_code ?? 3),
    timeout: String(params.timeout ?? 0.25),
  });

  return fetchJson(`/api/sensores/fisicos?${query.toString()}`);
}

export async function fetchRelatorioResumo(hours = 24) {
  return fetchJson(`/api/relatorios/resumo?hours=${hours}`);
}

export async function criarAmbiente(payload) {
  return fetchJson("/api/ambientes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function excluirAmbiente(id) {
  return fetchJson(`/api/ambientes/${id}`, { method: "DELETE" });
}

// Relatórios
async function downloadFile(url, defaultFilename) {
  try {
    const response = await fetch(url, { headers: authHeaders() });
    if (response.status === 401) {
      window.location.href = "/login.html";
      const error = new Error("Sessão expirada. Faça login novamente.");
      showToast(error.message, "warning");
      throw error;
    }
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const error = new Error(body.erro || "Falha ao baixar relatório");
      showToast(error.message);
      throw error;
    }

    // Attempt to extract filename from Content-Disposition header
    let filename = defaultFilename;
    const disposition = response.headers.get("Content-Disposition");
    if (disposition && disposition.indexOf("attachment") !== -1) {
      const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
      const matches = filenameRegex.exec(disposition);
      if (matches != null && matches[1]) { 
        filename = matches[1].replace(/['"]/g, '');
      }
    }

    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(objectUrl);
  } catch (error) {
    if (error.name === "TypeError") {
      showToast("Falha de rede ao contactar o servidor.");
    }
    throw error;
  }
}

export async function downloadRelatorioTxt(hours) {
  return downloadFile(`/api/relatorios/txt?hours=${hours}`, "relatorio_ruido.txt");
}

export async function downloadRelatorioPdf(hours) {
  return downloadFile(`/api/relatorios/pdf?hours=${hours}`, "relatorio_ruido.pdf");
}

export async function downloadRelatorioCsv(hours) {
  return downloadFile(`/api/relatorios/csv?hours=${hours}`, "relatorio_ruido.csv");
}

// ---------------------------------------------------------------------------
// Usuários (admin)
// ---------------------------------------------------------------------------

export async function fetchUsuarios() {
  return fetchJson("/api/usuarios");
}

export async function criarUsuario(payload) {
  return fetchJson("/api/usuarios", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function atualizarUsuario(id, payload) {
  return fetchJson(`/api/usuarios/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function desativarUsuario(id) {
  return fetchJson(`/api/usuarios/${id}`, { method: "DELETE" });
}

export async function alterarSenhaUsuario(id, novaSenha) {
  return fetchJson(`/api/usuarios/${id}/senha`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nova_senha: novaSenha }),
  });
}
