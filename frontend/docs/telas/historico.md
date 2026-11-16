# Histórico de Envios

Lista as atividades já enviadas ao portal Munka, agrupadas por dia, com busca, filtro, re-envio e exclusão.

## Rota e arquivos

- Rota: `/historico` (`src/router/index.ts:28`).
- View: `src/views/HistoryView.vue`.
- Componentes: `TutorialModal` (`:6`). Stores: `useToastStore` e `useFilaStore` (`:205-206`).
- Id do tutorial: `historico` (`src/config/tutorials.ts:269`).

## Para que serve

Cada atividade enviada ao Munka vira um registro de histórico. A tela permite conferir o que foi lançado, achar atividades sem data de fim, reenviar uma atividade ou apagar o registro. Quem é novo no projeto pode usá-la como auditoria rápida dos lançamentos.

## Seções da tela

1. Cabeçalho: título, tutorial, contador de atividades e botão "Atualizar" (`:3-15`).
2. Estados: "Carregando..." (`:17`) e vazio "Nenhuma atividade enviada ainda." (`:19`).
3. Barra de filtros: campo de busca e botões segmentados Todas / Concluídas / Sem Data Fim, com contagens (`:25-75`).
4. Estado "sem resultados" com botão "Limpar Filtros" (`:78`).
5. Grupos por dia: cabeçalho "23 Jun, 2026 - N atividades" e linhas com avatar do autor, título, badges (código, HPA, status), mensagem do commit, "Enviado há X" e ações (`:86-178`).
6. Modal "Confirmar Exclusão" (`:182-192`).

## Ações do usuário

| Ação | O que acontece | Endpoint/store |
| ---- | -------------- | -------------- |
| Abrir a tela | Carrega e repete a cada 30 s em modo silencioso, sem spinner (`:317-322`) | `GET /historico` |
| "Atualizar" | Recarrega com spinner (`:11`) | `api.historico.listar` |
| Buscar / filtrar | Filtragem local (`itemsFiltrados`, `:219`) | — |
| Clicar no SHA | Navega para `/commits/:sha` (`:143`) | router |
| "Re-enviar" | `confirm()`, busca a análise, acha a atividade pelo título e enfileira o envio (`:295`) | `api.analise.obter`, `filaStore.enfileirarEnvio` |
| Excluir (ícone) | Abre modal; ao confirmar remove o registro e tira da lista local (`:509`) | `DELETE /historico/{id}` |

## Dados e estado

- `items` (`HistoricoItem[]`), `loading`, `termoBusca`, `filtroStatus` (`'todos' | 'concluidas' | 'sem_data'`), `itemParaDeletar`, `exibindoModalConfirmacao` (`:203-252`).
- Computeds: `totalConcluidas`, `totalSemDataFim`, `itemsFiltrados`, `historicoAgrupado` (`:211-240`, `:471`).

## Regras e filtros

- "Sem Data Fim" = `tem_data_fim === false` ou `status` contendo "Sem Data Fim" ou "Incompleta"; "Concluídas" é o complemento (`:211-217`). O rótulo "Concluídas" aqui significa apenas "com data fim", não status do portal.
- Busca (sem diferenciar maiúsculas) em título, código, id do commit, autor e mensagem do commit (`:228-237`).
- Data de agrupamento, em ordem de prioridade: `commit_data_autor`, `commit_data` (DD/MM/AAAA), `enviado_em`, senão "Outras datas" (`:355-389`).
- Ordenação: itens do grupo e os grupos por tempo decrescente (mais recente primeiro) (`:483-491`).
- Badge de status: laranja para sem data fim/incompleta, verde caso contrário; texto "Sem Data Fim" quando `tem_data_fim === false` (`:123-125`).
- Erro ao carregar não é tratado (sem `catch`); erro de exclusão e de re-envio geram toast (`:311`, `:515`).

## Endpoints usados

| Método | Rota | Uso |
| ------ | ---- | --- |
| GET | `/historico` | Lista com junção em `Commit`, mais recentes primeiro (`backend/api.py:1240`) |
| DELETE | `/historico/{item_id}` | Remove o registro; 404 se não existe (`backend/api.py:1288`) |
| GET | `/commits/{sha}/analise` | Busca a análise para o re-envio, via `api.analise.obter` (`backend/api.py:839`) |
| POST | `/fila/envio` | Enfileira o envio, via `filaStore.enfileirarEnvio` (`backend/api.py:1945`) |

## Notas

- O re-envio localiza a atividade pelo título exato; se o título mudou na análise, mostra erro "não encontrada" (`:305-307`).
- Excluir apaga apenas o registro de histórico; não há evidência no código de que isso remova a tarefa no Munka (não verificado).
- A data do commit vem de `Date:` no `diff_raw`, com fallback para `importado_em` (`backend/api.py:1253-1259`).
- No re-envio com sucesso aparecem dois toasts: um do store (`src/stores/fila.ts:129`) e outro da view (`:310`).
- A tela de Tarefas do Mês lê os mesmos registros (`Historico`) para o mês escolhido.
- Marcadores do tutorial: elementos com `data-tour="..."` (alvos `target:` dos tutoriais `historico` em `src/config/tutorials.ts`). Não dependem de classes CSS: renomear ou reestilizar um elemento não quebra o tutorial, mas remover o `data-tour` sim.
