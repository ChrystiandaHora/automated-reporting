# Detalhe do Commit

Tela de um único commit: metadados editáveis, atividades identificadas pela IA (editáveis, com pré-visualização de evidência) e envio ao Munka.

## Rota e arquivos

- Rota: `/commits/:sha` — `src/router/index.ts:22`. O `sha` vem de `route.params.sha` (`src/views/CommitDetailView.vue:318`), lido uma vez.
- View: `src/views/CommitDetailView.vue`.
- Componentes: `TutorialModal` (`screenId="commit-detail"`, linha 7).
- Stores: `useAnaliseStore` (`src/stores/commits.ts`) e `useFilaStore`; `api` direto para o commit.
- Tutorial: id `commit-detail` em `src/config/tutorials.ts:399`.

## Para que serve

Mostra o ciclo de um commit (importado, analisado por IA, faturado) e deixa o usuário revisar e corrigir cada atividade gerada pela IA antes de enviá-la ao portal Munka. Também permite ver o diff, por arquivo ou completo.

## Seções da tela

1. Cabeçalho: "← Voltar" (`$router.back()`), título (mensagem do commit ou SHA de 8 caracteres) e tutorial (`:3-9`).
2. "Carregando..." enquanto busca o commit (`:11`).
3. Linha "storytelling" com 3 etapas: Importado, Análise AI, Faturamento (com contagens e horas) (`:16-52`).
4. Barra de metadados (`.meta-bar`): SHA (12 caracteres), Data, Projeto, Autor e botão de editar; em edição, inputs de Data, Projeto, Autor, Mensagem com Salvar/Cancelar (`:55-92`).
5. "Análise Gemini": botões "Analisar/Re-analisar com AI" (link para `/analisar?commit=<sha>`), "Salvar edições", "Enviar Selecionadas (N)", "Enviar Todas ao Portal" (`:95-113`).
6. Complexidade Global (textarea) e um card por atividade (`:122-`): checkbox, etapa, código · HPA, título, selo (Enviada / Sem Data Fim / Pendente) e botão Enviar/Re-enviar. Abas "Formulário" (título, descrição, justificativa, categoria, código, HPA, complexidade, arquivos afetados com diff inline) e "Visualizar Evidência" (iframe com HTML, Copiar HTML, Atualizar).
7. Sem análise: "Nenhuma análise disponível. Clique em 'Analisar com AI'." (`:283`).
8. "Diff Completo do Commit", recolhido por padrão (`showCommitDiff`) (`:288-303`).

## Ações do usuário

| Ação | O que acontece | Endpoint/store |
| ---- | -------------- | -------------- |
| Abrir a tela | Carrega commit, análise e checa `data_fim`; agenda checagem a cada 30 s (`:614`) | `GET /commits/{sha}`, `GET /commits/{sha}/analise`, `GET /commits/{sha}/check-data-fim` |
| Editar / Salvar metadados | Envia data, projeto, autor, mensagem e atualiza localmente (`salvarMeta`, `:480`) | `PATCH /commits/{sha}` |
| Editar campos da atividade | Altera o estado local da análise; mudar código ou complexidade recalcula HPA (`recalcularHpa`, `:584`) | local |
| "Salvar edições" | Grava atividades e complexidade global, recarrega o commit, `alert` (`salvar`, `:635`) | `PUT /commits/{sha}/atividades` |
| "Enviar ao Portal" / "Re-enviar" (por atividade) | Salva edições e enfileira o envio da atividade (`enviarUma`, `:643`) | `PUT .../atividades`, `POST /fila/envio` |
| "Enviar Selecionadas" | Salva, enfileira cada índice marcado e vai para `/fila` se algum teve sucesso (`:658`) | `PUT`, `POST /fila/envio` |
| "Enviar Todas ao Portal" | Salva e enfileira as não enviadas; se todas enviadas, `confirm()` para reenviar tudo; vai para `/fila` (`:686`) | `PUT`, `POST /fila/envio` |
| Aba "Visualizar Evidência" / Atualizar | Gera o HTML de evidência da atividade (`carregarPreview`, `:434`) | `POST /commits/{sha}/preview-evidencia` |
| "Copiar HTML" | Copia o HTML ao clipboard (`:419`) | clipboard |
| "Visualizar Alterações" (por arquivo) | Extrai do `diff_raw` o trecho do arquivo e colore +/- (`:379-417`) | local |
| "Analisar com AI" | Navega para `/analisar?commit=<sha>` | router |

