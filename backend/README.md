# Backend — Munka 2.0

API REST em Python com FastAPI, SQLAlchemy (SQLite) e automação via Playwright.

## Arquitetura

```
backend/
├── api.py              # Aplicação FastAPI — todas as rotas HTTP
├── automation.py       # MunkaAutomation — Playwright para o portal Munka
├── gemini_service.py   # Análise de diff com Google Gemini AI
├── gitlab_service.py   # Cliente HTTP para a API REST do GitLab
├── evidence_generator.py  # Geração de HTML de evidência técnica
├── diff_renderer.py    # Renderização de diff em PNG (Playwright headless)
├── database.py         # Engine SQLAlchemy + factory de sessão
├── models.py           # Modelos ORM: Commit, Analise, Historico
├── migrate.py          # Script de migração: arquivos → SQLite
└── Docs/
    ├── CATALOGO_DETALHES_SERVICOS (1).md   # Catálogo de serviços de faturamento
    └── PROMPT_MEDICAO_CATALOGO (1).md      # Regras e prompt para o Gemini
```

## Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/commits` | Lista todos os commits importados |
| `POST` | `/commits/importar` | Importa commit do GitLab (metadados + diff) |
| `GET` | `/commits/{sha}` | Retorna dados de um commit específico |
| `DELETE` | `/commits/{sha}` | Remove commit e sua análise |
| `GET` | `/commits/{sha}/analise` | Retorna análise cached do Gemini |
| `POST` | `/commits/{sha}/analisar` | Dispara análise com Gemini AI |
| `PUT` | `/commits/{sha}/atividades` | Salva edições nas atividades identificadas |
| `POST` | `/commits/{sha}/enviar` | Envia atividade ao portal Munka via Playwright |
| `GET` | `/historico` | Lista atividades enviadas com sucesso |
| `GET` | `/config` | Retorna configuração atual (senhas mascaradas) |
| `POST` | `/config` | Atualiza variáveis de ambiente no `.env` |

Documentação interativa disponível em `http://localhost:8000/docs` (Swagger UI).

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
    importado_em TEXT               -- ISO datetime
);

-- Análises geradas pelo Gemini
CREATE TABLE analises (
    commit_id           TEXT PRIMARY KEY REFERENCES commits(id),
    complexidade_global TEXT,
    atividades_json     TEXT,       -- JSON array de atividades
    analisado_em        TEXT        -- ISO datetime
);

-- Histórico de atividades enviadas ao Munka
CREATE TABLE historico (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    commit_id   TEXT REFERENCES commits(id),
    titulo      TEXT,
    codigo      TEXT,               -- Código do catálogo (ex: 21a)
    hpa         REAL,               -- Horas faturadas
    status      TEXT,
    enviado_em  TEXT                -- ISO datetime
);
```

## Variáveis de Ambiente

| Variável | Uso |
|---|---|
| `GEMINI_API_KEY` | Autenticação na API do Google Gemini |
| `MUNKA_USER` / `MUNKA_PASS` | Login no portal Munka (Playwright) |
| `GITLAB_TOKEN` | PRIVATE-TOKEN para API do GitLab |
| `MUNKA_URL` | URL base do portal Munka |
| `GITLAB_URL` | URL base do GitLab (ex: `https://gitlab.suaorganizacao.com`) |
| `GITLAB_PROJECT` | Projeto padrão (ex: `grupo/projeto`) |
| `DATABASE_URL` | Caminho do SQLite (padrão: `sqlite:///munka.db`, em Docker: `sqlite:////data/munka.db`) |

## Rodar Localmente

```bash
# A partir da raiz do projeto
cd backend
../.venv/bin/uvicorn api:app --reload --port 8000
```

## Migração de Dados

```bash
# A partir da raiz do projeto — lê commits/ e historico.csv automaticamente
cd backend && ../.venv/bin/python3 migrate.py
```
