# Frontend — Munka 2.0

Interface web em Vue 3 + TypeScript + Vite para o sistema de automação de faturamento.

## Stack

| Tecnologia | Papel |
|---|---|
| [Vue 3](https://vuejs.org/) + Composition API | Framework reativo |
| [TypeScript](https://www.typescriptlang.org/) | Tipagem estática |
| [Vite](https://vitejs.dev/) | Build e dev server |
| [Pinia](https://pinia.vuejs.org/) | Gerenciamento de estado |
| [Vue Router 4](https://router.vuejs.org/) | Roteamento SPA |
| [Axios](https://axios-http.com/) | Cliente HTTP |
| [Nginx](https://nginx.org/) | Servidor de produção (Docker) |

## Estrutura de Pastas

```
frontend/src/
├── api/
│   └── index.ts          # Cliente HTTP tipado (Axios) + interfaces TypeScript
│
├── stores/
│   └── commits.ts        # Stores Pinia: useCommitsStore e useAnaliseStore
│
├── router/
│   └── index.ts          # Rotas: /commits, /commits/:sha, /historico, /config
│
├── views/
│   ├── CommitsView.vue       # Lista de commits importados + modal de importação
│   ├── CommitDetailView.vue  # Análise Gemini + edição de atividades + envio ao Munka
│   ├── HistoryView.vue       # Tabela de atividades enviadas
│   └── ConfigView.vue        # Configuração de credenciais (Gemini, Munka, GitLab)
│
├── components/
│   └── HelpModal.vue     # Botão (?) com modal de ajuda contextual reutilizável
│
├── App.vue               # Layout principal com sidebar de navegação
└── main.ts               # Entry point — registra Pinia, Vue Router e monta a app
```

## Desenvolvimento

```bash
# Instala dependências
npm install

# Sobe o servidor de desenvolvimento (com proxy → backend em :8000)
npm run dev
# Acesse: http://localhost:5173
```

O Vite configura automaticamente um proxy em `/api/*` → `http://localhost:8000`, então o backend precisa estar rodando em paralelo (via `./start.sh` na raiz ou manualmente).

## Build de Produção

```bash
npm run build
# Output em frontend/dist/
```

Em Docker, o Dockerfile faz o build automaticamente e serve o `dist/` via Nginx. O Nginx também faz proxy de `/api/` → `http://backend:8000/`.

## Comunicação com o Backend

Toda a comunicação com a API usa o cliente em `src/api/index.ts` com `baseURL: '/api'`. Este prefixo é removido tanto pelo proxy do Vite (dev) quanto pelo Nginx (produção), chegando ao FastAPI sem o `/api`.

Exemplo de fluxo:
```
Frontend: GET /api/commits
   ↓ (Vite dev proxy ou Nginx)
Backend:  GET /commits  →  FastAPI retorna lista de commits
```

## Componente HelpModal

O `HelpModal.vue` é um botão circular `?` que abre um modal com texto de ajuda contextual. Usado em todas as páginas.

```vue
<HelpModal
  title="Título do modal"
  :items="[
    { title: 'Tópico 1', text: 'Explicação detalhada...' },
    { title: 'Tópico 2', text: 'Outra explicação...' },
  ]"
/>
```
