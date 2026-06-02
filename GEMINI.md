# AGENT.md

Este documento serve como um guia operacional, técnico e arquitetural para agentes de Inteligência Artificial que forem dar manutenção ou adicionar novas funcionalidades neste projeto. Siga rigorosamente estas diretrizes para manter a consistência e a integridade da aplicação.

## 1. Visão Geral do Projeto

* **O que o projeto faz:** Sistema de monitoramento acústico de ambientes que coleta, exibe e gera relatórios de ruídos, alertando caso os níveis ultrapassem os limites pré-definidos para cada ambiente.
* **Objetivo principal:** Rodar de forma autônoma e com baixo custo operacional em um **Raspberry Pi 3 B+**, sendo um projeto de TCC (Trabalho de Conclusão de Curso). Deve ser leve e eficiente (headless execution + web dashboard local).
* **Stack utilizada:**
  * **Backend:** Python 3, Flask (Framework Web) e SQLite (Banco de Dados embutido).
  * **Frontend:** Vanilla HTML, CSS e JavaScript (Sem frameworks complexos, foco em leveza).
* **Tipo de aplicação:** Aplicação Monolítica (O backend serve tanto a API REST quanto os arquivos estáticos do frontend).
* **Principais responsabilidades do sistema:**
  * Registrar e gerenciar ambientes e seus respectivos sensores (IDs e limites de dB).
  * Receber telemetria (mediciões de ruído) em tempo real dos sensores.
  * Avaliar se as medições excedem os limites e gerar alertas de forma síncrona.
  * Fornecer dados estruturados e relatórios para a interface web.

## 2. Arquitetura

* **Estrutura de pastas:**
  * `code/backend/`: Contém todo o código da API Flask.
    * `main.py`: Entrypoint para subir o servidor.
    * `app/__init__.py`: Factory do Flask, configurações e CORS.
    * `app/database.py`: Funções de conexão SQLite, bootstrap de tabelas e seeds.
    * `app/services.py`: Regras de negócio (inserções, relatórios e validações).
    * `app/routes.py`: Controladores REST.
  * `code/frontend/`: Arquivos estáticos (HTML/CSS/JS) servidos pelo Flask.
  * `code/mock/`: Script Python (`sensor.py`) que simula o hardware de sensores enviando dados via HTTP para a API.
  * `code/deploy/`: Arquivos de serviço do `systemd` para executar o sistema no boot do Raspberry Pi.
* **Fluxo de dados:** 
  1. Sensores (ou o Mock) enviam requisições `POST /api/medicoes`.
  2. O backend valida a requisição, verifica o limite do ambiente associado e grava a medição (e alerta, se aplicável) no banco SQLite.
  3. O Frontend faz _polling_ nas rotas `GET /api/monitoramento` e `GET /api/alertas` para atualizar o dashboard.
* **Camadas da aplicação:** Apresentação (Vanilla JS) -> Roteamento (Flask) -> Lógica de Negócios (services.py) -> Persistência de Dados (database.py com SQLite Raw).
* **Padrões arquiteturais:** MVC simplificado (onde as Views são apenas JSON servido para a interface), sem ORM (Raw SQL Querying).
* **Dependências importantes:** Apenas `Flask` e `requests`. (Mantenha o minimalismo, o hardware destino é restrito).
* **Serviços externos:** Nenhum. A aplicação deve funcionar 100% offline em uma rede local (LAN).

## 3. Convenções do Projeto

* **Padrões de nomenclatura:**
  * Python: `snake_case` para variáveis, funções e arquivos. Rotas são prefixadas com `http_` (ex: `http_list_ambientes`).
  * Tabelas e Colunas no DB: Nomenclatura em português usando `snake_case` (ex: `ambientes`, `limite_db`, `excedeu_limite`).
  * API: Respostas JSON também usam `snake_case` em português.
* **Estilo de código:** Código simples, funções curtas e diretas. Retornos de API devem sempre usar as funções utilitárias como `json_error()` definidas no `routes.py`.
* **Organização de componentes:** Evite colocar regras de negócio no `routes.py`. O `routes.py` apenas faz parsing do payload HTTP, chama uma função no `services.py` e formata a resposta/status code.
* **Padrões de API:**
  * Erros retornam JSON no formato `{"erro": "Mensagem descritiva"}`.
  * Sucesso em `POST` deve retornar `201 Created` e o objeto gerado.
  * Códigos comuns: `200` OK, `400` Bad Request (Validação falhou), `404` Not Found, `409` Conflict (Restrição de unicidade).
* **Tipagem:** Python não é fortemente tipado neste projeto, porém a conversão e validação de tipos de dados da requisição (como extrair um integer) usa funções helper como `parse_int()` no `routes.py`.
* **Data e Hora:** Utilize SEMPRE `utc_now_iso()` do `database.py` para gerar timestamps UTC no formato ISO 8601 e salvar como `TEXT` no SQLite.
* **Tratamento de erros:** Serviços disparam exceções (`ValueError`, `RuntimeError`), e a camada de rotas (`routes.py`) usa `try/except` para transformá-las em repostas HTTP amigáveis.

## 4. Regras para Agentes

