# Tarefas do Mês (Munka)

Área com duas abas, Lista e Kanban, para auditar e ajustar no portal Munka as tarefas lançadas em um mês.

## Rota e arquivos

- Rotas (`src/router/index.ts:29-37`): `/tarefas-mes` (wrapper, redireciona para `/tarefas-mes/lista`), `/tarefas-mes/lista` e `/tarefas-mes/kanban` (rotas filhas).
- Wrapper: `src/views/TarefasView.vue`. Lista: `src/views/TarefasMesView.vue`. Kanban: `src/views/TarefasKanbanView.vue`.
- Store: `src/stores/tarefasMes.ts` (mês/ano compartilhados). Outras: `useToastStore`, `useFilaStore` (só na Lista).
- Catálogo de status: `src/config/statusMunka.ts` e `backend/status_munka.py`.
- Ids de tutorial: `tarefas-mes` na Lista (`src/views/TarefasMesView.vue:8`) e `tarefas-kanban` no Kanban (`src/views/TarefasKanbanView.vue:6`). O wrapper não tem tutorial.

## Para que serve

Cada atividade enviada ao Munka gera um registro de histórico. Esta área lista os registros do mês escolhido, mostra o status real da tarefa no portal e deixa ajustar campos (status, cargo, nível etc.) individualmente ou em lote. O Kanban mostra os mesmos dados agrupados por status, só para leitura.

## Seções da tela

### Wrapper e abas

- Barra de abas Lista / Kanban com `router-link`; a aba ativa é a que tem `route.path` igual ao destino (`src/views/TarefasView.vue:1-14`, `:22-25`), seguida de `<router-view />`.

### Aba Lista

1. Cabeçalho: título, tutorial, contador "N lançadas", seletor de período (anterior, mês, ano, próximo, "Hoje" fora do mês atual), "Sincronizar no Munka" e "Atualizar" (`TarefasMesView.vue:4-94`).
2. Quatro cards de métricas: Total Lançadas, Disponíveis p/ Ajuste, Concluídas no Munka, Selecionadas (`:97-150`).
3. Barra de ações em lote, visível com seleção (`:153-167`).
4. Filtros: busca geral, botões Todas / Em Aberto / Concluídas e, em linha, Regra, Nome da atividade, Status no portal, Condição supervisor e "Limpar filtros" (`:170-265`).
5. Estados de carregando e vazio (`:268-294`) e a tabela: seleção, ID Munka (link), Atividade & Commit, Regra/HPA, Status no Portal, Condição Supervisor, Ajustar (`:297-441`).
6. Modal de ajuste individual (`:446-565`) e modal de ajuste em lote (`:568-775`).

### Aba Kanban

Cabeçalho com contador "X de Y" e seletor de mês/ano; filtros Regra e Nome da atividade; quadro com uma coluna por status, cada uma com cartões de tarefa (`TarefasKanbanView.vue:3-65`).

## Ações do usuário

| Ação | O que acontece | Endpoint/store |
| ---- | -------------- | -------------- |
| Trocar mês/ano (Lista ou Kanban) | Atualiza a store e recarrega (`mudarMes`, `TarefasMesView.vue:1048`; `TarefasKanbanView.vue:119`) | `GET /tarefas-mes`, `tarefasMes` store |
| "Hoje" (Lista) | Volta ao mês atual (`:1063`) | idem |
| "Sincronizar no Munka" (Lista) | Enfileira leitura de status no portal e atualiza a fila (`:1083`) | `POST /tarefas-mes/sincronizar`, `filaStore.fetchJobs` |
| Marcar linhas / "selecionar todas" | Seleciona as visíveis (`:1015-1034`) | estado local |
| "Ajustar" na linha | Abre modal individual com padrões da config (`:1096`) | `GET /config` (na montagem) |
| Salvar ajuste individual | Envia um id e todos os campos do formulário (`:1113`) | `POST /tarefas-mes/ajustar` |
| Ajuste em lote | Só envia campos cujo toggle está ligado (`:1171-1190`) | `POST /tarefas-mes/ajustar` |
| Abrir tarefa no Munka | Link externo `task_url` | — |
| Clicar no SHA (Lista) | `/commits/:sha` (`:367`) | router |

## Dados e estado

- Store `tarefasMes`: `mes` e `ano`, iniciados com a data de hoje; compartilhados pelas duas abas (`src/stores/tarefasMes.ts:5-9`). Trocar o período numa aba vale para a outra.
- Lista: `dados` (resposta de `/tarefas-mes`), `filtroTexto`, `filtroStatus`, `filtroRegra`, `filtroAtividade`, `filtroStatusPortal`, `selecionadosIds`, `configPadrao`, `formSingle`, `formLote`, `habilitarCampo` (`TarefasMesView.vue:857-922`).
- Kanban: `dados`, `loading`, `filtroRegra`, `filtroAtividade` (`TarefasKanbanView.vue:85-88`).
- A Lista carrega `GET /config` ao montar para preencher padrões; falha é ignorada (`:1249-1255`).

## Regras e filtros

