# Análise de Commits com IA

Tela onde o usuário escolhe um modelo Gemini e seleciona commits importados para enfileirar a análise por IA.

## Rota e arquivos

- Rota: `/analisar` (`src/router/index.ts:24`).
- View: `src/views/AnalisarView.vue`.
- Componentes: `TutorialModal` (`src/components/TutorialModal.vue`).
- Stores: `useCommitsStore` (`src/stores/commits.ts`) para a lista de commits; `useFilaStore` (`src/stores/fila.ts`) para enfileirar.
- Tutorial: id `analisar` (`src/views/AnalisarView.vue:6`, definido em `src/config/tutorials.ts:125`).

## Para que serve

Depois de importar commits do GitLab, cada um precisa de uma análise por IA que gera as atividades (evidências e horas) a lançar no Munka. Esta tela permite escolher o modelo, filtrar e marcar vários commits de uma vez e mandá-los para a fila de execução. Ao confirmar, o usuário é levado para `/fila` para acompanhar o processamento.

## Seções da tela

1. Cabeçalho: título, botão de tutorial e link "Ver Fila de Execução" para `/fila` (`src/views/AnalisarView.vue:3-12`).
2. Passo 1, seleção do modelo de IA: grade de cartões `radio` com 4 modelos (`:14-50`, lista em `:530-535`).
3. Passo 2, seleção de commits (`:52-420`):
   - Alternador de modo "Por Repositório" / "Todos em Lista", com contadores (`:64-92`).
   - Filtro de status: Todos / Apenas Pendentes / Analisados (`:95-117`).
   - Campo de busca com botão de limpar (`:120-138`).
   - Chips de repositório, com contagem por repositório (`:142-169`).
   - Barra de ações em lote: Selecionar Pendentes, Selecionar Todos Exibidos, Desmarcar Todos (`:172-207`).
   - Estados: carregando, nenhum commit importado, nenhum resultado para os filtros (com "Limpar Filtros") (`:211-224`).
   - Modo por repositório: cartão por repositório com checkbox tri-estado, "Selecionar Pendentes (n)" e botão de recolher; linhas de commit (`:227-354`).
   - Modo lista: linhas de commit com etiqueta do repositório (`:357-419`).
4. Barra flutuante inferior, visível só com seleção: contagem de commits e de repositórios, modelo escolhido, "Limpar Seleção" e "Confirmar e Enfileirar (n)" (`:423-450`).

## Ações do usuário

| Ação | O que acontece | Endpoint/store |
| ---- | -------------- | -------------- |
| Abrir a tela | Carrega commits; se houver `?commit=<sha>`, pré-seleciona o commit cujo id começa com o valor (`:537-548`) | `commitsStore.fetchCommits` -> `GET /commits` e `GET` de stats |
| Escolher modelo | Atualiza `selectedModel` (clique, Enter ou Espaço) (`:29-31`) | local |
| Trocar modo/filtros/busca | Atualiza refs locais; a lista é recalculada | local |
| Clicar chip de repositório | Alterna `repositorioFiltro` (`:558-565`) | local |
| Marcar/desmarcar commit | Clique na linha ou checkbox alterna o id em `selecionados` (`:606-613`) | local |
| Checkbox do repositório | Marca/desmarca todos os commits do grupo exibido (`:723-733`) | local |
| Selecionar Pendentes (global ou do repo) | Adiciona os não analisados exibidos (`:735-745`) | local |
| Confirmar e Enfileirar | Chama `enfileirarAnalise(selecionados, selectedModel)` e navega para `/fila` (`:768-779`) | `filaStore.enfileirarAnalise` -> `POST /fila/analise` |
| Limpar Filtros | Zera repositório, status e busca (`:567-571`) | local |

## Dados e estado

- `commitsStore.commits` e `commitsStore.loading`: lista vinda de `api.commits.listar()` (`src/stores/commits.ts:12-23`). Não há polling nesta tela.
- Refs locais (`src/views/AnalisarView.vue:468-477`): `selectedModel` (inicial `Gemini 3.8 Flash`), `selecionados` (ids), `enfileirando`, `visaoModo` (inicial `repositorio`), `statusFiltro` (inicial `pendentes`), `repositorioFiltro`, `termoBusca`, `reposColapsados`.
- Computeds: `commitsFiltrados` (`:620`), `totalPendentesGeral`, `totalPendentesExibidos`, `repositoriosResumo` (todos os commits, ordenado por quantidade), `commitsAgrupadosPorRepo` (só os filtrados), `totalRepositoriosSelecionados`.
- A seleção (`selecionados`) não é limpa quando os filtros mudam: pode haver ids selecionados que não estão visíveis.

## Regras e filtros

- Filtros aplicados em sequência: repositório, status, busca textual (`:620-648`). A busca é case-insensitive sobre mensagem, id (SHA), autor e projeto.
- Commit sem `projeto` é agrupado como "Sem repositório".
- "Pendente" significa `!commit.analisado`; commits analisados mostram badge verde e, se houver, o total de atividades (`atv.`, apenas no modo por repositório).
- Ordenação: repositórios por quantidade de commits (decrescente); a ordem dos commits segue a resposta de `GET /commits` (mais recentemente importado primeiro, `backend/api.py:373-382`).
- Botões "Selecionar Pendentes" ficam desabilitados quando não há pendentes exibidos; "Selecionar Todos Exibidos" quando a lista filtrada está vazia.
- Cores do repositório e do avatar do autor derivam de um hash do nome (`:573-604`).
- Estado de erro: a store guarda `commitsStore.error`, mas a tela não o exibe (não verificado se outro componente exibe).
- Falha ao enfileirar: o toast é emitido pela store; a tela permanece e `enfileirando` volta a `false` (`:774-778`).

## Endpoints usados

| Método | Rota | Uso |
| ------ | ---- | --- |
| GET | `/commits` | Lista de commits com flag `analisado` e `atividades_total` (`backend/api.py:373`) |
| POST | `/fila/analise` | Cria um job `analise` (status `pending`) por commit e dispara `analisar_commit_task` no Celery; corpo `{commit_ids, modelo}` (`backend/api.py:1909-1942`) |

## Notas

- Marcadores do tutorial: elementos com `data-tour="..."` (alvos `target:` dos tutoriais `analisar` em `src/config/tutorials.ts`). Não dependem de classes CSS: renomear ou reestilizar um elemento não quebra o tutorial, mas remover o `data-tour` sim.
- O backend sempre força re-análise (`True` passado à task, `backend/api.py:1931`), então enfileirar commits já "Analisados" sobrescreve a análise existente.
- O backend ignora silenciosamente ids que não casam com nenhum commit (`continue`, `backend/api.py:1916`), mas o toast da store informa `commitIds.length`, não o número real enfileirado.
- O pré-seleção por `?commit=` ocorre só no `onMounted`; se o commit já estiver analisado e o filtro inicial for "pendentes", ele fica selecionado mas oculto.
- A lista de modelos é fixa no front (`:530-535`) e duplicada em `src/views/FilaView.vue:1102`. A tela de Modelos/Config não é consultada aqui (não verificado se há relação).
- `/fila` é a tela de destino; o progresso aparece lá (ver `fila.md`).
