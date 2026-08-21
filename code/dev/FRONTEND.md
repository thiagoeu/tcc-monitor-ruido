# Frontend — NoiseRadar

Documentação técnica do frontend web do projeto NoiseRadar.

## Estrutura de Arquivos

```
code/frontend/
├── index.html              # Dashboard (tempo real)
├── graficos.html           # Gráficos por ambiente
├── logs.html               # Medições, alertas e exportação
├── configuracoes.html      # Cadastro de ambiente, scan RS485, preferências
├── login.html              # Tela de autenticação
├── asserts/
│   └── logo_do_tcc_transparente.png
├── css/
│   ├── style.css           # Hub centralizador (usando @import)
│   ├── variables.css       # Tokens de cor (dark/light)
│   ├── reset.css           # Reset básico de estilos
│   ├── utilities.css       # Classes utilitárias gerais
│   ├── components/         # Módulos de componentes reutilizáveis
│   └── pages/              # Estilos específicos de cada página
└── js/
    ├── api.js              # Chamadas ao backend (fetch helpers)
    ├── auth.js             # Autenticação (token JWT em localStorage)
    ├── charts.js           # Lógica dos gráficos (Chart.js)
    ├── dashboard.js        # Lógica do Dashboard
    ├── graficos.js         # Lógica da página de Gráficos
    ├── logs.js             # Lógica da página de Logs
    ├── configuracoes.js    # Lógica da página de Configurações
    ├── login.js            # Lógica da tela de Login
    ├── toast.js            # Sistema de notificações toast
    └── utils.js            # Utilitários: formatação, fetchJson, dark mode
```

## Mapa de Páginas

| Página | Arquivo HTML | Arquivo JS | Responsabilidade |
|---|---|---|---|
| Dashboard | `index.html` | `dashboard.js` | Cards de ambientes em tempo real, mini-gráficos de tendência e % de alertas |
| Gráficos | `graficos.html` | `graficos.js` | Gráficos detalhados por ambiente com stats (última, média, min/max, alertas) |
| Logs | `logs.html` | `logs.js` | Tabela de medições recentes (filtrável) e tabela de alertas |
| Relatórios | `relatorios.html` | `relatorios.js` | Resumo estatístico, cálculo de $L_{eq}$ e exportação em PDF, CSV e TXT |
| Configurações | `configuracoes.html` | `configuracoes.js` | Cadastro de ambiente, scan de sensores RS485 e preferências do usuário |
| Login | `login.html` | `login.js` | Autenticação por e-mail + senha |

## Sistema de Temas (Dark / Light Mode)

O tema é controlado por:

- **CSS Custom Properties** em `:root` (dark) e `:root[data-theme="light"]` (light)
- **`localStorage`** com chave `nr_theme` — persiste entre páginas e reloads
- **`initDarkMode()`** em `utils.js` — inicializa o tema em todas as páginas; lê a preferência salva e, se não houver, usa `prefers-color-scheme` do sistema

```js
// Como aplicar em uma nova página
import { initDarkMode } from "./utils.js";
// No bootstrap() da página:
initDarkMode();
```

- O botão toggle tem o ID `themeToggle` (elemento `.toggle-track`).
- A função `setTheme(theme)` de `utils.js` permite alterar o tema programaticamente (usada pela página de Configurações).

## Design System

O projeto usa uma arquitetura CSS modular importada no `css/style.css`. Os estilos são separados por responsabilidades (`variables.css`, `reset.css`, `components/`, e `pages/`). Não use estilos inline desnecessários.

### Variáveis principais

| Variável | Uso |
|---|---|
| `--bg` | Fundo da página |
| `--panel` | Fundo de cards e seções |
| `--line` | Bordas e divisores |
| `--text` | Texto principal |
| `--text-secondary` | Texto secundário/labels |
| `--text-muted` | Texto desabilitado/placeholder |
| `--accent` | Verde de destaque (alertas OK, botões primários) |
| `--danger` | Vermelho de alerta |
| `--warn` | Laranja de aviso |

### Componentes CSS disponíveis

- `.section` + `.section-header` + `.section-body` — seção com cabeçalho
- `.card` — card com borda e hover
- `.metric` — card de métrica (label + valor grande)
- `.metric-grid` — grid responsiva de métricas
- `.pref-item` + `.switch` — item de preferência com toggle
- `.filter-bar` — barra de filtros horizontal
- `.table-wrap` — tabela com scroll horizontal
- `.btn-primary`, `.btn-secondary`, `.btn-danger`, `.btn-ghost` — botões
- `.tag-ok`, `.tag-warn`, `.tag-muted` — badges de status
- `.page-header` — header da página com `h1` + descrição
- `.topbar` — barra superior fixa com título e ações
- `.sidebar` — navegação lateral fixa

## Autenticação

O token JWT é salvo em `localStorage` com a chave `noiseradar_token` e o objeto do usuário logado na chave `noiseradar_user`.

Toda página protegida inclui no `<head>`:

```html
<script>
  if (!localStorage.getItem("noiseradar_token")) {
    window.location.replace("/login.html");
  }
</script>
```

E no JS da página:

```js
import { requireAuth, logout } from "./auth.js";
// No bootstrap():
if (!await requireAuth()) return;
```

Para páginas restritas a administradores (ex: `configuracoes.html`), usamos:

```js
import { requireAdmin } from "./auth.js";
if (!await requireAdmin()) return;
```

O `requireAdmin` e a API validam os papéis `admin` e `admin_master`.

## Convenções

- **IDs únicos por página:** Cada elemento interativo tem um ID único e descritivo (ex: `campo-sensor-id`, `scanSensoresBtn`).
- **ES Modules:** Todos os scripts são `type="module"`. Não usar scripts globais.
- **Sem jQuery / sem frameworks:** Vanilla JS + Fetch API + CSS nativo.
- **Auto-refresh:** Dashboard: 5s. Logs: 10s. Gráficos: 10s. Configurações: sem auto-refresh.
- **`localStorage` keys usadas:**

| Chave | Tipo | Conteúdo |
|---|---|---|
| `noiseradar_token` | string | JWT de autenticação |
| `noiseradar_user` | JSON | Dados do usuário logado (nome, email, papel) |
| `nr_theme` | string | `"dark"` ou `"light"` |
| `nr_prefs` | JSON | Objeto de preferências do usuário |
