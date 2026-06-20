# Munka 2.0

Ferramenta de automação de faturamento de entregas técnicas de software para o portal Munka (Saúde-GO). Importa commits do GitLab, analisa os diffs com Google Gemini AI e automatiza o cadastro e homologação de atividades no portal de faturamento.

## Visão geral do fluxo

```
GitLab → diff do commit
    ↓
Google Gemini AI → identifica atividades, códigos e HPA do catálogo
    ↓
Usuário revisa e edita as atividades no frontend Vue
    ↓
Playwright → automatiza o cadastro + evidência + homologação no portal Munka
```

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/)
- Arquivo `.env` configurado (ver seção abaixo)

## Quick Start (Docker)

```bash
# 1. Clone o repositório
git clone <url-do-repositório> && cd munka

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# 3. Suba tudo com um comando
docker-compose up --build

# Acesse:
# Frontend:  http://localhost
# Backend:   http://localhost:8000
# Swagger:   http://localhost:8000/docs
```

## Variáveis de Ambiente (`.env`)

| Variável | Descrição | Exemplo |
|---|---|---|
| `GEMINI_API_KEY` | Chave da API do Google Gemini (aistudio.google.com) | `AIza...` |
| `MUNKA_URL` | URL base do portal Munka | `https://munka.suaorganizacao.com` |
| `MUNKA_USER` | Usuário de login no portal Munka | `joao.silva` |
| `MUNKA_PASS` | Senha do portal Munka | `minhasenha` |
| `GITLAB_TOKEN` | PRIVATE-TOKEN do GitLab (escopo: read_repository) | `glpat-...` |
| `GITLAB_URL` | URL base do GitLab da organização | `https://gitlab.suaorganizacao.com` |
| `GITLAB_PROJECT` | Projeto GitLab padrão (namespace/nome) | `grupo/projeto` |

## Migração de Dados Antigos

Se você usava a versão anterior (Streamlit com arquivos em `commits/`), migre para o banco SQLite com:

```bash
cd backend && ../.venv/bin/python3 migrate.py
```

O script lê automaticamente os arquivos `commits/diff_commits_*.txt`, seus caches `.json` e o `historico.csv` da raiz do projeto.

## Desenvolvimento Local (sem Docker)

```bash
# Instala dependências Python no ambiente virtual
.venv/bin/pip install -r backend/requirements.txt
.venv/bin/playwright install chromium

# Instala dependências do frontend
npm install --prefix frontend

# Sobe backend e frontend em paralelo
./start.sh

# Backend:  http://localhost:8000
# Frontend: http://localhost:5173
```

## Estrutura do Projeto

```
munka/
├── backend/          # FastAPI + SQLAlchemy + Playwright
│   ├── api.py        # Endpoints REST
│   ├── automation.py # Automação Playwright → portal Munka
│   ├── gemini_service.py  # Análise de diff com Gemini AI
│   ├── gitlab_service.py  # Cliente API do GitLab
│   ├── database.py   # Configuração SQLite (SQLAlchemy)
│   ├── models.py     # Modelos ORM (Commit, Analise, Historico)
│   ├── migrate.py    # Migração de dados antigos
│   └── Docs/         # Base de conhecimento do Gemini (preencher manualmente)
│
├── frontend/         # Vue 3 + Vite + Pinia + TypeScript
│   ├── src/views/    # Páginas: Commits, CommitDetail, History, Config
│   ├── src/stores/   # Estado global (Pinia)
│   └── src/api/      # Cliente HTTP (Axios)
│
├── docker-compose.yml
├── .env              # Credenciais (não versionar)
└── start.sh          # Script de desenvolvimento local
```

## Base de Conhecimento (`backend/Docs/`)

A pasta `backend/Docs/` contém os arquivos que o Gemini usa como contexto para classificar as atividades de faturamento. Os arquivos estão incluídos no repositório como **templates em branco** — preencha-os com o conteúdo real antes de usar a análise:

| Arquivo | Conteúdo esperado |
|---|---|
| `regras-medicao.md` | Regras de medição, tabela HPA por complexidade e prompt de contexto |
| `catalogo-servicos.md` | Catálogo completo de serviços com entregáveis e atividades |

> Sem o conteúdo nesses arquivos, o endpoint `POST /commits/{sha}/analisar` produzirá análises vazias ou incorretas.

## Tecnologias

| Camada | Stack |
|---|---|
| Frontend | Vue 3 + Vite + Pinia + TypeScript |
| Backend | Python 3.12 + FastAPI + SQLAlchemy |
| Banco de dados | SQLite (volume Docker persistente) |
| Automação web | Playwright (Chromium headless) |
| IA | Google Gemini (gemini-2.5-flash) |
| Containerização | Docker + Nginx |