- Filtros da Lista combinam em `tarefasFiltradasPorTexto` (Regra, Status no portal, Nome, busca geral em título, SHA, autor, mensagem, código e id Munka); "Condição supervisor" é aplicada depois, para que as contagens dos botões respeitem os demais filtros (`:969-1002`).
- Condição "Concluída" = `isStatusConcluido(status_munka || status)` (`:928`). O cartão "Concluídas no Munka" usa `dados.concluidas` do backend; o cartão "Disponíveis p/ Ajuste" mostra `dados.total` (`:114`, `:125`).
- Trocar o mês limpa a seleção (`carregarTarefas`, `:1072`).
- Lote: botão "Aplicar" fica desabilitado com zero campos ligados (`:765`). Por padrão os toggles começam desligados.
- Após ajuste, a UI atualiza o status de forma otimista com `rotuloStatus` e recarrega a lista (`:1129-1137`, `:1196-1211`).
- Vazio na Lista: mensagem distinta se há filtros ativos ou não, com botão para sincronizar (`:274-294`). Kanban: coluna vazia mostra "Nenhuma tarefa" (`:47`). Erro de carga: toast (`:1077`, `TarefasKanbanView.vue:139`).

## Catálogo único de status

- Frontend: `CATALOGO_STATUS` com `id`, `rotulo`, `concluida`, `badge` (`src/config/statusMunka.ts:26-36`); backend: `CATALOGO_STATUS` com `(id, rótulo, concluída)` em `backend/status_munka.py:4-14`. IDs: 15 Backlog, 16 Backlog Prioritário, 17 Pendente, 18 Desenvolvimento, 19 Concluído para o Supervisor, 20 Homologação, 21 Concluído, 22 Arquivado, 35 Evidência com Pendência. Concluídos: 19 e 21.
- `STATUS_OUTROS` (id `outros`, "Sem status / Outros") é o balde para o que não casa (`:19`).
- `resolverStatus(valor)`: normaliza (sem acento, minúsculas), tenta casar por id, depois por rótulo, depois por `ALIASES` (ex.: "enviado ao munka" e "aberto" viram 17; "concluido" vira 21); senão `null` (`:57-67`).
- `isStatusConcluido` e `classeBadgeStatus` usam o catálogo e, sem correspondência, heurísticas por texto ("conclu", "supervisor", "homolog"...) (`:73-91`).
- Backend: `STATUS_MAP` mapeia id para rótulo, com o 17 gravado como "Enviado ao Munka" (`backend/status_munka.py:17-18`); `eh_concluido` é a versão de backend, usada em `GET /tarefas-mes` (`backend/api.py:1411`) e `listar_catalogo` alimenta `GET /status-munka` (`backend/api.py:1667`).
- Filtro "Status no portal" (Lista): a chave de cada tarefa é o id resolvido, ou o texto cru se não reconhecido (`chaveStatusPortal`, `:937`). As opções são todo o catálogo (mesmo com 0 tarefas) mais os textos desconhecidos do portal, com contagem (`opcoesStatusPortal`, `:947-964`).
- Kanban: cada tarefa vai para a coluna `resolverStatus(status_munka || status)?.id`, ou `outros` (`TarefasKanbanView.vue:103-117`). Há uma coluna por item do catálogo, na ordem do catálogo, sempre exibida; a coluna "Sem status / Outros" só aparece se houver tarefas. Se o texto do portal difere do rótulo da coluna, o cartão mostra o texto cru como etiqueta (`:53`).
- Os modais de ajuste (individual e lote) e a Configuração listam `CATALOGO_STATUS` nos selects (`TarefasMesView.vue:476`, `:609`).

## Endpoints usados

| Método | Rota | Uso |
| ------ | ---- | --- |
| GET | `/tarefas-mes?mes&ano` | Tarefas do mês e totais; padrão mês atual (`backend/api.py:1338`) |
| POST | `/tarefas-mes/sincronizar` | Cria job `verificacao` e dispara `sincronizar_status_munka_task` (`:1460`) |
| POST | `/tarefas-mes/ajustar` | Um job `ajuste` por tarefa; 400 sem ids ou sem campos (`:1486`) |
| GET | `/config` | Padrões dos modais (Lista) |
| GET | `/status-munka` | Catálogo no backend (`:1667`); o frontend não o consome, usa a cópia local |

## Notas

- O Kanban é somente leitura: não há arrastar, nem ação de ajuste, nem sincronização; só filtros e link para o Munka.
- O catálogo está duplicado (TS e Python) e precisa ser mantido igual à mão; o comentário do TS diz que "espelha" o Python. Alterar os dois juntos.
- `pode_alterar` é sempre `true` e `editaveis` é igual a `total` no backend: não há bloqueio por status (`backend/api.py:1423`, `:1445`).
- Mês da tarefa: `enviado_em` com prefixo `AAAA-MM`, ou data do commit contendo `/MM/AAAA` (`backend/api.py:1352-1372`).
- `GET /tarefas-mes` pode gravar `task_id`/`task_url` no histórico ao listar, recuperando do job de envio (`backend/api.py:1378-1409`).
- Ajuste apenas de status ignora tarefas já naquele status e retorna `total_ignoradas` (`backend/api.py:1520-1540`). O front não exibe esse total.
- O ajuste só enfileira jobs; o resultado no portal aparece depois, via Fila. O campo "tipo" é texto livre (padrão "projeto").
- Sincronização automática: o beat do Celery dispara `tasks.agendar_sincronizacao_periodica` a cada 15 min (`backend/celery_app.py:32-37`), que chama `enfileirar_sincronizacao_inicial`; pula sem credenciais ou se já há job recente (`backend/api.py:2605-2629`). Exige o serviço `celery_beat`. O que a tarefa faz no portal (só leitura de status, segundo o docstring) está em `backend/celery_tasks.py:827`; o corpo completo não foi verificado.
- Marcadores do tutorial: elementos com `data-tour="..."` (alvos `target:` dos tutoriais `tarefas-mes e tarefas-kanban` em `src/config/tutorials.ts`). Não dependem de classes CSS: renomear ou reestilizar um elemento não quebra o tutorial, mas remover o `data-tour` sim.
