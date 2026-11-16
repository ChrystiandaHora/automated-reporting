# Importar Commits do GitLab

Tela para importar commits em lote colando URLs completas do GitLab e escolhendo qual conta usar.

## Rota e arquivos

- Rota: `/importar` — `src/router/index.ts:23`.
- View: `src/views/ImportarCommitsView.vue`.
- Componentes: `TutorialModal` (`screenId="importar"`, linha 12).
- Stores: `useToastStore` (`src/stores/toast.ts`). Não usa a store de commits: chama `api.gitAccounts.listar()` e `api.commits.importar()` diretamente.
- Tutorial: id `importar` em `src/config/tutorials.ts:89`.

## Para que serve

É o ponto de entrada de dados do sistema: traz mensagem, metadados e diff dos commits do GitLab para o banco local, para depois serem analisados pela IA. O usuário cola várias URLs, vê uma pré-visualização validada em tempo real e importa tudo de uma vez.

## Seções da tela

1. Cabeçalho: botão "Voltar aos Commits", título, tutorial, subtítulo e link "Gerenciar Contas GitLab" (`/config`) (`:4-25`).
2. Alerta global de erro (`erroGlobal`, `:28`).
3. Passo 1 — Seleção da conta GitLab: cartões tipo radio (`:33-119`): "Detecção Automática (SMART MATCH)" e uma por conta cadastrada, com selo PADRÃO e token mascarado. Sem contas: aviso e botão para `/config`.
4. Passo 2 — Informe os Commits: textarea de URLs, contador de identificados e painel "Pré-Visualização Inteligente" (SHA, projeto, domínio ou "Formato Inválido") (`:122-191`).
5. Passo 3 — Barra de ação "Pronto para importar N commits" com a instância escolhida e botão de importar (`:194-214`).
6. Progresso e relatório: barra, contagem de importados / já existiam / falhas, lista por item (NOVO, EXISTENTE, ERRO) e botões pós-importação (`:217-279`).

## Ações do usuário

| Ação | O que acontece | Endpoint/store |
| ---- | -------------- | -------------- |
| Abrir a tela | Carrega as contas e pré-seleciona a padrão (`carregarContas`, `:337`) | `GET /git-accounts` |
| Escolher conta ou Detecção Automática | Define `selectedAccountId` (0 = automática) | local |
| Colar/editar URLs | `parsedItems` recalcula validação em tempo real | local |
| "Limpar Texto" | Zera texto, relatório e progresso (`:428`) | local |
| "Importar N Commit(s)" | Importa um a um, em sequência (`executarImportacao`, `:434`) | `POST /commits/importar` |
| "Prosseguir para Análise com IA" | Navega para `/analisar` | router |
| "Ver Todos os Commits" | Navega para `/commits` | router |
| "Gerenciar Contas GitLab" | Navega para `/config` | router |

## Dados e estado

- `contas` (`GitAccount[]`), `loadingContas`, `selectedAccountId` (`:293-295`).
- `urlsTexto`, `importando`, `progressoAtual`, `erroGlobal`, `relatorioExecucao` (`:297-309`).
- `parsedItems` (`:367`) é um computed que analisa cada linha; `parsedItemsValidos` filtra os válidos; `totalSucessos/JaExistiam/Falhas` derivam do relatório; `percentualProgresso` alimenta a barra.

## Regras e filtros

- Linha válida: regex `https?://dominio/projeto/(-/)?commit/<sha 6-64 hex>` (`:374`). Alternativa: linha contendo um hash de 40 hex, sem projeto nem domínio (`:386`). Qualquer outra é "Formato Inválido" e é ignorada na importação.
- Conta: se `selectedAccountId !== 0`, envia `git_account_id`; se 0, não envia e o backend detecta pelo domínio (`:449-451`). Pré-seleção: conta com `padrao`, senão a primeira, senão 0 (`:343-350`).
- Payload: `commit_hash` recebe a linha inteira (`item.raw`), não só o SHA (`:445`).
- Importação sequencial; um erro não interrompe os demais. `res.ja_existia` vira status "existente".
- Botão de importar desabilitado se `importando` ou sem itens válidos; textarea desabilitada durante a importação.
- Ao final: toast de erro se houve falhas, senão de sucesso (`:485-489`).
- Estados: carregando contas (`:43`), sem contas (`:48`), erro ao carregar contas vira `erroGlobal`.

## Endpoints usados

| Método | Rota | Uso |
| ------ | ---- | --- |
| GET | `/git-accounts` | Lista contas GitLab com token mascarado (`backend/api.py:1764`) |
| POST | `/commits/importar` | Busca metadados e diff no GitLab e grava o commit; retorna `{id, ja_existia}`; 400 se o GitLab falhar (`backend/api.py:519`) |

## Notas

- No backend, com `git_account_id` o token e a URL vêm da conta; a URL do commit colada também define URL/projeto/SHA, e sem conta o backend procura uma conta cujo `url` combine com o domínio da URL (`backend/api.py:535-570`). O comportamento exato quando nenhuma conta combina: não verificado.
- O texto do tutorial fala em "barra de progresso em tempo real": é de fato `progressoAtual/total` atualizado a cada commit concluído.
- Linhas só com hash de 40 hex passam na validação do frontend, mas dependem de o backend conseguir resolver projeto/URL: não verificado.
- A `CommitsView` ainda contém um modal de importação (`showImport`), mas ele não é aberto por nenhum botão; o fluxo real é esta tela (ver `commits.md`).
- Marcadores do tutorial: elementos com `data-tour="..."` (alvos `target:` dos tutoriais `importar` em `src/config/tutorials.ts`). Não dependem de classes CSS: renomear ou reestilizar um elemento não quebra o tutorial, mas remover o `data-tour` sim.
- Depende de `/config` para cadastrar contas (tela Configurações) e leva a `/analisar` após importar.
