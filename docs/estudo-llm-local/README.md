# Nexus 2.0 — Estudo de classificação local de commits

Estado em **17/11/2026**. Este documento é o ponto de retomada do estudo: o que foi decidido,
como a estrutura roda, o que cada teste mostrou e qual é o próximo passo.

## Objetivo

Classificar os diffs de commit em códigos do Catálogo de Serviços **localmente**, sem custo de API
e sem enviar código para fora, com a mesma qualidade (ou melhor) do Gemini usado hoje.

Decisões já tomadas:

- **O Gemini continua** como alternativa. Máquina fraca, sem GPU ou com falha local → Gemini.
- **Tudo roda em Docker**, usando no máximo **80%** dos recursos da máquina.
- **O HPA é calculado pelo código**, a partir da tabela do catálogo. O modelo só escolhe o código.
- **O diff decide** a classificação; a mensagem do commit é só contexto auxiliar.
- **Meta:** ≥95% de acerto nos commits que o sistema aprova sozinho. O que ele não souber, por
  falta de base aprovada, é **sinalizado para revisão** com o motivo.

## Infraestrutura local

### Máquina de referência

| Recurso | Total | Teto de 80% |
|---|---|---|
| CPU | Ryzen 7 5700X, 16 threads | 12,8 CPUs |
| GPU | AMD RX 9060 XT (RDNA4, gfx1200), 16 GB VRAM | ~13 GB (3,2 GB reservados) |
| RAM | 15 GB + 15,9 GB de swap | 12 GB no container do Ollama |

### Ajustes feitos na máquina (fora do repositório)

- **Docker nativo movido para o `/home`.** `/var/lib/docker` e `/var/lib/containerd` são *bind mounts*
  de `/home/docker-data` (linhas no `/etc/fstab`). A raiz tem só 32 GB e lotou no download do modelo.
  Script: [`llm-local/mover-docker-para-home.sh`](../../llm-local/mover-docker-para-home.sh).
- **Swap reativado.** A partição `nvme1n1p3` (15,9 GB) estava comentada no `/etc/fstab`. Sem swap, a
  máquina **congelou** durante um teste (o log mostrou `Under memory pressure` e nenhum erro de GPU).
- **Dois Dockers:**
  - o **Docker Desktop** roda o Nexus, mas fica numa VM e não enxerga a GPU;
  - o **Docker nativo** (`docker --context default`) roda o Ollama com a GPU.
  Feche o Docker Desktop durante os testes: a VM dele ocupa ~4 GB de RAM.

### Serviços (pasta [`llm-local/`](../../llm-local/))

| Arquivo | O que sobe | Recursos |
|---|---|---|
| `compose.ollama.yml` | Ollama ROCm, porta só em `127.0.0.1:11434` | GPU, 12,8 CPUs, 12 GB RAM, 1 requisição por vez |
| `compose.benchmark.yml` | teste dos modelos de linguagem | 1 CPU, 1 GB, rede interna do Ollama |
| `compose.classificador.yml` | classificador treinado (scikit-learn) | 2 CPUs, 2 GB, **sem rede** |

Dados: o teste lê **uma cópia** do banco em `llm-local/dados/nexus.db` (fora do Git), sempre em
modo somente leitura. O banco real do Nexus nunca é tocado.

### Comandos

