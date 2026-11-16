# Mapa de telas

Frontend Vue 3 + Vue Router + Pinia (`frontend/src`). Navegação: barra superior plana em `App.vue`; títulos em `routeTitles`.

| Rota | Arquivo | Finalidade | Endpoints / stores |
| ---- | ------- | ---------- | ------------------ |
| `/` | — | Redireciona para `/dashboard` | — |
| `/dashboard` | `views/DashboardView.vue` | KPIs executivos, commits e horas (HPA) | `config.obter`, stores commits e fila |
| `/commits` | `views/CommitsView.vue` | Lista de commits e ações | stores commits, fila, toast |
| `/commits/:sha` | `views/CommitDetailView.vue` | Detalhe do commit e editor por atividade | `commits.obter/atualizar/verificarDataFim`, `analise.previewEvidencia` |
| `/importar` | `views/ImportarCommitsView.vue` | Importação de commits do GitLab | `commits.importar`, `gitAccounts.listar` |
| `/analisar` | `views/AnalisarView.vue` | Análise por IA dos commits | stores commits e fila |
| `/fila` | `views/FilaView.vue` | Fila de execução | `fila.*`, store fila |
| `/fila-logs` | `views/FilaLogsView.vue` | Logs de execução | `filaLogs.*` |
| `/modelos` | `views/ModelosView.vue` | Limites de uso por modelo de IA | `modelos.*` |
| `/historico` | `views/HistoryView.vue` | Histórico de lançamentos | `historico.*`, `analise.obter` |
| `/tarefas-mes` | `views/TarefasView.vue` | Wrapper com abas; redireciona para `/tarefas-mes/lista` | — |
| `/tarefas-mes/lista` | `views/TarefasMesView.vue` | Auditoria e ajuste (individual/lote) de tarefas no Munka | `tarefasMes.listar/sincronizar/ajustar` |
| `/tarefas-mes/kanban` | `views/TarefasKanbanView.vue` | Kanban somente leitura, uma coluna por status | `tarefasMes.listar` |
| `/config` | `views/ConfigView.vue` | Configurações (Git, Munka, backup) | `config.*`, `gitAccounts.*`, `backup.*` |

Componentes compartilhados: `TutorialModal`, `HelpModal`, `NotificacoesSino`, `ToastManager`.

## Status do Munka

Fonte única: `src/config/statusMunka.ts` (frontend) e `backend/status_munka.py` (backend, exposto em `GET /status-munka`). IDs: 15 Backlog, 16 Backlog Prioritário, 17 Pendente, 18 Desenvolvimento, 19 Concluído para o Supervisor, 20 Homologação, 21 Concluído, 22 Arquivado, 35 Evidência com Pendência.

Onde é usada: Configurações (Status Inicial Padrão), modais de ajuste individual e em lote, filtro "Status no portal", badges e colunas do Kanban.
