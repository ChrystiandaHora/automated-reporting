# Modelos (Limites de taxa por modelo)

Painel de monitoramento do consumo de requisições e tokens de cada modelo de IA, com edição dos limites.

## Rota e arquivos

- Rota: `/modelos` (`src/router/index.ts:27`).
- View: `src/views/ModelosView.vue`.
- Componentes: `TutorialModal` (`src/views/ModelosView.vue:174`). Não usa stores Pinia; chama `api.modelos.*` direto.
- Id do tutorial: `modelos` (`src/config/tutorials.ts:233`).

## Para que serve

As análises de commit usam modelos de IA com cotas (RPM, TPM e RPD). Esta tela mostra, quase em tempo real, quanto de cada cota já foi usado e permite ajustar os limites configurados. O objetivo é evitar estouro de cota (HTTP 429), conforme o tutorial.

## Seções da tela

1. Cabeçalho: título "Limites de taxa por modelo", botão de tutorial, checkbox "Auto-atualizar (3s)", botões "Resetar Métricas" e "Atualizar Agora" (`:170-189`).
2. Estado de carregamento (spinner "Carregando métricas dos modelos...") (`:191`).
3. Tabela com uma linha por modelo: Modelo (nome + id), Categoria, RPM, TPM, RPD (valor/limite, % e barra), Status e Ações (`:196-291`).
4. Modal "Configurar Limites" com três campos numéricos (`:294-319`).

## Ações do usuário

| Ação | O que acontece | Endpoint/store |
| ---- | -------------- | -------------- |
| Abrir a tela | Carrega limites e inicia polling a cada 3 s (`:154-161`) | `api.modelos.limits` |
| Desmarcar "Auto-atualizar" | O intervalo continua, mas só recarrega se `autoRefresh` for true (`:156-158`) | — |
| "Atualizar Agora" | Recarrega a lista (`carregarLimites`, `:57`) | `GET /modelos/limits` |
| "Testar" na linha | Simula 1 chamada e recarrega (`simularChamada`, `:68`) | `POST /modelos/test-call` |
| "Resetar Métricas" | `confirm()` e zera os contadores de todos os modelos (`:80`) | `POST /modelos/reset` |
| Engrenagem | Abre modal preenchido com os limites do modelo (`abrirEdicao`, `:130`) | — |
| "Salvar Limites" | Envia os 3 limites, fecha o modal e recarrega (`:143`) | `PUT /modelos/limits/{id}` |

## Dados e estado

- `modelos` (`ModelStatus[]`), `loading`, `autoRefresh`, `testingModelId` (desabilita o botão "Testar" da linha) (`:6-9`).
- `editingModel` e `editForm` (`rpm_limit`, `tpm_limit`, `rpd_limit`; padrões iniciais 10, 250000, 500) (`:16-21`).
- Os dados vêm de `rate_limiter.get_all_models_status()` no backend; o conteúdo exato de cada item além dos campos usados no template não foi verificado.

## Regras e filtros

- Cor da barra por percentual: `>= 85` vermelho, `>= 60` amarelo, abaixo verde (`classeFaixa`, `:35`). A largura é limitada a 100% (`:230`).
- Status exibido: `danger` = "Limite Crítico", `warning` = "Atenção", demais = "Operacional" (`:269`). Quem calcula o status é o backend (não verificado).
- TPM é formatado com sufixo K/M (`formatTokens`, `:47`).
- Não há filtro nem ordenação no front; a ordem é a da API.
- Erros de rede só vão para `console.error`; não há toast nem mensagem de erro na tela. Não há estado vazio: com lista vazia a tabela fica sem linhas.
- Modal: Esc fecha, Tab fica preso dentro (focus trap), foco retorna ao elemento anterior (`:90-128`). Campos: RPM min 1; TPM min 1000, passo 1000; RPD min 1.

## Endpoints usados

| Método | Rota | Uso |
| ------ | ---- | --- |
| GET | `/modelos/limits` | Lista modelos e métricas (`backend/api.py:2555`) |
| PUT | `/modelos/limits/{model_id}` | Atualiza limites; 404 se o modelo não existe (`:2561`) |
| POST | `/modelos/test-call` | Registra uma chamada simulada de 1500 tokens (`:2575`) |
| POST | `/modelos/reset` | Zera contadores de requisições e tokens (`:2582`) |

## Notas

- "Testar" não chama a IA de verdade: só registra a chamada no rate limiter e consome 1500 tokens fictícios (`backend/api.py:2578`).
- O botão "Resetar Métricas" afeta todos os modelos, não só um.
- Marcadores do tutorial: elementos com `data-tour="..."` (alvos `target:` dos tutoriais `modelos` em `src/config/tutorials.ts`). Não dependem de classes CSS: renomear ou reestilizar um elemento não quebra o tutorial, mas remover o `data-tour` sim.
- A tela de Analisar menciona esta tela para configurar RPM/TPM (`src/config/tutorials.ts:135`).