## Dados e estado

- `commit` (resposta de `GET /commits/{sha}`, tipado `any`) e `loadingCommit`.
- `analiseStore.analise` (atividades, `complexidade_global`), `.analisando`, `.error`; `fetchAnalise` preenche `complexidade` ausente com "Média" se o código começa por 57-61, senão "Baixa" (`src/stores/commits.ts:62-69`).
- Locais: `selecionadas` (índices), `enviandoIndividual`, `enviandoAtividade`, `activeTabs`, `previews`, `loadingPreviews`, `statusCopia`, `exibindoDiff`, `editandoMeta`, `metaEditavel`, `showCommitDiff`.
- Etapas: Análise ativa se `commit.analisado`; Faturamento ativo se há `atividades_enviadas > 0`; completa se enviadas == total e total > 0 (`:337-342`).

## Regras e filtros

- Checkbox da atividade fica desabilitado se `atv.enviado`.
- Selo: Enviada (`enviado` e não `data_fim_missing`), Sem Data Fim (enviada, mas sem data fim) ou Pendente. Em ambos os casos "enviada" o botão vira "Re-enviar".
- HPA é recalculado por tabela fixa no frontend (código x complexidade) em `obterHpaPorCodigoEComplexidade` (`:493`); códigos fora da tabela mantêm o HPA digitado.
- Botões de ação ficam desabilitados durante análise ou envio; "Enviar Selecionadas" exige ao menos uma marcada.
- A checagem de `data_fim` casa atividades por **título** (`:595-612`), atualizando `enviado` e `data_fim_missing` localmente.
- Erro de preview mostra mensagem com "Tentar Novamente". Diff sem trecho: "Sem alterações ou arquivo não encontrado no diff."

## Endpoints usados

| Método | Rota | Uso |
| ------ | ---- | --- |
| GET | `/commits/{sha}` | Dados do commit incluindo `diff_raw` (`backend/api.py:656`) |
| PATCH | `/commits/{sha}` | Edita data, projeto, autor, mensagem (`backend/api.py:799`) |
| GET | `/commits/{sha}/analise` | Análise salva; 404 tratado como "sem análise" (`backend/api.py:839`) |
| PUT | `/commits/{sha}/atividades` | Sobrescreve atividades e complexidade global (`backend/api.py:918`) |
| GET | `/commits/{sha}/check-data-fim` | Status de envio/data fim por atividade (`backend/api.py:722`) |
| POST | `/commits/{sha}/preview-evidencia` | HTML de evidência (`backend/api.py:951`) |
| POST | `/fila/envio` | Enfileira envio de uma atividade (`backend/api.py:1945`) |

## Notas

- O envio é sempre assíncrono pela fila (`POST /fila/envio`); `api.enviar` (`POST /commits/{sha}/enviar`, síncrono) não é usado aqui.
- A análise em si não roda nesta tela: o botão leva a `/analisar`. `analiseStore.analisar` não é chamado aqui.
- Há `alert()`/`confirm()` nativos (salvar, erro de metadados, reenviar tudo).
- O `sha` não reage a mudança de rota (lido uma vez sem `watch`); navegar de um commit a outro reutilizando o componente: não verificado.
- A tabela de HPA duplica regra do backend; se divergirem, o valor salvo é o do frontend (comparação com o backend: não verificado).
- Marcadores do tutorial: elementos com `data-tour="..."` (alvos `target:` dos tutoriais `commit-detail` em `src/config/tutorials.ts`). Não dependem de classes CSS: renomear ou reestilizar um elemento não quebra o tutorial, mas remover o `data-tour` sim.
