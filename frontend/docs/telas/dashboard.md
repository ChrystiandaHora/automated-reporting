# Dashboard de Indicadores

Painel executivo com métricas consolidadas de commits, cobertura da análise por IA e faturamento HPA enviado ao Munka.

## Rota e arquivos

- Rota: `/dashboard` (a raiz `/` redireciona para ela) — `src/router/index.ts:19-20`.
- View: `src/views/DashboardView.vue`.
- Componentes: `TutorialModal` (`screenId="dashboard"`, linha 8).
- Stores: `useCommitsStore` (`src/stores/commits.ts`) e `useFilaStore` (`src/stores/fila.ts`); também chama `api.config.obter()` direto (`DashboardView.vue:621`).
- Tutorial: id `dashboard` em `src/config/tutorials.ts:17`.

## Para que serve

É a tela inicial. Resume quanto HPA (horas faturáveis) foi identificado pela IA, quanto já foi enviado ao Munka e quanto falta, além de mostrar a saúde das integrações e da fila. Serve para decidir o que fazer no dia: importar commits, analisar pendentes ou enviar tarefas.

## Seções da tela

1. Cabeçalho: título, tutorial, seletor de **Período** (só aparece com `store.stats`), botão de recarregar e botão "+ Importar Commit" (`:4-55`).
2. Barra de status das integrações (GitLab, Gemini IA, Munka) e link para a fila com contador (`:58-82`).
3. Estados: carregando (`:85`), vazio com botão "Importar Primeiro Commit" (`:90`) ou o conteúdo principal.
4. Faixa de 5 KPIs: HPA Faturável, Tarefas Identificadas, Commits no Período, Esforço Médio, Status da Fila (`:106-209`).
5. Banner de ações recomendadas, só se houver commits ou tarefas pendentes (`:212-238`).
6. Pipeline de Automação com 4 etapas (`:241-265`).
7. Duas colunas: "Repositórios & Faturamento" e "Evolução Mensal de HPA" (gráfico SVG de barras) (`:268-432`).
8. Tabela "Quantificação por Tipo de Serviço" com busca e ordenação (`:435-514`).

## Ações do usuário

| Ação | O que acontece | Endpoint/store |
| ---- | -------------- | -------------- |
| Trocar o Período | Recalcula KPIs, pipeline, repositórios e tabela (filtro local) | só `mesSelecionado` (`:583`) |
| Clicar no botão recarregar | Refaz todas as cargas (`carregarTudo`, `:599`) | `fetchCommits`, `fetchStats`, `filaStore.fetchJobs(true)`, `GET /config` |
| "+ Importar Commit" / "Importar Primeiro Commit" | Navega para `/importar` | router |
| Link da fila (barra de status e KPI 5) | Navega para `/fila` | router |
| "Gerenciar na Tela de Commits" | Navega para `/commits` | router |
| Clicar numa linha de repositório | Vai para `/commits?repo=<nome>` (`navegarParaRepo`, `:762`) | router |
| Clicar numa barra do gráfico | Alterna o mês selecionado; clicar de novo volta a "todos" (`selecionarMes`, `:891`) | local |
| "Ver Consolidado" | `mesSelecionado = 'todos'` | local |
| Buscar código / ordenar (Mais HPA, Mais Tarefas, Código) | Filtra/ordena a tabela | local |

## Dados e estado

- `store.commits` (`CommitSummary[]`) e `store.stats` (`CommitStatsResponse`: `months`, `by_month`, `totals`) vêm da store de commits.
- `filaStore.jobs` alimenta os contadores da fila; `startPolling()` é chamado após o carregamento (`:596`).
- `servicosStatus` (`:588`): padrão `true` para os três serviços; sobrescrito por `cfg.status` de `GET /config` (`:621-624`). Falha na chamada é silenciosa (mantém `true`).
- `commitsDoPeriodo` (`:653`): filtra `store.commits` pelo mês; `statsExibidas` (`:661`) usa `stats.totals` ou `stats.by_month[mes]`.
- Derivados: `taxaAnaliseIA`, `hpaEnviadoPeriodo`, `hpaPendentePeriodo`, `taxaHpaEnviado`, `tarefasEnviadasPeriodo`, `tarefasPendentesPeriodo`, `mediaHpaPorTarefa` (`:672-725`).
- `distribuicaoRepositorios` (`:767`) agrega por `projeto`; `historicoMensal` (`:837`) ordena `stats.months` cronologicamente; `codigosProcessados` (`:900`) monta a tabela.

## Regras e filtros

- Mês do commit: `data_autor` (ISO) formatado `MM/AAAA`; fallback para `data` no formato `DD/MM/AAAA`; senão `'Outros'` (`:631-650`). Os meses do seletor vêm de `stats.months`, então commits em `'Outros'` só aparecem em "Consolidado" pelas listas, mas não têm opção própria (a menos que o backend a envie).
- Tarefas na fila = jobs com status `pending` ou `running` (`:728`).
- Commits sem `projeto` são agrupados como "Sem repositório"; repositórios ordenados por HPA total decrescente (`:823`).
- Percentuais limitados a 100; divisões por zero retornam 0.
- KPI 3: selo verde se cobertura de IA >= 90%, senão âmbar. Pipeline: etapa 2 "concluída" com >= 90% (`:970`); etapa 4 com 100% de tarefas enviadas (`:984`).
- Barra do KPI 4 é escala fixa: média / 3,0 h (`:180`); barra do KPI 5 é fixa (70% com fila, 100% sem).
- Banner de ações aparece se `commitsPendentesPeriodo > 0` ou `tarefasPendentesPeriodo > 0`.
- Tabela de códigos: busca por substring no código (case-insensitive); vazio mostra "Nenhum código de serviço encontrado...". Gráfico vazio e repositórios vazios têm mensagens próprias.
- Carregando: só mostra "Carregando indicadores..." se `store.loading` e ainda não há commits.

## Endpoints usados

| Método | Rota | Uso |
| ------ | ---- | --- |
| GET | `/commits` | Lista de commits com métricas de atividades/HPA (`backend/api.py:373`) |
| GET | `/commits/stats` | Totais de tarefas e HPA por código e por mês (`backend/api.py:443`) |
| GET | `/config` | Config com `status` das integrações; segredos mascarados (`backend/api.py:1673`) |
| GET | `/fila` | Jobs da fila, via polling (`backend/api.py:2316`) |

## Notas

- `store.fetchCommits()` já chama `fetchStats()` internamente (`src/stores/commits.ts:19`), e a view chama `fetchStats()` de novo em paralelo: `/commits/stats` é requisitado duas vezes por carga.
- O polling da fila (3 s) para sozinho quando não há jobs ativos (`src/stores/fila.ts:176-190`).
- Marcadores do tutorial: elementos com `data-tour="..."` (alvos `target:` dos tutoriais `dashboard` em `src/config/tutorials.ts`). Não dependem de classes CSS: renomear ou reestilizar um elemento não quebra o tutorial, mas remover o `data-tour` sim.
- O texto do tutorial diz "Clique nos números para acessar as listagens" e fala em 3 etapas do pipeline; a tela tem 4 etapas e os números dos KPIs não são clicáveis (só o link da fila). Texto do tutorial desatualizado.
- Os rótulos "Gemini" e "Munka" refletem apenas as flags de `cfg.status`; o que cada flag verifica no backend: não verificado.
