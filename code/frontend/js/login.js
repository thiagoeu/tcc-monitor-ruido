// login.js - lógica da página de login
import { login, redirectIfAuthenticated } from "./auth.js";
import { showToast } from "./toast.js";

if (redirectIfAuthenticated()) {
  // já autenticado — a função redirecionou para o dashboard
}

const form = document.getElementById("loginForm");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const email = form.email.value.trim();
  const senha = form.senha.value;

  const button = form.querySelector("button[type=submit]");
  button.disabled = true;
  button.textContent = "Entrando...";

  try {
    await login(email, senha);
    showToast("Login realizado com sucesso.", "success");
    window.location.href = "/";
  } catch (error) {
    if (error instanceof TypeError) {
      showToast("Falha de rede ao contactar o servidor.");
    }
    // erros da API já são exibidos via toast em auth.login()
  } finally {
    button.disabled = false;
    button.textContent = "Entrar";
  }
});