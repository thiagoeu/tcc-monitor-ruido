// login.js - lógica da página de login
import { login, redirectIfAuthenticated } from "./auth.js";

if (redirectIfAuthenticated()) {
  // já autenticado — a função redirecionou para o dashboard
}

const form = document.getElementById("loginForm");
const message = document.getElementById("loginMessage");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const email = form.email.value.trim();
  const senha = form.senha.value;

  message.textContent = "";
  message.style.color = "";

  const button = form.querySelector("button[type=submit]");
  button.disabled = true;
  button.textContent = "Entrando...";

  try {
    await login(email, senha);
    window.location.href = "/";
  } catch (error) {
    message.textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = "Entrar";
  }
});