```bash
# 1. Ollama (Docker nativo, GPU)
docker --context default compose -f llm-local/compose.ollama.yml up -d

# 2. Atualizar a cópia do banco (precisa do Docker Desktop aberto)
docker run --rm -v automated-reporting_munka_data:/data -v "$PWD/llm-local/dados:/out" \
  --user 1000:1000 python:3.12-slim python -c "import sqlite3; \
  s=sqlite3.connect('file:/data/nexus.db?mode=ro',uri=True); d=sqlite3.connect('/out/nexus.db'); \
  s.backup(d); d.execute('PRAGMA journal_mode=DELETE'); d.close()"

# 3. Modelo de linguagem com exemplos aprovados (30 commits de teste fixos)
MODELOS=qwen3:14b N_COMMITS=30 N_EXEMPLOS=3 \
  docker --context default compose -f llm-local/compose.benchmark.yml run --rm --build benchmark

# 4. Referência sem IA (copia o commit aprovado mais parecido)
MODELOS=knn N_COMMITS=30 docker --context default compose -f llm-local/compose.benchmark.yml run --rm --build benchmark

# 5. Classificador por arquivo (validação cruzada nos 160 commits aprovados)
docker --context default compose -f llm-local/compose.classificador.yml run --rm --build \
  classificador /app/classificador/por_arquivo.py avaliar
```

Os resultados vão para esta pasta (`resumo-*.md`, `resultados-*.json`, `classificador-*-avaliacao.json`).

## Base de treino: tarefas aprovadas

O gabarito são as **tarefas lançadas antes de novembro** (tabela `historico`), todas aprovadas pelo
supervisor.

| Dado | Valor |
|---|---|
| Tarefas aprovadas | 427, em **160 commits** (todos com diff no banco) |
| Códigos distintos usados | **26** (de 106 do catálogo) |
| Mais comuns | 21e (71), 22a (57), 21d (54), 21b (54), 21a (42), 22b (23), 62b (21) |
| Commits com o mesmo código aprovado mais de uma vez | 38 de 160 (escopo "por evento") |
| Tarefas que casam com uma atividade da análise (mesmo título) | 427 de 427, todas com a lista de arquivos |
| Arquivos que pertencem a uma única tarefa | 92% |

Detalhes do sorteio:

- **Teste dos modelos de linguagem:** 30 commits sorteados com `SEMENTE=7`, entre os diffs de até
  24 mil caracteres. Os outros 67 (ou 130, com `INCLUIR_GRANDES=1`) formam o banco de exemplos.
  Um commit de teste **nunca** vira exemplo.
- **Classificador:** validação cruzada em 10 partes, separando sempre por commit.

## Resultados

### Linha do tempo

| Rodada | O que mudou | Melhor resultado |
|---|---|---|
| 1 | qwen2.5-coder 7B/14B, prompt reduzido, gabarito Gemini | 5% de acerto de código; códigos malformados (`[21a]`, `n/a`, hash) |
| 2 | código travado na lista do catálogo + HPA pela tabela | 10% de código, 8,7 h de erro de HPA (qwen3:14b) |
| 3 | gabarito = tarefas aprovadas + 3–6 exemplos aprovados por commit | **57% de código, 72% de serviço, 1,6 h de HPA (qwen3:14b)** |
| — | classificador por commit (CPU) | 11% de commits exatos |
| — | classificador por arquivo (CPU) | 42% dos arquivos, 19% de commits exatos, 3,2 h de HPA |

### Comparação atual (30 commits aprovados de teste)

| Método | Acerto de código | Acerto de serviço | Erro médio de HPA | s/diff |
|---|---|---|---|---|
| Cópia do aprovado mais parecido, sem IA | 46% | 64% | 2,4 h | 0 |
| gemma3:12b + 3 exemplos | 37% | 52% | 1,8 h | 26 |
| gemma3:12b + 6 exemplos | 45% | 57% | 1,7 h | 25 |
| **qwen3:14b + 3 exemplos** | **57%** | **72%** | **1,6 h** | 32 |

O classificador por arquivo foi medido de outra forma (validação cruzada nos 160 commits) e não entra
nesta tabela.

Como ler as métricas:

- **Acerto de código:** parte dos códigos aprovados que o método acertou, considerando a quantidade.
- **Acerto de serviço:** o mesmo, comparando só o número do serviço (`57` = `57b`).
- **Erro de HPA:** diferença média por commit entre o HPA calculado pela tabela e o aprovado.

## O que aprendemos

