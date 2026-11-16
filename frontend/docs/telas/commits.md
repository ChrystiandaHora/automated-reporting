# Commits

Lista dos commits importados, agrupada por repositório ou por data, com busca, filtros e ações em lote (análise por IA e envio ao Munka).

## Rota e arquivos

- Rota: `/commits` — `src/router/index.ts:21`. Aceita `?repo=<nome>` e `?fila=true` (`src/views/CommitsView.vue:1140-1146`).
- View: `src/views/CommitsView.vue`.
- Componentes: `TutorialModal` (`screenId="commits"`, linha 6).
- Stores: `useCommitsStore`, `useFilaStore`, `useToastStore`.
- Tutorial: id `commits` em `src/config/tutorials.ts:53`.

## Para que serve

É a central de trabalho sobre os commits já importados. Mostra o estado de cada um (pendente ou analisado, quantas tarefas foram enviadas, se há jobs na fila) e permite selecionar vários para mandar para análise da IA ou para o Munka. Dali também se abre o detalhe de cada commit.

## Seções da tela

1. Cabeçalho: título, tutorial e botão "+ Importar Commit" (navega para `/importar`) (`:3-12`).
2. Estados: "Carregando commits..." (`:36`), vazio "Nenhum commit importado..." (`:39`).
3. Barra de controle (`:47-244`):
   - abas "Por Repositório" e "Linha do Tempo (Data)" com contadores;
   - caixa de busca (mensagem, SHA, autor ou repositório);
   - chips: Todos, "Na Fila" (só se há jobs ativos) e um por repositório (com selo de fila);
   - faixa de "Filtros ativos" com remoção individual e "Limpar Filtros";
   - "Seleção em lote": Selecionar Todos, Apenas Analisados, Apenas Pendentes, contador e Limpar.
4. Mensagem "Nenhum commit encontrado" quando os filtros zeram a lista (`:247`).
5. Visão por repositório (`:255`): um card por repositório, colapsável, com checkbox de repositório, badges (na fila, analisados, pendentes, HPA) e as linhas de commit.
6. Visão por data (`:484`): grupos por dia ("31 Ago, 2026") com as linhas de commit e uma tag clicável do repositório.
7. Linha de commit: checkbox, avatar com iniciais, mensagem, badges (Analisado/Pendente, `enviadas/total env.`, "Análise na fila", "N na fila"), autor e tempo relativo, e os botões excluir, copiar SHA e abrir detalhes (olho).
8. Modal de confirmação de exclusão (`:~660`) e barra flutuante de ações em lote, visível com seleção (`:~690`).

## Ações do usuário

| Ação | O que acontece | Endpoint/store |
| ---- | -------------- | -------------- |
| Abrir a tela | Carrega commits e jobs; inicia polling da fila (`:1140`) | `GET /commits`, `GET /commits/stats`, `GET /fila` |
| Alternar aba Repositório/Data | Muda `visaoModo` e grava em `localStorage` (`nexus-commits-view-mode`) (`:965`) | local |
| Buscar / clicar em chip / "Na Fila" | Filtra `commitsFiltrados` | local |
| Clicar na tag de repositório (visão por data) | Alterna filtro do repositório | local |
| Clicar no cabeçalho do card | Expande/recolhe o repositório | local |
| Clicar na linha ou no checkbox | Seleciona/desmarca o commit (a linha inteira seleciona, não abre) | local |
| Botão olho | Abre `/commits/<sha>` (único caminho para o detalhe) | router |
| Botão SHA | Copia o SHA completo e mostra toast (`:1247`) | clipboard |
| Lixeira, confirmar | Exclui commit e análise (`confirmarExclusao`, `:1271`) | `DELETE /commits/{sha}` via `store.deletar` |
| "Adicionar N Tarefa(s) na Fila Munka" | Enfileira envio em lote e recarrega (`:1653`) | `POST /fila/envio-lote` (`forcar_reenvio=false`) |
| "Reenfileirar N Tarefa(s)" | Pede `confirm()` e enfileira com `forcar_reenvio=true` (`:1667`) | `POST /fila/envio-lote` |
| "Analisar N com IA" | Enfileira análise dos selecionados pendentes (`:1684`) | `POST /fila/analise` |
| "Ver Fila" | Navega para `/fila` | router |

