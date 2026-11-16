# Fila de Execução

Monitor em tempo real dos jobs assíncronos (análises de IA, envios ao Munka, ajustes e sincronizações), com ações de pausar, retomar, cancelar, reenfileirar e ver logs.

## Rota e arquivos

- Rota: `/fila` (`src/router/index.ts:25`).
- View: `src/views/FilaView.vue`.
- Componentes: `TutorialModal`.
- Stores: `useFilaStore` (`src/stores/fila.ts`), `useToastStore` (`src/stores/toast.ts`).
- API direta (sem store): `api.config.obter`, `api.fila.limparMesesAnteriores`, `api.fila.verificar`, `api.fila.corrigir` (`src/api/index.ts:282-306`).
- Tutorial: id `fila` (`src/views/FilaView.vue:6`, `src/config/tutorials.ts:161`).

## Para que serve

Análises por IA e lançamentos no portal Munka rodam em workers Celery, não na hora do clique. Esta tela mostra o que está executando, o que aguarda e o que terminou ou falhou, e deixa o usuário intervir. É para onde `/analisar` e outras telas mandam o usuário depois de enfileirar algo.

## Seções da tela

1. Cabeçalho (`:3-52`): título, tutorial, selo de concorrência (`Concorrência: X análises / Y envios (N total | M Cores CPU)`) e ações globais: Retomar Pausadas, Pausar Pendentes, Reenfileirar Todas com Falha, Limpar Meses Anteriores, Atualizar. Cada botão condicional só aparece se houver jobs aplicáveis.
2. "Carregando fila..." enquanto `loading` e sem jobs (`:55`).
3. "Em Execução Agora" (`:59-179`): cartões dos jobs `running` com badge de tipo, id, data, Ver Commit, Logs (Ao Vivo), Cancelar, metadados por tipo e última linha de log. Selo "AO VIVO" e contagem de pendentes.
4. Aviso "N tarefa(s) aguardando na fila" quando nada roda mas há pendentes (`:182-187`).
5. Duas colunas (`:190-586`):
   - Esquerda "Lançamentos" (`.coluna-lancamentos`): jobs `analise` e `envio` agrupados por commit, grupos recolhíveis, cada job com status, botões e mensagens.
   - Direita "Ajustes & Sincronizações" (`.coluna-ajustes`): jobs `ajuste` e `verificacao` como cartões, com chips de campos alterados, resumo de conclusão e link para `/tarefas-mes` quando vazia.
6. Modal "Logs de Automação (Job #id)" com o texto dos logs (`:590-612`).

## Ações do usuário

| Ação | O que acontece | Endpoint/store |
| ---- | -------------- | -------------- |
| Abrir a tela | Busca jobs, busca config de concorrência e inicia polling de 3,5 s (`:871-885`) | `fetchJobs` -> `GET /fila`; `GET /config` |
| Atualizar | Recarrega com indicador de loading (`:891`) | `GET /fila` |
| Pausar Pendentes / Pausar (grupo ou job) | Pausa `pending` de tipo analise/envio; global pede `confirm` (`:725`) | `filaStore.pausarJobs` -> `POST /fila/pausar` |
| Retomar (global, grupo ou job) | Redespacha jobs `paused` (`:731`) | `filaStore.retomarJobs` -> `POST /fila/retomar` |
| Cancelar | `confirm`; marca como erro "CANCELADO" e revoga no Celery (`:982`) | `filaStore.cancelarJob` -> `POST /fila/{id}/cancel` |
| Limpar (job done/error) | Remove da lista sem confirmação (`:988`) | `filaStore.removerJob` -> `DELETE /fila/{id}` |
| Reenfileirar Todas com Falha / Falhas (grupo) | `confirm`; reenvia jobs `error` (todos ou do commit) (`:735`, `:848`) | `filaStore.reenfileirarComErros` -> `POST /fila/retry-failed` |
| Limpar Meses Anteriores | `confirm`; remove done/error anteriores ao mês atual e recarrega (`:741`) | `POST /fila/limpar-meses-anteriores` |
| Verificar / Lançamento OK / Corrigir (envio concluído) | Sem verificação ou OK: verifica; com divergência: corrige (`:1068-1100`) | `POST /fila/{id}/verificar` ou `/corrigir` |
| Logs (Ao Vivo) / Ver Logs | Abre modal e atualiza a cada 1,2 s (`:1024-1036`) | `fetchJobs(true)` -> `GET /fila` |
| Reprocessar com outro modelo | `confirm`; remove o job e enfileira nova análise (`:1135`) | `DELETE /fila/{id}` + `POST /fila/analise` |
| Re-enviar / Tentar Novamente | `confirm`; remove o job e enfileira o envio (`:1147`) | `DELETE /fila/{id}` + `POST /fila/envio` |
| Recolher/expandir grupo de commit | Alterna `gruposColapsados` (`:857`) | local |

## Dados e estado