* **NUNCA alterar a estrutura do banco SQLite sem extrema necessidade.** Se necessário, considere que tabelas são criadas com `IF NOT EXISTS`. Não temos sistema de migração complexo. Alterações destrutivas requerem drop manual.
* **NUNCA criar arquivos duplicados ou espalhar lógica:** Se existe um helper em `services.py`, reutilize-o. Não reinvente funções de persistência, use `database.get_connection()`.
* **NUNCA insira dados concatenando strings no SQLite:** Utilize os parâmetros (`?`) nas queries para evitar SQL Injection. Ex: `execute("SELECT * FROM tb WHERE id = ?", (id,))`.
* **NÃO utilizar bibliotecas pesadas:** Nada de Pandas, SQLAlchemy, React, Vue, etc. O hardware é restrito. Use `sqlite3` built-in e Vanilla JS.
* **NÃO modifique o frontend para adotar build tools:** O frontend (`.html`, `.js`, `.css`) deve continuar podendo ser aberto/servido estaticamente sem precisar de NodeJS, Webpack ou Vite.
* **Sempre manter compatibilidade retroativa** nas rotas da API; os scripts de mock e de frontend dependem delas.
* **Sempre responda CORS adequadamente.** (Já gerenciado no `__init__.py`).

## 5. Fluxo de Desenvolvimento

* **Como instalar dependências:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
* **Como rodar localmente:**
  Em um terminal inicie a API:
  ```bash
  source .venv/bin/activate
  python code/backend/main.py
  ```
  Em outro terminal, simule o hardware gerando ruído falso (Modo Dinâmico - detecta ambientes sozinho):
  ```bash
  source .venv/bin/activate
  python code/mock/sensor.py --api-url http://127.0.0.1:5000/api/medicoes --interval 5 --dynamic
  ```
* **Testes, Lint e Build:** Não há build scripts, linters como `flake8` ou suítes `pytest` configurados no momento. Qualquer alteração deve ser validada manualmente rodando o backend e mock localmente e inspecionando o Dashboard no navegador (http://127.0.0.1:5000).

## 6. Testes

* **Estratégia atual:** Testes E2E Manuais. Como agente, certifique-se de que qualquer nova rota seja testada via `curl` ou requisições semelhantes antes de sugerir que o trabalho está concluído.
* **O que testar:** 
  - Criação de Ambientes (Limites de nomes, conflito de IDs únicos).
  - Inserção de métricas com valores estourando o limite em dB (deve gerar alerta na base).
  - Geração de relatórios (garantir que não ocorra quebra de divisão por zero ou exceções de parsing).

## 7. Banco de Dados

* **ORM:** Nenhum. Uso de SQLite embutido via módulo python nativo `sqlite3`.
* **Migrations:** Não existem. A função `init_db()` em `database.py` cria o esquema.
* **Seed de dados:** Ao iniciar, `seed_default_environments()` insere "Sala Principal" e "Biblioteca" se não existirem.
* **Cuidados:** No SQLite, cursores e conexões não devem ser compartilhados entre threads/requisições. O método `get_connection()` já abre uma nova conexão que deve ser commitada e fechada `connection.close()` no fim da operação. As rotas usam `sqlite3.Row` (via `row_factory`) para facilitar conversão para Dict.

## 8. APIs e Integrações

* **Integrações Externas:** Não faz integrações para a internet. O Dashboard faz requests locais para si mesmo.
* **Autenticação:** Inexistente. Assume-se ambiente confiável de rede local da universidade/laboratório.
* **Rate Limits:** Inexistentes. O gargalo é apenas do banco de dados (lock local).

## 9. Segurança

* **Boas Práticas:**
  * Usar *Parameterized Queries* no SQLite. Este é o ponto MAIS crítico de segurança da aplicação. NUNCA faça `f"SELECT * FROM tbl WHERE id = {var}"`.
* **Sem segredos:** Não há uso de `.env` ou chaves de API secretas atualmente. Configurações estão hardcoded em `app/__init__.py`.

## 10. Checklist Antes de Finalizar Alterações

Se for sugerir ou commitar qualquer alteração, garanta:

* [ ] O código Python não tem erros de sintaxe (execute-o mentalmente ou via terminal se possível).
* [ ] Conexões SQLite estão sendo fechadas adequadamente nas novas funções.
* [ ] Queries usaram `?` e tuples para passagem de parâmetros.
* [ ] Exceções previsíveis foram tratadas e não derrubam o server do Flask.
* [ ] Retornos da API estão formatados como JSON legível e padronizado (`{"erro": ...}`).
* [ ] Se rotas foram criadas/modificadas, os arquivos `index.html` ou `app.js` não quebraram.
* [ ] Não há logs esquecidos de `print("debug aqui")`.

## 11. Anti-patterns do Projeto

* **Problema conhecido:** O Raspberry Pi possui SD Card como armazenamento. Excesso de ESCRITAS pode danificar o cartão. Operações em lote (se um dia implementadas) ou redução de polling desnecessário são encorajadas.
* **Anti-Pattern 1: Complexidade no HTML/JS.** Não introduza React, TypeScript ou minificadores CSS. Este código deve ser auditado facilmente de forma estática por qualquer aluno/professor lendo o HTML puro.
* **Anti-Pattern 2: Consultas SQL dentro de `routes.py`.** A comunicação com DB ocorre exclusivamente no arquivo `services.py`.

## 12. Exemplos de Modificações

### Exemplo: Como ler os dados de forma correta (em `services.py`)

```python
from app.database import get_connection, row_to_dict

def get_ambiente_por_id(ambiente_id):
    conn = get_connection()
    cursor = conn.cursor()
    # ✅ CERTO: Usando parâmetro ?
    cursor.execute("SELECT * FROM ambientes WHERE id = ?", (ambiente_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    return row_to_dict(row)
```

### Exemplo: Como criar uma nova rota de API (em `routes.py`)

```python
from flask import Blueprint, jsonify
from app.services import get_ambiente_por_id

# Supondo uso do main_bp existente
@main_bp.route("/api/ambientes/<int:id>", methods=["GET"])
def http_get_ambiente(id):
    ambiente = get_ambiente_por_id(id)
    if not ambiente:
        return json_error("Ambiente não encontrado", 404)
    return jsonify(ambiente)
```
