# Backend — Munka 2.0

API REST em Python com FastAPI, SQLAlchemy (SQLite), automação de portal via Playwright, processamento de tarefas assíncronas com Celery + Redis, e análise inteligente de diffs via Google Gemini AI.

## Arquitetura

```
backend/
├── api.py                  # Aplicação FastAPI — todas as rotas HTTP e endpoints REST
├── automation.py           # MunkaAutomation — Playwright headless/headed para o portal Munka
├── celery_app.py           # Configuração da aplicação Celery e roteamento de filas
├── celery_tasks.py         # Tarefas assíncronas Celery (análise Gemini e envio Playwright)
├── concurrency.py          # Cálculo dinâmico de concorrência por CPU para trabalhadores Celery
├── model_rate_limiter.py   # Gerenciador de Rate Limit (RPM/TPM/RPD) dos modelos Gemini (Redis + Memory fallback)
├── gemini_service.py       # Análise de diffs git com Google Gemini AI e modelos configuráveis
├── gitlab_service.py       # Cliente HTTP para integração com a API REST do GitLab
├── evidence_generator.py   # Geração de relatórios HTML de evidência técnica
├── diff_renderer.py        # Renderização de diffs unificados em imagem PNG (Playwright headless)
├── database.py             # Engine SQLAlchemy e factory de sessão com SQLite
├── models.py               # Modelos ORM: Commit, Analise, Historico, Fila
├── migrate.py              # Script de migração de arquivos legados (JSON/CSV → SQLite)
└── Docs/
    ├── CATALOGO_DETALHES_SERVICOS (1).md   # Catálogo oficial de serviços e atividades de faturamento
    └── PROMPT_MEDICAO_CATALOGO (1).md      # Regras, diretrizes de medição e prompt do Gemini AI
```

## Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/commits` | Lista todos os commits importados com suporte a busca |
| `POST` | `/commits/importar` | Importa commit do GitLab (metadados + diff) |
| `GET` | `/commits/{sha}` | Retorna metadados e diff bruto de um commit específico |
| `PATCH` | `/commits/{sha}` | Atualiza metadados editáveis de um commit |
| `DELETE` | `/commits/{sha}` | Remove o commit, sua análise e histórico associado |
| `GET` | `/commits/{sha}/analise` | Retorna a análise cached gerada pelo Gemini |
| `POST` | `/commits/{sha}/analisar` | Executa/dispara análise síncrona com Gemini AI |
| `PUT` | `/commits/{sha}/atividades` | Atualiza as atividades identificadas no JSON da análise |
| `POST` | `/commits/{sha}/preview-evidencia` | Gera visualização HTML da evidência técnica da atividade |
| `POST` | `/commits/{sha}/enviar` | Envia atividade ao portal Munka via Playwright (síncrono) |
| `GET` | `/commits/{sha}/enviar-stream` | Envia atividade ao Munka com progresso em tempo real (SSE) |
| `GET` | `/task/{task_id}` | Consulta status e metadados de uma tarefa Celery em execução |
| `GET` | `/historico` | Lista atividades enviadas e homologadas no Munka |
| `DELETE` | `/historico/{item_id}` | Remove uma atividade do histórico |
| `GET` | `/projeto/atualizacao` | Verifica se o repositório possui commits pendentes via Git |
| `GET` | `/config` | Retorna configurações do sistema (senhas mascaradas) |
| `POST` | `/config` | Salva e atualiza variáveis de ambiente no arquivo `.env` |
| `POST` | `/fila/analise` | Enfileira análise de commit na fila assíncrona do Celery |
| `POST` | `/fila/envio` | Enfileira envio de atividade ao Munka na fila assíncrona do Celery |
| `GET` | `/fila` | Lista todos os jobs na fila de processamento (pendentes, rodando, concluídos, erro) |
| `DELETE` | `/fila/{job_id}` | Cancela ou remove um job da fila |
| `GET` | `/modelos/limits` | Retorna o consumo e status de Rate Limit de todos os modelos Gemini |
| `PUT` | `/modelos/limits/{model_id}` | Atualiza limites operacionais de um modelo (RPM, TPM, RPD) |
| `POST` | `/modelos/test-call` | Executa chamada de teste no modelo especificado para validação |
| `POST` | `/modelos/reset` | Reseta métricas e contadores de uso de Rate Limit |

Documentação interativa Swagger UI disponível em `http://localhost:8000/docs`.

## Schema do Banco SQLite

