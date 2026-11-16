# Configuração

Tela de ajustes do sistema: contas GitLab, valores padrão de faturamento no Munka, informações de concorrência e backup.

## Rota e arquivos

- Rota: `/config` (`src/router/index.ts:38`).
- View: `src/views/ConfigView.vue`.
- Componentes/stores: `TutorialModal` (`:6`), `useToastStore` (`:310`); catálogo `CATALOGO_STATUS` de `src/config/statusMunka.ts` (`:297`).
- Id do tutorial: `config` (`src/config/tutorials.ts:363`).

## Para que serve

Centraliza o que o sistema precisa para falar com o GitLab e o Munka: cadastro de várias contas GitLab, valores padrão (cargo, nível, produto, projeto, status inicial, horários) usados nos lançamentos, e backup dos dados. Também exibe, somente para leitura, o dimensionamento dos workers.

## Seções da tela

1. Cabeçalho com título, tutorial e botão "Salvar" (`:3-12`).
2. Barra de status: Gemini, Munka, GitLab (nº de contas) e Concorrência (`:17-34`).
3. "Contas e Instâncias do GitLab": botão de cadastro e tabela Nome / URL Base / Token mascarado / Padrão / Conexão / Ações (`:39-116`).
4. "Munka - Faturamento Padrão": cargo, nível, responsável, produto, projeto, status inicial, data/hora de início e de fim (`:118-148`).
5. "Processamento Assíncrono" (só se `cfg.concurrency` existir): cores, capacidade total, pool dinâmico e workers por fila (`:150-177`).
6. "Segurança & Backup Automático": criar backup, ping do Munka, resultado do ping e lista de arquivos (`:179-214`).
7. Mensagem de resultado do "Salvar" (`:217`) e modal de conta GitLab (`:220-287`).

## Ações do usuário

| Ação | O que acontece | Endpoint/store |
| ---- | -------------- | -------------- |
| Abrir a tela | Carrega config, backups e contas GitLab (`:513-531`) | `GET /config`, `/backup/listar`, `/git-accounts` |
| "Salvar" | Envia os campos do formulário e recarrega a config (`salvar`, `:533`) | `POST /config` |
| Cadastrar/editar conta | Modal; cria ou atualiza e recarrega a lista (`:398`) | `POST/PUT /git-accounts` |
| "Definir Padrão" | Atualiza `padrao: true` da conta (`:428`) | `PUT /git-accounts/{id}` |
| Excluir conta | `confirm()` e remove (`:438`) | `DELETE /git-accounts/{id}` |
| "Testar Conexão" | Valida o token; mostra usuário ou erro na linha e em toast (`:449`) | `POST /git-accounts/{id}/testar` |
| "Criar Backup JSON + SQL Agora" | Gera backup, toast com arquivo e recarrega a lista (`:486`) | `POST /backup/criar` |
| "Testar Conectividade (Ping Munka)" | Exibe resultado abaixo dos botões (`:500`) | `GET /ping-munka` |

## Dados e estado

- `cfg` (resposta de `/config`), `form` (campos editáveis), `loading`, `saving`, `msg`/`ok` (`:311-331`).
- Contas: `gitAccounts`, `gitForm`, `showGitModal`, `mostrarToken`, `salvandoGit`, `gitModalErro`, `testandoGitId`, `testeResultados` (`:334-355`).
- Backup/ping: `backupsList`, `backupLoading`, `pingLoading`, `pingResult` (`:472-475`).

## Regras e filtros

- Valores padrão quando a API não devolve: cargo 9, nível 3, produto "[DESENV] MUNKA", projeto "MUNKA Multicontrato", status inicial 17, horários 08:00 / 18:00 (`:519-525`).
- O select "Status Inicial Padrão" lista `CATALOGO_STATUS` (`:142`).
- Em `salvar`, campos cujo nome contém `key`, `pass` ou `token` só são enviados se preenchidos e diferentes de `***`; os demais sempre (`:538-544`). O backend repete essa regra (`backend/api.py:1753-1758`).
- "Salvar" grava no `.env` e no ambiente do processo (`backend/api.py:1716-1760`).
- No modal de conta: ao editar, o token vem como `***` (mantém o atual); "Salvar Conta" fica desabilitado sem URL ou, em conta nova, sem token (`:279`). Primeira conta nasce como padrão (`:374`).
- No backend, marcar uma conta como padrão desmarca as outras; ao excluir a padrão, a primeira restante vira padrão (`backend/api.py:1785-1880`).
- Estados: "Carregando..." geral; "Carregando contas GitLab..."; "Nenhuma conta GitLab cadastrada..." (`:54-57`). Erros de carga de contas/backups só vão a `console.error`.

## Endpoints usados

| Método | Rota | Uso |
| ------ | ---- | --- |
| GET | `/config` | Config com segredos mascarados e `concurrency` (`backend/api.py:1673`) |
| POST | `/config` | Salva no `.env` (`backend/api.py:1716`) |
| GET/POST | `/git-accounts` | Lista e cria contas (`:1764`, `:1785`) |
| PUT/DELETE | `/git-accounts/{id}` | Atualiza e remove (`:1825`, `:1862`) |
| POST | `/git-accounts/{id}/testar` | Testa conexão (`:1883`) |
| POST | `/backup/criar` | Gera backup JSON + SQL (`:2660`) |
| GET | `/backup/listar` | Lista arquivos de backup (`:2670`) |
| GET | `/ping-munka` | Ping rápido ao portal (`:2687`) |

## Notas

- O formulário não tem campos para chave Gemini, usuário/senha do Munka nem token GitLab legado: esses ficam em `form` mas sem input no template. Só `munka_user` e `gitlab_url` são copiados da config para o `form` (`:516-517`), então o `.env` é o lugar dessas credenciais (não verificado como são definidas).
- O status "Gemini/Munka Conectado" só indica que há credencial configurada, não testa a conexão (`backend/api.py:1702-1706`). O status "GitLab" da barra usa o número de contas cadastradas, não `cfg.status.gitlab`.
- O "Status Inicial Padrão" é reaproveitado como valor inicial nos modais de ajuste da tela de Tarefas do Mês (ver `tarefas-mes.md`).
- A conta GitLab padrão é usada na importação de commits (tela `/importar`; detalhes não verificados aqui).
- Marcadores do tutorial: elementos com `data-tour="..."` (alvos `target:` dos tutoriais `config` em `src/config/tutorials.ts`). Não dependem de classes CSS: renomear ou reestilizar um elemento não quebra o tutorial, mas remover o `data-tour` sim.
- A lista de backups tipa `criado_em`, mas o backend devolve `modificado_em` (`:473`; `backend/api.py:2679`); a tela só exibe nome e tamanho.