## Dados e estado

- `store.commits` (`CommitSummary[]`), `store.loading`.
- `filaStore.jobs` alimenta `filaPorCommit` (`:1086`): por commit, conta jobs `pending/running`, separando `analise` e envios.
- Filtros: `repositorioFiltro` (`'todos'` por padrão), `termoBusca`, `apenasNaFila` (`:950-952`).
- `commitsFiltrados` (`:1378`) -> `commitsAgrupadosPorRepo` (`:1442`) e `commitsAgrupadosPorData` (`:1413`); `repositoriosResumo` (`:1323`) alimenta os chips e usa todos os commits.
- Seleção: `selecionados: string[]` (ids), com computeds `totalTarefasProntas`, `totalTarefasJaEnviadas`, `totalCommitsPendentesSelecionados` etc. (`:1548-1650`).
- Estado de UI: `reposColapsados`, `shaCopiadoId`, `commitParaDeletar`, `exibindoModalConfirmacao`.

## Regras e filtros

- Repositório vazio vira "Sem repositório". Cores de repositório e avatar são determinísticas (hash do nome).
- Ordenação: commits por timestamp decrescente (`data_autor`, depois `data` `DD/MM/AAAA`, depois `importado_em`); repositórios por quantidade de commits decrescente; grupos de data pelo mais recente.
- Tarefas prontas = soma de `atividades_total - atividades_enviadas` dos selecionados analisados (`:1620`). Botão de envio normal só aparece se > 0; se não há prontas, mas há já enviadas em selecionados analisados, aparece o de reenfileirar.
- "Analisar com IA" só envia os selecionados com `analisado = false`; o modelo está fixo no código como `'Gemini 3.8 Flash'` (`:1688`).
- Após o envio em lote, a seleção é limpa; após a análise, não (`:1688-1696`).
- Auto-atualização: quando o número de jobs `done`/`error` aumenta, recarrega `store.fetchCommits()` (`:1131`).
- Vindo de `/dashboard`, `?repo=` pré-seleciona o repositório. `?fila=true` ativa "Apenas na Fila".
- Seleção persiste entre filtros (pode haver selecionados fora da lista exibida; a barra de lote conta todos).

## Endpoints usados

| Método | Rota | Uso |
| ------ | ---- | --- |
| GET | `/commits` | Lista (`backend/api.py:373`) |
| GET | `/commits/stats` | Chamado por `fetchCommits` (`backend/api.py:443`) |
| DELETE | `/commits/{sha}` | Exclui commit e Analise associada (`backend/api.py:818`) |
| GET | `/fila` | Polling de jobs (`backend/api.py:2316`) |
| POST | `/fila/analise` | Enfileira análises (`backend/api.py:1909`) |
| POST | `/fila/envio-lote` | Enfileira envios de todas as atividades pendentes; exige MUNKA_USER/PASS configurados, senão 400 (`backend/api.py:1986`) |
| POST | `/commits/importar` | Só pelo modal de importação, hoje inalcançável (ver Notas) |

## Notas

- Código morto: o modal "Importar Commits do GitLab (Lote)" (`showImport`, `importar()` em `:1497`) nunca é aberto: `showImport` só é posto em `false`. O botão do cabeçalho navega para `/importar`.
- A linha inteira seleciona, então clicar nela não abre o commit; só o ícone de olho abre.
- Textos de tempo relativo estão em inglês ("authored 2 hours ago", "just now"), mesmo com a interface em português.
- Os chips e `repositoriosResumo` ignoram os filtros; os contadores dos chips são sempre totais.
- Enfileirar no Munka depende de credenciais configuradas em Configurações; erro do backend aparece como toast da store da fila.
- Marcadores do tutorial: elementos com `data-tour="..."` (alvos `target:` dos tutoriais `commits` em `src/config/tutorials.ts`). Não dependem de classes CSS: renomear ou reestilizar um elemento não quebra o tutorial, mas remover o `data-tour` sim.
- Os números de linha de blocos finais do template (modal e barra flutuante) são aproximados (marcados com `~`).
