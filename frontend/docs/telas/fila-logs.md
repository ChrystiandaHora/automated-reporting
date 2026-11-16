# Logs de Execução

Histórico de tentativas das tarefas da fila (retries, falhas finais e sucessos) para auditoria e diagnóstico, com busca, filtro e exclusão.

## Rota e arquivos

- Rota: `/fila-logs` (`src/router/index.ts:26`).
- View: `src/views/FilaLogsView.vue`.
- Componentes: `TutorialModal`.
- Stores: apenas `useToastStore` (`src/stores/toast.ts`); não usa `useFilaStore`.
- API: `api.filaLogs` (`src/api/index.ts:307-311`).
- Tutorial: id `fila-logs` (`src/views/FilaLogsView.vue:7`, `src/config/tutorials.ts:197`).

## Para que serve

Quando uma análise ou envio ao Munka falha ou é repetido, o texto completo do que o worker fez fica salvo por tentativa. Esta tela lista esses registros, permite achar um erro específico pelo conteúdo do log e limpar registros antigos. Complementa `/fila`, que só mostra o estado atual dos jobs.

## Seções da tela

1. Cabeçalho (`:4-32`): título, tutorial, contador "X de Y logs", botão "Excluir Selecionados (n)" (só com seleção) e "Atualizar".
2. Barra de filtros (`FiltersBar`, `:35-106`): busca textual, pílulas de status (Todos, Retries, Erros, Sucesso, com contagens) e checkbox "Selecionar Todos" (só com resultados).
3. Estados: "Carregando histórico de logs..." (`:109`); vazio, com mensagem diferente se há filtro ativo (`:114-116`).
4. Lista de logs (`:119-237`), um cartão por registro:
   - Checkbox, badge de tipo (Análise AI / Envio Portal), badge de status com tentativa, data relativa, link com SHA curto do commit, botões Expandir/Ocultar e Excluir.
   - Corpo: título da atividade, mensagem do commit e, se recolhido, a última linha do log (clicável).
   - Expandido: terminal com todas as linhas e botão "Copiar".

## Ações do usuário

| Ação | O que acontece | Endpoint/store |
| ---- | -------------- | -------------- |
| Abrir a tela | Carrega todos os logs (`:289-291`) | `api.filaLogs.listar` -> `GET /fila-logs` |
| Atualizar | Recarrega (`:278`) | `GET /fila-logs` |
| Buscar / filtrar por status | Atualiza refs locais; filtragem no cliente (`:293-310`) | local |
| Selecionar log / Selecionar Todos | Altera `selecionados`; "todos" atua só nos visíveis (`:324-352`) | local |
| Expandir/Ocultar | Alterna `expandidos` (`:320`) | local |
| Copiar | Copia as linhas unidas por `\n` e mostra toast (`:401-408`) | Clipboard API |
| Excluir (individual) | `confirm`; remove do servidor e da lista (`:354-364`) | `DELETE /fila-logs/{id}` |
| Excluir Selecionados | `confirm`; remoção em lote (`:366-379`) | `POST /fila-logs/delete-multiple` |
| Clicar no SHA | Navega para `/commits/<sha completo>` (`:162-169`) | router |

## Dados e estado

- `logs: FilaLogItem[]` (`src/api/index.ts:165-176`), `loading`, `filtroTexto`, `filtroStatus` (`todos|retrying|error|done`), `selecionados: number[]`, `expandidos: Record<number, boolean>` (`:249-254`).
- `logsFiltrados` e `todosSelecionados` são computeds. Não há polling: a lista só muda ao abrir, ao clicar em Atualizar ou ao excluir.
- Dados de origem: tabela `fila_logs_historico` (`backend/models.py:125-141`), campos `fila_id`, `tipo`, `commit_id`, `atividade_idx`, `tentativa`, `status`, `logs` (JSON), `criado_em`. O endpoint acrescenta `commit_mensagem` e `titulo_atividade` (`backend/api.py:2481-2522`).

## Regras e filtros

- Status do log: `retrying` (borda amarela, "Retry"), `error` ("Falha Final") e `done` ("Sucesso"), sempre com "(Tentativa N)" (`:381-393`).
- Busca (case-insensitive) casa com mensagem do commit, título da atividade, SHA e qualquer linha de log (`:293-310`); combina com o filtro de status.
- Ordenação: a do backend, por `criado_em` decrescente (`backend/api.py:2481`); a tela não reordena.
- Data: relativa ("Agora mesmo", "Há N min", "Há Nh", depois dd/mm hh:mm); a data completa aparece no `title` (`:410-435`).
- Realce no terminal: linhas com X vermelho, `ERRO` ou `Falha` em vermelho; com aviso ou pausa em amarelo (`:233`).
- Log sem conteúdo mostra "(Sem conteúdo de log registrado)".
- Falha de carga ou exclusão gera toast de erro; a lista não mostra estado de erro próprio.

## Endpoints usados

| Método | Rota | Uso |
| ------ | ---- | --- |
| GET | `/fila-logs` | Lista todos os registros de histórico (`backend/api.py:2481`) |
| DELETE | `/fila-logs/{id}` | Exclui um registro, 404 se não existir (`backend/api.py:2525`) |
| POST | `/fila-logs/delete-multiple` | Exclui vários; corpo `{ids}` (`backend/api.py:2534`) |

## Notas

- Marcadores do tutorial: elementos com `data-tour="..."` (alvos `target:` dos tutoriais `fila-logs` em `src/config/tutorials.ts`). Não dependem de classes CSS: renomear ou reestilizar um elemento não quebra o tutorial, mas remover o `data-tour` sim.
- Os registros são gerados pelos workers em `backend/celery_tasks.py` (por exemplo `:136`, `:359`, `:469`, `:509`, `:535`): análise concluída grava um sucesso; envio grava uma linha por tentativa. Tipos `ajuste`/`verificacao` também gravam histórico em algumas tasks (`:654`, `:1078`), mas o tipo no front é restrito a `analise|envio` (não verificado como são exibidos).
- Todos os logs são carregados de uma vez, sem paginação; a lista pode ficar pesada com muito histórico.
- `POST /fila/limpar-meses-anteriores` apaga também os registros de histórico dos jobs removidos (`backend/api.py:2464`), então logs aqui podem desaparecer após a limpeza feita em `/fila`.
- O "Copiar" não faz nada se `navigator.clipboard` não existir (sem aviso).
- A exclusão remove o log apenas do histórico; o job na fila (`fila_id`) não é afetado.
