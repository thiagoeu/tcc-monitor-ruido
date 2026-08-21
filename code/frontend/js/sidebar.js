/**
 * sidebar.js — Controle responsivo da sidebar + visibilidade por papel
 * Incluir como <script src="/js/sidebar.js"> no final do body de cada página.
 */

document.addEventListener('DOMContentLoaded', function () {
  var sidebar = document.querySelector('.sidebar');
  var overlay = document.getElementById('sidebar-overlay');
  var menuBtn = document.getElementById('menu-toggle');

  if (!sidebar || !overlay || !menuBtn) {
    console.warn('[sidebar.js] Elementos não encontrados. Sidebar não iniciada.');
    return;
  }

  // ── RBAC: ocultar link Configurações para não-admins ─────────────────────
  (function ocultarConfiguracoesSePreciso() {
    try {
      var raw = localStorage.getItem('noiseradar_user');
      if (!raw) return;
      var user = JSON.parse(raw);
      if (user && user.papel !== "admin" && user.papel !== "admin_master") {
        // Localiza o <li> que contém o link para configuracoes.html
        var links = sidebar.querySelectorAll('.sidebar-link');
        links.forEach(function (link) {
          if (link.getAttribute('href') === '/configuracoes.html') {
            var li = link.closest('li');
            if (li) li.style.display = 'none';
          }
        });
      }
    } catch (_) {
      // JSON inválido no localStorage — ignora silenciosamente
    }
  })();

  // ── Responsive sidebar ────────────────────────────────────────────────────

  function openSidebar() {
    sidebar.classList.add('open');
    overlay.classList.add('visible');
    menuBtn.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    sidebar.classList.remove('open');
    overlay.classList.remove('visible');
    menuBtn.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  }

  // Botão hamburger toggle
  menuBtn.addEventListener('click', function () {
    if (sidebar.classList.contains('open')) {
      closeSidebar();
    } else {
      openSidebar();
    }
  });

  // Fechar ao clicar no overlay
  overlay.addEventListener('click', closeSidebar);

  // Fechar ao clicar em link da sidebar (mobile)
  var links = sidebar.querySelectorAll('.sidebar-link');
  links.forEach(function (link) {
    link.addEventListener('click', function () {
      if (window.innerWidth < 769) closeSidebar();
    });
  });

  // Fechar ao redimensionar para desktop
  window.addEventListener('resize', function () {
    if (window.innerWidth >= 769) closeSidebar();
  });

  // Fechar com Escape
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeSidebar();
  });
});