```sql
-- Commits importados do GitLab
CREATE TABLE commits (
    id          TEXT PRIMARY KEY,   -- SHA completo (40 chars)
    data        TEXT,               -- DD/MM/YYYY
    projeto     TEXT,               -- Ex: grupo/projeto
    autor       TEXT,
    mensagem    TEXT,
    diff_raw    TEXT,               -- Conteúdo completo do diff
    importado_em TEXT               -- Timestamp ISO
);

-- Análises geradas pelo Gemini
CREATE TABLE analises (
    commit_id           TEXT PRIMARY KEY REFERENCES commits(id),
    complexidade_global TEXT,
    atividades_json     TEXT,       -- JSON array de atividades
    analisado_em        TEXT        -- Timestamp ISO
);

-- Histórico de atividades enviadas ao Munka
CREATE TABLE historico (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    commit_id   TEXT REFERENCES commits(id),
    titulo      TEXT,
    codigo      TEXT,               -- Código do catálogo (ex: 21a)
    hpa         REAL,               -- Horas faturadas
    status      TEXT,               -- Status (ex: Enviado ao Munka)
    enviado_em  TEXT                -- Timestamp ISO
);

-- Fila de tarefas assíncronas (Celery / Redis)
CREATE TABLE fila (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo          TEXT,             -- 'analise' ou 'envio'
    commit_id     TEXT REFERENCES commits(id),
    atividade_idx INTEGER,          -- Índice da atividade (para envios)
    modelo        TEXT,             -- Modelo Gemini selecionado
    status        TEXT,             -- 'pending', 'running', 'done', 'error'
    task_id       TEXT,             -- Celery Task ID
    resultado     TEXT,             -- JSON de retorno ou logs de execução
    criado_em     TEXT,             -- Timestamp ISO
    concluido_em  TEXT              -- Timestamp ISO
);
```

## Sistema de Filas e Concorrência Dinâmica

O sistema conta com filas assíncronas dedicadas impulsionadas por Celery + Redis:
- **`analises`**: Fila para processar requisições à API do Gemini AI.
- **`envios`**: Fila para execução dos scripts Playwright de automação do portal.

A concorrência de workers é calculada automaticamente baseada na CPU da máquina host (`concurrency.py`):
$$\text{Total} = \max(4, \lfloor \text{CPU\_CORES} \times 0.70 \rfloor)$$
- A fila `analises` recebe $\lceil \text{Total} / 2 \rceil$ workers.
- A fila `envios` recebe $\lfloor \text{Total} / 2 \rfloor$ workers.

## Monitoramento de Rate Limit do Gemini AI

O módulo `model_rate_limiter.py` realiza a gestão e o rastreamento em tempo real do uso da API do Gemini AI para evitar erros de cota (HTTP 429/503):
- Monitora métricas de **RPM** (Requests Per Minute), **TPM** (Tokens Per Minute) e **RPD** (Requests Per Day).
- Backend primário via **Redis** com fallback automático em **memória**.
- Níveis de alerta visual baseados na utilização mais alta (`ok` < 60%, `warning` 60-85%, `danger` > 85%).
- Suporte a retries inteligentes com backoff no Celery em caso de exaustão de cota.

## Variáveis de Ambiente

| Variável | Uso | Padrão |
|---|---|---|
| `GEMINI_API_KEY` | Chave de autenticação da API Google Gemini AI | - |
| `MUNKA_USER` / `MUNKA_PASS` | Credenciais de login no portal Munka | - |
| `GITLAB_TOKEN` | PRIVATE-TOKEN da API do GitLab | - |
| `MUNKA_URL` | URL base do portal Munka | - |
| `GITLAB_URL` | URL base da instância GitLab | - |
| `GITLAB_PROJECT` | Projeto padrão do GitLab | - |
| `DATABASE_URL` | String de conexão SQLAlchemy | `sqlite:///munka.db` |
| `CELERY_BROKER_URL` | URL do Redis broker do Celery | `redis://redis:6379/0` |
| `CELERY_RESULT_BACKEND` | URL do Redis result backend do Celery | `redis://redis:6379/0` |
| `REDIS_URL` | Conexão Redis para o Rate Limiter | `redis://redis:6379/0` |
| `MUNKA_PROJETO` / `MUNKA_PRODUTO` | Projeto e Produto padrão no portal Munka | - |
| `MUNKA_CARGO` / `MUNKA_NIVEL` | Cargo e Nível do desenvolvedor no Munka | - |
| `MUNKA_RESPONSAVEL` | Nome do responsável no Munka | - |
| `MUNKA_STATUS_ID` | Status ID padrão para novos envios | `17` |
| `MUNKA_DATA_INICIO` / `MUNKA_DATA_FIM` | Horários padrão de execução de atividades | `08:00` / `18:00` |

## Rodar Localmente

```bash
# Navegar até a pasta backend
cd backend

# Subir a API FastAPI
../.venv/bin/uvicorn api:app --reload --port 8000

# Subir o Worker Celery (opcional, para processamento assíncrono em fila)
../.venv/bin/celery -A celery_app worker --loglevel=info
```

## Migração de Dados Legados

```bash
# Executa migração dos arquivos JSON/CSV históricos para a base SQLite
cd backend && ../.venv/bin/python3 migrate.py
```