1. **Exemplos aprovados pesam mais que o tamanho do modelo.** O qwen3 foi de 10% para 57% só com eles.
2. **Travar o código e calcular o HPA pela tabela** eliminou códigos inválidos e horas inventadas.
3. **Modelos de código (qwen2.5-coder) tendem a inventar arquivos.** qwen3 e gemma3 não inventaram.
4. **A mensagem do commit quase não muda o resultado.** O diff carrega a informação.
5. **O classificador sozinho é fraco com 160 commits.** A estrutura do diff não separa bem `21e`
   (bug) de `21d` (regra de negócio): a diferença está no significado da mudança.
6. **Há um teto:** mesmo classificando todo arquivo corretamente, só ~77% dos commits ficariam 100%
   exatos, porque o supervisor aprova "eventos" (dois bugs no mesmo arquivo) que a estrutura não mostra.
   **Os 95% só são possíveis respondendo sozinho quando há confiança** e sinalizando o resto.
7. **Agrupar códigos repetidos está errado.** Em 38 commits o supervisor aprovou o mesmo código mais
   de uma vez. O benchmark ainda agrupa (`consolidar`); é preciso desfazer.

## Arquitetura proposta

```
 diff ─► 1. pré-processamento (CPU): arquivos NOVO/ALTERADO/REMOVIDO, bloco por arquivo
         2. busca dos commits APROVADOS mais parecidos (CPU)
         3. três opiniões independentes:
              a) Ollama + qwen3:14b + exemplos aprovados (GPU)   ← Gemini se não houver GPU
              b) classificador treinado nas tarefas aprovadas (CPU)
              c) cópia do aprovado mais parecido (CPU)
         4. decisão: concordam → aprova sozinho │ discordam → REVISAR (com motivo e opções)
         5. HPA = tabela do catálogo
```

**Como o sistema "aprende":** cada tarefa aprovada entra no banco de exemplos e no treino do
classificador, que treina em segundos. O modelo de linguagem não muda, por isso o comportamento é
o mesmo em qualquer máquina; o que muda entre máquinas é só a velocidade.

## Próximos passos

1. [ ] **Remover o agrupamento** de códigos repetidos (`consolidar`) do benchmark.
2. [ ] **Medir a concordância:** rodar qwen3 + classificador + cópia nos mesmos commits e calcular
       a cobertura com ≥95% de acerto quando os três concordam.
3. [ ] **Testar o banco de exemplos maior** (`INCLUIR_GRANDES=1`, 130 commits) com o qwen3.
4. [ ] **Ajustar o classificador:** limiar de confiança e códigos raros (60, 62a, 57, 21g, 61 têm
       menos de 10 exemplos).
5. [ ] **Dividir diffs grandes** (> 24 mil caracteres) por arquivo antes de enviar ao modelo.
6. [ ] **Completar a tabela de complexidade** do catálogo com respira-go, ulysses, ftr e hub_saude
       (hoje caem em "Média").
7. [ ] **Integrar ao Nexus:** provider `ollama | gemini | auto` no lugar de `gemini_service.py`, com a
       etapa de revisão na interface.

## Arquivos

| Arquivo | Papel |
|---|---|
| [`llm-local/catalogo_hpa.py`](../../llm-local/catalogo_hpa.py) | tabela de HPA do catálogo → códigos válidos e HPA por código |
| [`llm-local/benchmark_llm_local.py`](../../llm-local/benchmark_llm_local.py) | teste dos modelos de linguagem e da referência sem IA (`knn`) |
| [`llm-local/classificador/por_arquivo.py`](../../llm-local/classificador/por_arquivo.py) | classificador por arquivo (versão atual) |
| [`llm-local/classificador/classificador.py`](../../llm-local/classificador/classificador.py) | classificador por commit (primeira versão, superada) |
| [`llm-local/mover-docker-para-home.sh`](../../llm-local/mover-docker-para-home.sh) | move os dados do Docker nativo para o `/home` |
