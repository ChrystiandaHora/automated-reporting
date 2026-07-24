# Munka 2.0

Ferramenta de automação de faturamento de entregas técnicas de software para o portal Munka (Saúde-GO). Importa commits do GitLab, analisa os diffs com Google Gemini AI, gerencia limites de cota de IA, e automatiza o cadastro e homologação de atividades no portal de faturamento via Playwright com suporte a filas assíncronas (Celery + Redis).

## Visão Geral do Fluxo

```
GitLab API → Importação de commits + diffs unificados
     ↓
Análise Gemini AI (Síncrona ou em Fila Celery)
     ↳ Identificação de atividades, complexidade, código do catálogo e HPA
     ↳ Painel de Rate Limit (RPM / TPM / RPD) com suporte a retries inteligentes
     ↓
Interface Web (Vue 3 + TypeScript)
     ↳ Revisão, edição de atividades e agrupamento para envios em lote
     ↳ Central de monitoramento de tarefas na fila assíncrona
     ↓
Playwright Headless → Automação no portal Munka
     ↳ Cadastro automático da tarefa
     ↳ Renderização e anexo de evidência técnica HTML/PNG
     ↳ Homologação da atividade e salvamento no histórico
```

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/)
- Python 3.12+ e Node.js 18+ (caso queira rodar sem Docker)
- Instância do [Redis](https://redis.io/) (para desenvolvimento local sem Docker)
- Arquivo `.env` configurado na raiz do projeto (veja modelo abaixo)

## Quick Start (Docker Compose)

```bash
# 1. Clone o repositório
git clone <url-do-repositorio> && cd automated-reporting

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas credenciais (Gemini, GitLab, Munka)

# 3. Inicie a aplicação completa via Docker Compose
docker-compose up --build
```

### Portas e Acessos do Sistema

| Serviço | URL | Descrição |
|---|---|---|
| **Frontend Web** | `http://localhost:5000` | Interface SPA para gestão de commits, fila, modelos e histórico |
| **Backend REST API** | `http://localhost:3000` | Endpoints FastAPI |
| **Documentação (Swagger)** | `http://localhost:3000/docs` | Interface OpenAPI interativa |
| **Celery Flower** | `http://localhost:3090` | Dashboard de monitoramento de workers Celery e tarefas |
| **Redis** | `localhost:3080` | Broker de mensagens e backend do Rate Limiter |

## Variáveis de Ambiente (`.env`)

```env
# Google Gemini AI
GEMINI_API_KEY=AIzaSy...

# Portal Munka
MUNKA_URL=https://munka.saude.go.gov.br
MUNKA_USER=seu.usuario
MUNKA_PASS=sua.senha
MUNKA_PROJETO=NOME_DO_PROJETO
MUNKA_PRODUTO=NOME_DO_PRODUTO
MUNKA_CARGO=9
MUNKA_NIVEL=3
MUNKA_RESPONSAVEL=Nome do Desenvolvedor
MUNKA_STATUS_ID=17
MUNKA_DATA_INICIO=08:00
MUNKA_DATA_FIM=18:00

# GitLab
GITLAB_TOKEN=glpat-...
GITLAB_URL=https://gitlab.saude.go.gov.br
GITLAB_PROJECT=grupo/projeto

# Redis & Celery (Docker envs pré-configurados)
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

## Estrutura do Projeto

```
automated-reporting/
├── backend/                  # API FastAPI + Celery + Playwright + SQLite
│   ├── api.py                # Endpoints REST e streaming SSE
│   ├── automation.py         # Script de automação Playwright no portal Munka
│   ├── celery_app.py         # Configuração Celery e roteamento de filas
│   ├── celery_tasks.py       # Workers assíncronos para análise Gemini e envio Munka
│   ├── concurrency.py        # Algoritmo de cálculo de trabalhadores baseado na CPU
│   ├── model_rate_limiter.py # Monitoramento em tempo real do Rate Limit dos modelos Gemini
│   ├── gemini_service.py     # Integração com Google Gemini AI
│   ├── gitlab_service.py     # Cliente HTTP para API do GitLab
│   ├── evidence_generator.py # Emissor de relatórios de evidências técnicas
│   ├── diff_renderer.py      # Gerador de imagens de diffs em PNG
│   ├── database.py           # Conexão SQLite / SQLAlchemy
│   ├── models.py             # Modelos de dados (Commit, Analise, Historico, Fila)
│   ├── migrate.py            # Migrador de arquivos legados JSON/CSV → SQLite
│   └── Docs/                 # Documentos de catálogo e regras de medição
│
├── frontend/                 # Interface Web Vue 3 + TypeScript + Vite
│   ├── src/
│   │   ├── api/              # Cliente Axios tipado
│   │   ├── components/       # Modais de ajuda e gerenciador de Toasts visuais
│   │   ├── stores/           # Gerenciamento de estado Pinia (Commits, Fila, Toasts)
│   │   ├── views/            # Visualizações SPA:
│   │   │   ├── CommitsView.vue      # Importação e busca de commits
│   │   │   ├── CommitDetailView.vue # Detalhe do commit, análise e envio
│   │   │   ├── AnalisarView.vue    # Análise em lote de múltiplos commits
│   │   │   ├── FilaView.vue        # Painel de acompanhamento da fila Celery
│   │   │   ├── ModelosView.vue     # Monitoramento do Rate Limit de IA
│   │   │   ├── HistoryView.vue     # Tabela de atividades homologadas
│   │   │   └── ConfigView.vue      # Gestão de credenciais e .env
│   │   └── App.vue           # Layout com navegação e badge de atualizações git
│   ├── nginx.conf            # Reverse proxy de produção para o frontend
│   └── Dockerfile            # Container Nginx com multi-stage build
│
├── docker-compose.yml        # Orquestração (Frontend, Backend, Workers Celery, Redis, Flower)
├── .env.example              # Modelo de variáveis de ambiente
└── start.sh                  # Script de inicialização para desenvolvimento local
```

## Desenvolvimento Local (sem Docker)

### 1. Iniciar Redis local
Certifique-se de que um servidor Redis está rodando na porta 6379 (ou altere no `.env`).

### 2. Configurar e rodar o Backend
```bash
# Criar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências e Playwright
pip install -r backend/requirements.txt
playwright install chromium

# Subir a API FastAPI
cd backend
uvicorn api:app --reload --port 8000
```

### 3. Rodar Workers Celery (em abas/terminais separados)
```bash
# Worker para fila de análises Gemini
celery -A celery_app worker --loglevel=info -Q analises

# Worker para fila de envios Munka (Playwright)
celery -A celery_app worker --loglevel=info -Q envios
```

### 4. Rodar o Frontend
```bash
cd frontend
npm install
npm run dev
# Acesse: http://localhost:5173
```

Alternativamente, utilize o script `./start.sh` na raiz do projeto para inicializar o ambiente de desenvolvimento local.

## Migração de Dados Legados

Se possui registros antigos armazenados em `commits/` ou `historico.csv`, execute o migrador automático para SQLite:

```bash
cd backend && python3 migrate.py
```

## Tecnologias

| Camada | Stack |
|---|---|
| **Frontend** | Vue 3, Vite, Pinia, TypeScript, Axios |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy |
| **Processamento Assíncrono** | Celery, Redis, Flower |
| **Banco de dados** | SQLite (Persistência via volume Docker) |
| **Automação Web** | Playwright (Chromium headless) |
| **Inteligência Artificial** | Google Gemini (2.5 Flash Lite, 3.1 Flash Lite, 3.5 Flash) |
| **Containerização** | Docker, Docker Compose, Nginx |
