# Frontend — Nexus

Interface web moderna construída com Vue 3, TypeScript, Vite e Pinia para o sistema de automação de faturamento técnico e medição de software.

## Stack Tecnológica

| Tecnologia | Papel |
|---|---|
| [Vue 3](https://vuejs.org/) + Composition API | Framework reativo para construção de interfaces |
| [TypeScript](https://www.typescriptlang.org/) | Tipagem estática e interfaces para modelos da API |
| [Vite](https://vitejs.dev/) | Build tool de alta performance e dev server |
| [Pinia](https://pinia.vuejs.org/) | Gerenciamento de estado global reativo |
| [Vue Router 4](https://router.vuejs.org/) | Roteamento SPA e controle de navegação |
| [Axios](https://axios-http.com/) | Cliente HTTP para integração com a API REST FastAPI |
| [Nginx](https://nginx.org/) | Servidor web de produção e reverse proxy (Docker) |

## Estrutura de Pastas

```
frontend/src/
├── api/
│   └── index.ts            # Cliente Axios com tipagem estática e mapeamento de rotas da API
│
├── stores/
│   ├── commits.ts          # Store Pinia: gerenciamento de commits e análises
│   ├── fila.ts             # Store Pinia: polling e estado da fila de tarefas assíncronas
│   └── toast.ts            # Store Pinia: gerenciamento de notificações visuais do sistema
│
├── router/
│   └── index.ts            # Mapeamento de rotas da SPA
│
├── views/
│   ├── CommitsView.vue     # Tabela/Lista de commits importados com busca e importação
│   ├── CommitDetailView.vue# Visualizador de diff, análise Gemini, edição e disparo de envio
│   ├── AnalisarView.vue    # Importação e análise em lote de múltiplos commits
│   ├── FilaView.vue        # Painel da fila de tarefas assíncronas (acompanhamento e cancelamento)
│   ├── ModelosView.vue     # Painel de controle de Rate Limit de IA (modelos Gemini, RPM/TPM/RPD)
│   ├── HistoryView.vue     # Tabela de histórico de atividades enviadas/homologadas no Munka
│   └── ConfigView.vue      # Gerenciamento de credenciais e parâmetros das integrações
│
├── components/
│   ├── HelpModal.vue       # Componente de modal com ajuda contextual reutilizável
│   └── ToastManager.vue    # Gerenciador de notificações toast visuais sobrepostas
│
├── App.vue                 # Layout principal com barra superior de navegação e indicação de atualizações
└── main.ts                 # Ponto de entrada — inicializa Vue, Router, Pinia e estilização global
```

## Rotas da Aplicação

| Rota | View Component | Descrição |
|---|---|---|
| `/commits` | `CommitsView.vue` | Visualização de commits importados do GitLab e filtro de pesquisa |
| `/commits/:sha` | `CommitDetailView.vue` | Detalhes do commit, revisão da análise do Gemini e envio síncrono/stream ao Munka |
| `/analisar` | `AnalisarView.vue` | Importação em lote e seleção de modelo Gemini para análise de múltiplos commits |
| `/fila` | `FilaView.vue` | Central de controle das tarefas assíncronas (status Celery, logs e controle de execução) |
| `/modelos` | `ModelosView.vue` | Monitoramento e edição de limites de requisições/tokens dos modelos Gemini AI |
| `/historico` | `HistoryView.vue` | Relatório de atividades já enviadas e registradas no sistema Munka |
| `/config` | `ConfigView.vue` | Painel de configuração de variáveis do `.env` (credenciais Munka, GitLab e Gemini) |

## Desenvolvimento Local

```bash
# Instala as dependências do projeto
npm install

# Inicia o servidor de desenvolvimento Vite (com proxy configurado para o backend em :8000)
npm run dev
# Acesse a aplicação em: http://localhost:5173
```

O Vite configura automaticamente um proxy de desenvolvimento em `/api/*` → `http://localhost:8000`, eliminando a necessidade de tratar CORS no backend em ambiente de desenvolvimento.

## Build de Produção

```bash
# Gera os arquivos estáticos otimizados para produção
npm run build
# Os arquivos compilados serão gerados no diretório `frontend/dist/`
```

Em ambiente Docker, o `Dockerfile` executa o build multi-stage e serve os artefatos estáticos através do **Nginx**. O Nginx é responsável por rotear chamadas `/api/` diretamente para `http://backend:8000/`.

## Comunicação com o Backend

Toda a comunicação com a API REST FastAPI é centralizada em `src/api/index.ts`. As requisições utilizam o prefixo `/api` como base:

```
Frontend SPA (Axios) -> GET /api/commits
         │
         ▼
[Vite Dev Proxy (5173) ou Nginx Container (80)]
         │
         ▼ (remove o prefixo /api)
Backend FastAPI -> GET /commits
```

## Componentes Reutilizáveis

### `HelpModal.vue`
Botão flutuante ou contextual `?` que abre um modal com tópicos explicativos formatados para orientar o usuário em cada visualização.

### `ToastManager.vue`
Sistema de feedback visual em tempo real para exibir alertas de sucesso, informação, aviso ou erro de forma discreta e elegante na interface.