- `filaStore.jobs`: lista completa de `FilaItem` (`src/api/index.ts:150-163`); `loading`, `error`.
- Polling duplo: a view faz `fetchJobs(true)` a cada 3500 ms (`:882`); a store tem `startPolling` a cada 3000 ms que se autodesliga sem jobs `pending/running` (`src/stores/fila.ts:176-190`). `onUnmounted` limpa só o intervalo da view (`:887`). Com o modal aberto há ainda um intervalo de 1200 ms (`:1028`).
- A store emite toast e som quando um job passa de `pending/running` para `done/error`, com deduplicação (`src/stores/fila.ts:26-85`). Respostas atrasadas são descartadas por sequência.
- Computeds: `jobsEmExecucao`, `pendingJobsCount`, `failedJobsCount`, `pausableJobsCount`, `pausedJobsCount`, `jobsLancamentos`, `jobsAjustes`, `jobsLancamentosAgrupados` (`:697-838`).
- Refs locais: `logJobSelecionado`, `concurrencyInfo`, `gruposColapsados`, `modelosSelecionados`, `jobsEmVerificacao`.

## Regras e filtros

- Estados do job: `pending` (amarelo), `paused` (cinza), `running` (azul), `done` (verde), `error` (vermelho) (`:650-656`, rótulos em `:905`).
- Pausar só vale para `pending` de tipo `analise` ou `envio` (`:702`; backend `TIPOS_PAUSAVEIS`, `backend/api.py:2154`). Job em execução termina normalmente.
- Ordenação nos grupos e em Ajustes: running, pending, depois mais recente por `criado_em`. Grupos: commits com running, depois com pending, depois pelo job mais recente (`:795-838`). Grupo com job `running` nunca fica recolhido (`:861`).
- Botão Cancelar: aparece em pending/running/paused na coluna esquerda e em pending/running na direita (`:362`, `:499`).
- "Mudar modelo" aparece só para análise com erro cujo texto contém `429`, `quota`, `limit` ou `exhausted`, ou `running` com `resultado.status === 'retrying'` (`:1123`).
- Mensagem de erro: `resultado.error`, senão a última linha de log com `ERRO` ou X vermelho, senão texto genérico (`:972`).
- Rótulos de campos de ajuste mapeiam códigos (cargo, nível, status) para nomes fixos no front (`:916-961`).
- Backend: retries automáticos de envio (até 3 tentativas) voltam o job a `pending` e gravam em `fila_logs_historico` (`backend/celery_tasks.py:494-523`).

## Endpoints usados

| Método | Rota | Uso |
| ------ | ---- | --- |
| GET | `/fila` | Lista de jobs com `commit_mensagem` e `titulo_atividade` (`backend/api.py:2316`) |
| GET | `/config` | Campo `concurrency` (queues, total, cpu_cores) (`backend/api.py:1706`) |
| POST | `/fila/pausar` | Pausa jobs pendentes (`backend/api.py:2162`) |
| POST | `/fila/retomar` | Retoma jobs pausados (`backend/api.py:2213`) |
| POST | `/fila/{id}/cancel` | Cancela job (`backend/api.py:2247`) |
| DELETE | `/fila/{id}` | Remove job da fila (`backend/api.py:2436`) |
| POST | `/fila/retry-failed` | Reenfileira jobs com erro; `commit_id` opcional (`backend/api.py:2131`) |
| POST | `/fila/limpar-meses-anteriores` | Apaga done/error de meses anteriores e o histórico de logs deles (`backend/api.py:2453`) |
| POST | `/fila/{id}/verificar` | Dispara verificação no portal (`backend/api.py:2274`) |
| POST | `/fila/{id}/corrigir` | Cria novo job `envio` de correção (`backend/api.py:2289`) |
| POST | `/fila/analise`, `/fila/envio` | Usados indiretamente em reprocessar/re-enviar (`backend/api.py:1909`, `:1945`) |

## Notas

- Marcadores do tutorial: elementos com `data-tour="..."` (alvos `target:` dos tutoriais `fila` em `src/config/tutorials.ts`). Não dependem de classes CSS: renomear ou reestilizar um elemento não quebra o tutorial, mas remover o `data-tour` sim.
- Job com `status === 'completed'` é tratado em alguns textos (`:423-429`), mas o tipo `FilaItem` e o backend só usam `done`; essa mensagem de "re-enviar" provavelmente nunca aparece para sucesso (não verificado em runtime).
- `reprocessar` e `reenviar` removem o job antes de enfileirar; se o novo enfileiramento falhar, o job original já foi perdido.
- A verificação/correção usa `alert()` em erros e o estado `jobsEmVerificacao` nunca é preenchido (apenas `verificandoJobId`), então o texto "Verificando..." não é exibido (`:691`, `:1046`).
- Logs completos por tentativa ficam em `/fila-logs` (ver `fila-logs.md`). A fila Fila e FilaLogsHistorico estão em `backend/models.py:92` e `:125`.
- Limpar um job aqui não confirma nem informa se o histórico de logs correspondente é apagado (não verificado em `remover_job_fila`: só `db.delete(job)`).
