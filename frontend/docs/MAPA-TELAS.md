# Mapa de telas

Frontend Vue 3 + Vue Router + Pinia (`frontend/src`). Navegação: barra superior plana em `App.vue`; títulos em `routeTitles`.

| Rota | Arquivo | Finalidade | Endpoints / stores |
| ---- | ------- | ---------- | ------------------ |
| `/` | — | Redireciona para `/dashboard` | — |
| `/dashboard` | `views/DashboardView.vue` ([doc](telas/dashboard.md)) | KPIs executivos, commits e horas (HPA) | `config.obter`, stores commits e fila |
| `/commits` | `views/CommitsView.vue` ([doc](telas/commits.md)) | Lista de commits e ações | stores commits, fila, toast |
| `/commits/:sha` | `views/CommitDetailView.vue` ([doc](telas/commit-detalhe.md)) | Detalhe do commit e editor por atividade | `commits.obter/atualizar/verificarDataFim`, `analise.previewEvidencia` |
| `/importar` | `views/ImportarCommitsView.vue` ([doc](telas/importar.md)) | Importação de commits do GitLab | `commits.importar`, `gitAccounts.listar` |
| `/analisar` | `views/AnalisarView.vue` ([doc](telas/analisar.md)) | Análise por IA dos commits | stores commits e fila |
| `/fila` | `views/FilaView.vue` ([doc](telas/fila.md)) | Fila de execução | `fila.*`, store fila |
| `/fila-logs` | `views/FilaLogsView.vue` ([doc](telas/fila-logs.md)) | Logs de execução | `filaLogs.*` |
| `/modelos` | `views/ModelosView.vue` ([doc](telas/modelos.md)) | Limites de uso por modelo de IA | `modelos.*` |
| `/historico` | `views/HistoryView.vue` ([doc](telas/historico.md)) | Histórico de lançamentos | `historico.*`, `analise.obter` |
| `/tarefas-mes` | `views/TarefasView.vue` | Wrapper com abas; redireciona para `/tarefas-mes/lista` | — |
| `/tarefas-mes/lista` | `views/TarefasMesView.vue` ([doc](telas/tarefas-mes.md)) | Auditoria e ajuste (individual/lote) de tarefas no Munka | `tarefasMes.listar/sincronizar/ajustar` |
| `/tarefas-mes/kanban` | `views/TarefasKanbanView.vue` ([doc](telas/tarefas-mes.md)) | Kanban somente leitura, uma coluna por status | `tarefasMes.listar` |
| `/config` | `views/ConfigView.vue` ([doc](telas/configuracao.md)) | Configurações (Git, Munka, backup) | `config.*`, `gitAccounts.*`, `backup.*` |

Componentes compartilhados: `TutorialModal`, `HelpModal`, `NotificacoesSino`, `ToastManager`.

## Status do Munka

Fonte única: `src/config/statusMunka.ts` (frontend) e `backend/status_munka.py` (backend, exposto em `GET /status-munka`). IDs: 15 Backlog, 16 Backlog Prioritário, 17 Pendente, 18 Desenvolvimento, 19 Concluído para o Supervisor, 20 Homologação, 21 Concluído, 22 Arquivado, 35 Evidência com Pendência.

Onde é usada: Configurações (Status Inicial Padrão), modais de ajuste individual e em lote, filtro "Status no portal", badges e colunas do Kanban.

## Estilos (Tailwind v4)

Todas as telas são estilizadas só com utilidades Tailwind. Não há CSS por tela nem CSS global de classes.

- **Único CSS:** `src/assets/tailwind.css`. Contém o preflight oficial do Tailwind, os tokens de cor/sombra/animação em `@theme`, as variáveis dos temas escuro e claro (`[data-theme]`) e três regras globais (anel de foco, barra de rolagem). Camadas: `theme < base < utilities`: utilidade sempre vence, então **não use `!important` nem o modificador `!`**.
- **Cores:** só tokens (`bg-background`, `bg-card`, `text-foreground`, `text-muted-foreground`, `border-border`, `text-primary`, `bg-badge-green`…). Seguem o tema claro/escuro. Cor nova vira token no `@theme`, nunca valor arbitrário como `bg-[#abc]`.
- **Componentes base** (`src/components/ui/`), único lugar do visual compartilhado:

| Componente | Uso |
| ---------- | --- |
| `BaseButton` | `variant` primary / ghost / danger / plain; `size` md / sm / xs; `to` para virar link |
| `BaseBadge` | `variant` green / gray / blue / orange / purple / hpa / plain |
| `BaseModal` | fundo + painel; `size` sm / md / lg / xl / auto; slot `actions`; painel em `modalRef.panel` |
| `BaseInput`, `BaseSelect`, `BaseTextarea` | campos com `v-model` (`.number`, `.trim`); `autoWidth` |
| `BaseLabel` | rótulo de formulário |
| `PageHeader`, `PageTitle` | cabeçalho e `h1` das telas |
| `StateMessage` | `type` loading / empty / error / success |
| `SearchBox`, `PillButton`, `FiltersBar` | busca, filtros em pílula e barra de filtros |

  Não passe aos componentes utilidades que repitam a mesma propriedade da variante (padding, cor, borda, largura): duas utilidades da mesma propriedade não têm ordem garantida. Para um visual próprio use `variant="plain"`, `size="auto"` ou `autoWidth`.
- **Tutorial:** os alvos em `src/config/tutorials.ts` usam atributos `data-tour="<tela>-<elemento>"`, não classes.
- **Build:** roda no Docker (`docker compose build frontend`); o `node_modules` da máquina não é usado.
