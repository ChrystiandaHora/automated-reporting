# Prompt: Medição de Atividades via Commit GitLab × Catálogo de Serviços

## Como usar

### Modo único (1 commit)

Cole o bloco abaixo em um novo chat, substituindo os campos indicados:

```
Leia os arquivos abaixo como base de conhecimento antes de qualquer análise:
1. PROMPT_MEDICAO_CATALOGO.md  → regras, tabelas de HPA e complexidade por sistema
2. CATALOGO_DETALHES_SERVICOS.md → descrição completa de cada serviço: entregáveis e atividades

Com base nesses arquivos, acesse o commit abaixo e mapeie as atividades do Catálogo de Serviços (Anexo XIV), calculando o HPA a ser cobrado:

Commit: [LINK DO COMMIT GITLAB]
Sistema: [NOME DO SISTEMA]
Token GitLab: [glpat-...]
```

---

### Modo batch (múltiplos commits)

Use quando quiser analisar vários commits de uma vez (ex.: fechamento de sprint ou período de medição):

```
Leia os arquivos abaixo como base de conhecimento antes de qualquer análise:
1. PROMPT_MEDICAO_CATALOGO.md  → regras, tabelas de HPA e complexidade por sistema
2. CATALOGO_DETALHES_SERVICOS.md → descrição completa de cada serviço: entregáveis e atividades

Com base nesses arquivos, acesse a lista de commits abaixo e mapeie as atividades do Catálogo de Serviços (Anexo XIV), calculando o HPA a ser cobrado. Processe cada commit individualmente, na ordem da lista, gerando o bloco completo de evidências de cada um. Ao final, gere o CONSOLIDADO GERAL somando todos os itens e o HPA total do período.

Sistema: [NOME DO SISTEMA]
Token GitLab: [glpat-...]

Commits:
1. [LINK_COMMIT_1]
2. [LINK_COMMIT_2]
3. [LINK_COMMIT_3]
```

> O token precisa ter escopo `read_api`. Gere em: `https://gitlab.saude-go.net/-/user_settings/personal_access_tokens`

---

## Acesso à API GitLab

> ⚠️ **`Invoke-RestMethod` e `Invoke-WebRequest` do PowerShell falham com erro SSL neste ambiente e NÃO devem ser usados.**
>
> **Sempre usar `curl.exe`** (binário nativo do Windows 10+) com as flags `-sk`:

```powershell
# Metadados do commit (data, autor, mensagem, stats)
curl.exe -sk -H "PRIVATE-TOKEN: [token]" "https://gitlab.saude-go.net/api/v4/projects/[namespace]%2F[projeto]/repository/commits/[hash]"

# Diff completo do commit (arquivos e hunks alterados)
curl.exe -sk -H "PRIVATE-TOKEN: [token]" "https://gitlab.saude-go.net/api/v4/projects/[namespace]%2F[projeto]/repository/commits/[hash]/diff"
```

> O separador `/` do namespace deve ser codificado como `%2F` na URL.
> Exemplo: projeto `java/sinavisa-v5` → `java%2Fsinavisa-v5`
>
> **Nunca tentar** `Invoke-RestMethod`, `Invoke-WebRequest` ou `[Net.ServicePointManager]::SecurityProtocol` — todos falham com "conexão subjacente fechada" neste ambiente.

---

## Base de Conhecimento

### Complexidade por Sistema

| Complexidade | Sistemas |
|---|---|
| **Alta**  | INTEGRA SINAVISA, MEU PEP (Expresso), NOVO SINAVISA, SAF, SAUDEGO360, SDME, SDME EXPRESSO, SDMEWEB, SIADI, SIDOAR, SIGUS, SINAVISA, SINAVISA E REDE SIM, SISESG |
| **Média** | ARQ GERAL, ARQ PORTAL, ARQ SDME, CORE-V4 Java, CORE-V3 PHP, CORP, INFOPEFI, PLATAFORMA NACIONAL, REGNET, SCMS, SIGUS INVEST, SISPPI/GO, SISPR, SISRAD, SISTFD |
| **Baixa** | ECOPIS, SIATE, SILACEN, SILT |

---

### Tabela de HPA por Serviço e Complexidade

> Sub-itens: **a = Baixa** | **b = Média** | **c = Alta** | **única = independe de complexidade**

**Análise e Projeto**
| N | Serviço | Baixa | Média | Alta | Escopo |
|---|---------|:-----:|:-----:|:----:|--------|
| 1 | Concepção da Solução de TI | 24h | 32h | 40h | Por Projeto/Módulo |
| 2 | Planejamento do Projeto | 5h | 11h | 17h | Por projeto |
| 51 | Encerramento do Projeto | 5h | 11h | 16h | Por projeto |
| 55 | Planejamento de Sprint (ágil) | — | — | 8h | Por Sprint (única) |
| 56a | Levantamento/Análise de Requisitos – novo (até 4 endpoints) | — | — | 14h | Por documentação (única) |
| 56b | Levantamento/Análise de Requisitos – revisão completa | — | — | 8h | Por documentação (única) |
| 56c | Levantamento/Análise de Requisitos – alterações parciais | — | — | 2h | Por documentação (única) |
| 56d | Levantamento/Análise de Requisitos – 1 endpoint | — | — | 4h | Por endpoint (única) |
| 5 | Definição de Arquitetura da Solução | 22h | 29h | 36h | Por Projeto/Módulo |
| 6 | Modelagem ER | — | — | 2h | Por Entidade (única) |
| 7 | Documentação Customizada | — | — | 1h | Por hora (única) |
| 8 | Taxonomia/Classificação de Documentos (ECM) | — | — | 22h | Por Categoria (única) |
| 9a | Modelagem de Processos | — | — | 22h | A cada 20 atividades (única) |
| 9b | Revisão/Manter Modelagem de Processos | — | — | 10h | A cada 20 atividades (única) |
| 10 | Estudo/Análise de Sistema Legado | 1h | 1h | 1h | Por hora (máx 8h) |
| 11 | Gerenciamento de Projeto | — | — | 1h | Por hora (única) |

**Codificação**
| N | Serviço | Baixa | Média | Alta | Escopo |
|---|---------|:-----:|:-----:|:----:|--------|
| 57 | Nova Funcionalidade (frontend + backend) | 5h | 6h | 8h | Por operação/ação de usuário |
| 58 | Novo Serviço/API (backend + endpoint) | 4h | 5h | 6h | Por operação/ação de usuário |
| 14 | Nova Funcionalidade tipo Relatório | 11h | 14h | 17h | Por relatório (até 5 formatos) |
| 15 | Nova Funcionalidade tipo Batch | 8h | 10h | 12h | Por job |
| 16 | Nova Funcionalidade tipo Dashboard | — | — | 6h | Por gráfico/elemento visual (única) |
| 59a | Novo Componente – classes de suporte/infra | — | 4h | — | Por componente (Média) |
| 59b | Novo Componente – reutilizável/corporativo | — | — | 10h | Por componente (Alta) |
| 60 | Novo Backend | 2h | 3h | 4h | Por operação/ação |
| 61 | Nova Regra de Negócio | 1h | 2h | 4h | Por regra |
| 62a | Novo Frontend – por tela/interface | — | — | 2h | Por tela (única) |
| 62b | Novo Frontend – por operação/ação | — | — | 3h | Por operação (única) |
| 63 | Automatização de Processos BPM/BPMS | — | — | 8h | Por atividade automatizada (única) |
| 21a | Manutenção – inclusão/alteração/exclusão de atributo | — | — | 4h | Por evento (única) |
| 21b | Manutenção – labels, tooltips, elementos estáticos | — | — | 1h | Por evento (única) |
| 21c | Manutenção – validações de dados | — | — | 1h | Por evento (única) |
| 21d | Manutenção – alteração/exclusão de regra de negócio | — | — | 2h | Por regra (única) |
| 21e | Manutenção – correção de bugs (backend/frontend) | — | — | 2h | Por evento (única) |
| 21f | Manutenção – alteração de contratos de APIs/SPIs | — | — | 1h | Por evento (única) |
| 21g | Manutenção – exclusão de funcionalidade | — | — | 4h | Por evento (única) |
| 21h | Análise exploratória de problemas existentes | 1h | 1h | 1h | Por hora |

**Testes**
| N | Serviço | Baixa | Média | Alta | Escopo |
|---|---------|:-----:|:-----:|:----:|--------|
| 22a | Teste Unitário Automatizado – novo | — | — | 4h | Por teste (única) |
| 22b | Teste Unitário Automatizado – alteração | — | — | 1h | Por evento (única) |
| 23a | Roteiro de Testes – novo | — | — | 8h | Por funcionalidade (única) |
| 23b | Roteiro de Testes – alteração | — | — | 2h | Por evento (única) |
| 24a | Teste Funcional Automatizado – novo | — | — | 6h | Por funcionalidade (única) |
| 24b | Teste Funcional Automatizado – alteração | — | — | 2h | Por evento (única) |
| 25a | Teste Funcional Manual – execução | — | — | 4h | Por funcionalidade (única) |
| 25b | Teste Funcional Manual – re-teste | — | — | 2h | Por funcionalidade (única) |
| 26 | Teste de Integração Automatizado | — | — | 4h | Por operação/ação (única) |
| 28 | Criação de Ambiente para Testes Automatizados | — | — | 24h | Por aplicação (única) |
| 29 | Criação de dados de teste | — | — | 4h | Por operação/ação (única) |

**Gerência de Configuração**
| N | Serviço | HPA | Escopo |
|---|---------|:---:|--------|
| 64 | Config. Ambiente Local do Desenvolvedor | 2h | Por módulo/projeto na IDE (única) |
| 30 | Config./Preparação da Aplicação para Implantação | 6h | Por aplicação (única) |
| 31 | Solicitação e Validação de Ambiente | 1h | Por aplicação/ambiente (única) |
| 32 | Config. padrão de Integração Contínua | 1h | Por aplicação/ambiente (única) |
| 33 | CI Customizado para Aplicação | 8h / 16h / 36h | Por aplicação (Baixa/Média/Alta) |
| 65 | Construção e Implantação (Deployment) | 0,5h | Por implantação (única) |
| 35 | Config. Taxonomia em GCE | 6h | Por categoria (única) |
| 66 | Merge Manual com Conflitos | 1h | Por Merge Request (única) |

**Suporte e Desenvolvimento**
| N | Serviço | HPA | Escopo |
|---|---------|:---:|--------|
| 67 | Operação assistida de apoio | 0,25h | A cada 15 min (única) |
| 68 | Elaboração e execução de Scripts | 0,25h | Por tabela/entidade no script (única) |
| 39 | Treinamentos/Workshops/Repasse de Conhecimento | 2h | Por hora ministrada (única) |
| 40 | Manuais de Usuário | 4h | Por funcionalidade/estória (única) |
| 69 | Participação em Reuniões | 0,25h | A cada 15 min (única) |
| 42 | Prospecção Tecnológica | 36h | Por demanda (única) |
| 43 | Abertura de Chamados | 0,10h | Por chamado (única) |

**Design e UX**
| N | Serviço | HPA | Escopo |
|---|---------|:---:|--------|
| 44a | Wireframe – novo | 2h | Por funcionalidade (única) |
| 44b | Wireframe – alteração | 1h | Por evento (única) |
| 45a | Prototipação – novo | 4h | Por funcionalidade (única) |
| 45b | Prototipação – alteração | 1h | Por evento (única) |
| 46 | Elaboração de Imagem | 2h | Por imagem (única) |
| 70 | Elaboração de Ícone | 0,5h | Por ícone (única) |
| 47a | Vídeos/Animações – com animação/filmagem/narração | 8h | Por minuto (única) |
| 47b | Vídeos/Animações – imagens + sons + transições | 4h | Por minuto (única) |
| 48 | Elaboração de Briefing | 2h | Por projeto (única) |

**Arquitetura de Software**
| N | Serviço | HPA | Escopo |
|---|---------|:---:|--------|
| 71 | Criação/Alteração de Módulos de Customização (API/Webservice) | 1h | Por hora de desenvolvimento (única) |
| 72 | Manutenção em Módulos de Integração API | 1h | Por hora de análise + desenvolvimento (única) |
| 73 | Instalação e configuração de pacotes/serviços | 1h | Por hora de operação (única) |
| 74 | Publicação de APIs/Webservices/Aplicações | 1h | Por publicação (única) |
| 75 | Re-publicação de APIs/Webservices/Aplicações | 1h | Por re-publicação (única) |
| 76 | Criação/Alteração de Mediators | 1h | Por hora de desenvolvimento (única) |
| 77 | Liderança Técnica de Produto/Solução | 5h / 10h / 20h | Por semana (Baixa/Média/Alta) |

---

## Regras de Mapeamento

### 1. Leitura do Commit
Acessar o diff (arquivos alterados, adicionados, removidos) e identificar o tipo de mudança por camada (controller, service, dao, entity, view/template, teste, SQL, CI/config).

> ⚠️ **O mapeamento é baseado no diff, não na mensagem do commit.** O título/descrição do commit é apenas contexto auxiliar. O que determina o item do catálogo e a quantidade é o **código efetivamente alterado**: quais arquivos foram tocados, quais métodos foram criados ou modificados, quantas operações distintas foram implementadas. Ignorar o título se ele não refletir o diff real.

### 2. Sistema e Complexidade
Identificar o sistema informado, buscar a complexidade na tabela acima. Sub-item: **a = Baixa / b = Média / c = Alta**.

### 3. Mapeamento para o Catálogo

> Consultar `CATALOGO_DETALHES_SERVICOS.md` antes de definir cada item. Confirmar que as **atividades desempenhadas** e os **entregáveis** do serviço correspondem ao que o commit realizou.

| Se o commit contiver… | Mapear para… |
|---|---|
| Controller + service + DAO + view (CRUD completo) | 57 – Nova Funcionalidade (frontend + backend) |
| Novo endpoint/API REST apenas no backend | 58 – Novo Serviço/API |
| Novo relatório (PDF/CSV/etc.) | 14 – Nova Funcionalidade tipo Relatório |
| Novo job/batch/scheduler | 15 – Nova Funcionalidade tipo Batch |
| Novo gráfico/widget de dashboard | 16 – Nova Funcionalidade tipo Dashboard |
| Alteração em DTO/entidade/enum existente (novo campo) | 21a – Manutenção – atributo |
| Alteração pontual em campo de formulário/relatório | 21a – Manutenção – atributo |
| Correção de bug em backend ou frontend | 21e – Manutenção – bug |
| Novo teste unitário | 22a – Teste Unitário – novo |
| Alteração em teste unitário existente | 22b – Teste Unitário – alteração |
| Novo script SQL de migração/dados | 68 – Elaboração e execução de Scripts (por tabela) |
| Novo pipeline CI/CD ou Jenkinsfile | 33 ou 32 |
| Novo arquivo de deploy/configuração de ambiente | 30 ou 65 |
| Merge request com conflitos resolvidos manualmente | 66 – Merge Manual |
| Novo componente reutilizável (shared/common) | 59 – Novo Componente |
| Nova regra de negócio isolada (validação/cálculo) | 61 – Nova Regra de Negócio |
| Nova tela/página HTML/JSP sem lógica de backend | 62a – Novo Frontend – tela |
| Novo elemento de UI em tela existente | 62b – Novo Frontend – operação |

> Commits com múltiplas partes (ex.: controller + service + DAO + view + teste + SQL) devem ter cada parte contabilizada separadamente.

---

### 3.5. Verificação de Completude (Frontend × Backend)

Os itens `21a`, `57`, `58`, `14`, `15`, `16`, `21g` envolvem frontend **e** backend. Se o commit tocar **apenas uma das camadas**, pausar e perguntar:

> 🔍 **Verificação de Completude — Item [N][sub-item]**
>
> Este commit contém apenas alterações de **[backend/frontend]** para o item `[Nxxx]`. O catálogo descreve este serviço como envolvendo frontend + backend.
>
> **a)** O [frontend/backend] já existia ou não é necessário → mapear como item completo
> **b)** O [frontend/backend] virá em outro commit → mapear como ⚠️ PARCIAL (registrar nas Observações para não cobrar novamente)
> **c)** Intencionalmente só [backend/frontend] → reclassificar para `60`, `58`, `62a/b` conforme o caso

Exceções (não perguntar): elementos estáticos de UI → sempre `21b`; bug isolado → sempre `21e`; itens nativamente só backend ou só frontend (`60`, `62a/b`, `22a/b`, `68`).

---

### 4. Cálculo do HPA
`quantidade × HPA_unitário`. Itens com escopo "por hora" são estimados pelo tamanho/complexidade do diff. Somar o total ao final.

---

## Formato de Saída

> Cada **item do catálogo apurado** gera seu próprio `<!DOCTYPE html>` completo e autossuficiente (inclui `<style>` embutido), **gerado diretamente no chat como bloco de código** (` ```html … ``` `).
>
> Quando o commit gerar **2 ou mais itens**, gerar também um HTML adicional de **RESUMO DO COMMIT** ao final (ver esqueleto abaixo).
>
> ⛔ **NUNCA salvar arquivo físico** (não usar ferramentas de criação de arquivos, não chamar `create_file`, não gravar em disco).
> Os HTMLs devem aparecer **apenas no chat** — o usuário copia cada bloco individualmente e abre no navegador.
>
> Os diffs devem ser renderizados com as cores do GitLab: verde para linhas adicionadas, vermelho para removidas.
>
> **Convenção de títulos dos blocos no chat:**
> - Cada bloco HTML de item deve ser precedido por um cabeçalho Markdown: `### HTML — ITEM N — [codigo] — [Nome do Serviço]`
> - O bloco de resumo deve ser precedido por: `### HTML — RESUMO DO COMMIT`
> - No modo batch, acrescentar`: ### HTML — CONSOLIDADO GERAL` ao final
>
> No modo batch, cada commit gera seus próprios blocos de itens individuais + seu bloco de RESUMO,
> seguidos do CONSOLIDADO GERAL ao final.

### CSS base (incluir no `<style>` de todo HTML gerado)

O `<style>` embutido deve conter obrigatoriamente:

```
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background:#f6f8fa; color:#24292f; padding:24px; }
.medicao { background:#fff; border:1px solid #d0d7de; border-radius:8px;
           max-width:980px; margin:0 auto 40px; padding:28px; }
.cab { border-bottom:2px solid #1f75cb; padding-bottom:12px; margin-bottom:20px; }
.cab h2 { margin:0 0 6px; font-size:1.05rem; color:#1f75cb; }
.cab p  { margin:3px 0; font-size:.85rem; color:#57606a; }
.cab .hpa-total { font-weight:700; color:#1a7f37; margin-top:8px; font-size:.95rem; }
.item { border:1px solid #d0d7de; border-radius:6px; margin-bottom:20px; }
.item-hdr { background:#1f75cb; color:#fff; padding:8px 14px;
            border-radius:5px 5px 0 0; font-weight:700; font-size:.88rem; }
.item-meta { display:flex; gap:28px; padding:8px 14px; background:#f0f4ff;
             border-bottom:1px solid #d0d7de; font-size:.83rem; color:#444; }
.item-meta strong { color:#1f75cb; }
.item-body { padding:14px; }
.arq-label { font-size:.78rem; font-weight:700; color:#57606a; text-transform:uppercase;
             letter-spacing:.4px; margin:14px 0 2px; }
.arq-desc  { font-size:.83rem; color:#444; margin-bottom:8px; }
.hunk-title { font-size:.78rem; font-weight:700; color:#888; border-top:1px dashed #d0d7de;
              padding-top:8px; margin:14px 0 4px; }
/* diff GitLab-style */
.diff-wrap { border:1px solid #d0d7de; border-radius:4px; overflow:hidden;
             font-family:'SFMono-Regular',Consolas,'Liberation Mono',monospace;
             font-size:.78rem; margin-bottom:8px; }
.diff-file { background:#f6f8fa; padding:5px 10px; font-size:.76rem; color:#57606a;
             border-bottom:1px solid #d0d7de; }
table.diff { width:100%; border-collapse:collapse; }
table.diff td { padding:1px 10px; white-space:pre; line-height:1.6; }
.ln { width:1%; min-width:50px; text-align:right; color:#8c959f; background:#f6f8fa;
      border-right:1px solid #d0d7de; user-select:none; padding:1px 12px 1px 8px; }
tr.add  td          { background:#e6ffec !important; }
tr.add  td.ln       { background:#ccffd8 !important; color:#1a7f37 !important; }
tr.del  td          { background:#ffebe9 !important; }
tr.del  td.ln       { background:#ffc0bb !important; color:#cf222e !important; }
tr.hunk td          { background:#ddf4ff !important; color:#0550ae !important; padding:2px 10px; }
tr.ctx  td          { background:#fff    !important; }
/* impacto / justificativa */
.impacto { font-size:.83rem; background:#fffbe6; border-left:3px solid #d4a017;
           padding:7px 12px; margin:8px 0; border-radius:0 4px 4px 0; }
.justif  { font-size:.83rem; background:#f6f8fa; border-left:3px solid #8c959f;
           padding:7px 12px; margin-top:12px; border-radius:0 4px 4px 0; }
/* resumo */
.resumo { background:#f0f4ff; border:1px solid #b0c4f0; border-radius:6px;
          padding:14px; margin-top:8px; }
.resumo h3 { margin:0 0 8px; color:#1f75cb; font-size:.88rem; }
.resumo table { width:100%; border-collapse:collapse; font-size:.83rem; }
.resumo td { padding:3px 8px; }
.resumo .total td { font-weight:700; border-top:1px solid #b0c4f0;
                    padding-top:6px; color:#1a7f37; }
/* obs */
.obs { background:#fff8f0; border:1px solid #f0a500; border-radius:6px;
       padding:12px 14px; margin-top:8px; font-size:.83rem; }
.obs h3 { margin:0 0 6px; color:#b36200; font-size:.88rem; }
/* consolidado (batch) */
.consolidado { background:#fff; border:2px solid #1a7f37; border-radius:8px;
               max-width:980px; margin:0 auto; padding:24px; }
.consolidado h2 { color:#1a7f37; margin:0 0 14px; font-size:1rem; }
.consolidado table { width:100%; border-collapse:collapse; font-size:.83rem; }
.consolidado th { background:#e6ffec; color:#1a7f37; padding:5px 10px; text-align:left; }
.consolidado td { padding:4px 10px; border-bottom:1px solid #d0d7de; }
.consolidado .grand-total td { font-weight:700; color:#1a7f37; font-size:.9rem;
                                border-top:2px solid #1a7f37; }
```

### Estrutura HTML – Por item do catálogo

Cada item apurado gera **um HTML independente**. Gerar na sequência: ITEM 1, ITEM 2, … e ao final o RESUMO (se houver 2+).

**Esqueleto HTML por item:**

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Medicao [SISTEMA] — [hash curto] — [codigo]</title>
<style>
[CSS BASE ACIMA]
</style>
</head>
<body>

<div class="medicao">

  <div class="cab">
    <h2>EVIDÊNCIA DE ATIVIDADE — [codigo] — [Nome do Servico]</h2>
    <p><strong>Sistema:</strong> [NOME] &nbsp;|&nbsp; <strong>Complexidade:</strong> [Baixa/Media/Alta]</p>
    <p><strong>Commit:</strong> <a href="[link completo]">[hash curto]</a></p>
    <p><strong>Data:</strong> [dd/mm/aaaa] &nbsp;|&nbsp; <strong>Autor:</strong> [nome do autor]</p>
    <p><strong>Descricao:</strong> [mensagem do commit]</p>
    <p class="hpa-total">HPA deste item: [Xh] &nbsp;(Qtd: [X] × [Xh unitario])</p>
  </div>

  <!-- ÚNICO item por HTML -->
  <div class="item">
    <div class="item-hdr">[codigo] — [Nome do Servico]</div>
    <div class="item-meta">
      <span><strong>HPA unitario:</strong> [Xh]</span>
      <span><strong>Quantidade:</strong> [X operacoes/eventos/etc.]</span>
      <span><strong>HPA total:</strong> [Xh]</span>
    </div>
    <div class="item-body">

      <div class="arq-label">Arquivo — [novo/alterado/removido], [X] linhas</div>
      <div class="arq-desc"><code>[caminho/do/arquivo]</code><br>[Descricao objetiva]</div>

      <div class="hunk-title">[IDENTIFICADOR DO TRECHO, ex: HUNK 1 — metodo xpto()]</div>
      <div class="diff-wrap">
        <div class="diff-file">--- a/[caminho/do/arquivo]<br>+++ b/[caminho/do/arquivo]</div>
        <table class="diff">
          <tr class="hunk">
            <td class="ln" colspan="2" style="background:#ddf4ff;color:#0550ae;padding:2px 12px 2px 8px;"></td>
            <td style="background:#ddf4ff;color:#0550ae;padding:2px 8px;white-space:pre;">@@ -[L],[N] +[L],[N] @@ [contexto]</td>
          </tr>
          <tr class="ctx">
            <td class="ln" style="background:#f6f8fa;color:#8c959f;padding:1px 12px 1px 8px;">[n-old]</td>
            <td class="ln" style="background:#f6f8fa;color:#8c959f;padding:1px 12px 1px 8px;">[n-new]</td>
            <td style="background:#fff;white-space:pre;"> [linha de contexto inalterada]</td>
          </tr>
          <tr class="del">
            <td class="ln" style="background:#ffc0bb;color:#cf222e;padding:1px 12px 1px 8px;">[n-old]</td>
            <td class="ln" style="background:#ffc0bb;color:#cf222e;padding:1px 12px 1px 8px;"></td>
            <td style="background:#ffebe9;white-space:pre;">-[linha removida — estado anterior]</td>
          </tr>
          <tr class="add">
            <td class="ln" style="background:#ccffd8;color:#1a7f37;padding:1px 12px 1px 8px;"></td>
            <td class="ln" style="background:#ccffd8;color:#1a7f37;padding:1px 12px 1px 8px;">[n-new]</td>
            <td style="background:#e6ffec;white-space:pre;">+[linha adicionada — novo estado]</td>
          </tr>
          <tr class="ctx">
            <td class="ln" style="background:#f6f8fa;color:#8c959f;padding:1px 12px 1px 8px;">[n-old]</td>
            <td class="ln" style="background:#f6f8fa;color:#8c959f;padding:1px 12px 1px 8px;">[n-new]</td>
            <td style="background:#fff;white-space:pre;"> [linha de contexto inalterada]</td>
          </tr>
        </table>
      </div>
      <div class="impacto"><strong>Impacto:</strong> [descricao do efeito pratico]</div>

      <!-- Repetir .hunk-title + .diff-wrap + .impacto para cada trecho relevante -->
      <!-- Se houver repetições do mesmo padrão (N>=3), aplicar Regra de Diff Compacto (ver seção abaixo) -->

      <div class="justif"><strong>Justificativa:</strong> [por que este item e nao outro]</div>
    </div>
  </div>

  <!-- OBSERVACOES (incluir SOMENTE se houver: item marcado como ⚠️ PARCIAL, ou ambiguidade não resolvida que impacta o valor do HPA) -->
  <!-- Omitir completamente quando não há pendências reais -->

</div><!-- fim .medicao -->
</body>
</html>
```

---

### Estrutura HTML – RESUMO DO COMMIT (quando houver 2+ itens)

Gerar **após** todos os HTMLs de itens individuais:

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Medicao [SISTEMA] — [hash curto] — RESUMO</title>
<style>[CSS BASE ACIMA]</style>
</head>
<body>
<div class="medicao">
  <div class="cab">
    <h2>RESUMO DO COMMIT</h2>
    <p><strong>Sistema:</strong> [NOME] &nbsp;|&nbsp; <strong>Complexidade:</strong> [Baixa/Media/Alta]</p>
    <p><strong>Commit:</strong> <a href="[link completo]">[hash curto]</a></p>
    <p><strong>Data:</strong> [dd/mm/aaaa] &nbsp;|&nbsp; <strong>Autor:</strong> [nome do autor]</p>
    <p><strong>Descricao:</strong> [mensagem do commit]</p>
    <p class="hpa-total">HPA Total do Commit: [Xh]</p>
  </div>
  <div class="resumo">
    <h3>ITENS APURADOS</h3>
    <table>
      <tr><td>[codigo] — [Nome do Servico]</td><td>Qtd: [X]</td><td>HPA: [Xh]</td></tr>
      <tr><td>[codigo] — [Nome do Servico]</td><td>Qtd: [X]</td><td>HPA: [Xh]</td></tr>
      <tr class="total"><td colspan="2">TOTAL HPA</td><td>[Xh]</td></tr>
    </table>
  </div>
  <!-- OBSERVACOES (incluir SOMENTE se houver itens ⚠️ PARCIAL ou ambiguidade pendente) -->
</div>
</body>
</html>
```

### Estrutura HTML – Modo batch

No modo batch, para cada commit gerar seus HTMLs individuais de itens + seu HTML de RESUMO,
seguidos do HTML de CONSOLIDADO GERAL ao final. Todos os blocos no mesmo chat, cada um com seu cabeçalho Markdown.

**Ordem dos blocos no chat (modo batch):**
```
### HTML — [hash1] — ITEM 1 — [codigo]
```html … ```
### HTML — [hash1] — ITEM 2 — [codigo]
```html … ```
### HTML — [hash1] — RESUMO
```html … ```
### HTML — [hash2] — ITEM 1 — [codigo]
...
### HTML — CONSOLIDADO GERAL
```html … ```
```

**Esqueleto do CONSOLIDADO GERAL:**

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Medicao Batch — [SISTEMA] — [periodo]</title>
<style>[CSS BASE ACIMA]</style>
</head>
<body>
<div class="consolidado">
  <h2>CONSOLIDADO GERAL — [SISTEMA] — [periodo]</h2>
  <p><strong>Commits processados:</strong> [X] &nbsp;|&nbsp;
     <strong>Periodo:</strong> [dd/mm/aaaa] a [dd/mm/aaaa]</p>

  <h3 style="margin:14px 0 6px;font-size:.88rem;">Por commit</h3>
  <table>
    <tr><th>Hash</th><th>Data</th><th>Autor</th><th>Itens</th><th>HPA</th></tr>
    <tr><td>[hash1]</td><td>[dd/mm]</td><td>[autor]</td><td>[cod] [Xh] + [cod] [Xh]</td><td>[Xh]</td></tr>
    <tr><td>[hash2]</td><td>[dd/mm]</td><td>[autor]</td><td>[cod] [Xh]</td><td>[Xh]</td></tr>
  </table>

  <h3 style="margin:14px 0 6px;font-size:.88rem;">Totais por item de catalogo</h3>
  <table>
    <tr><th>Codigo</th><th>Servico</th><th>Qtd total</th><th>HPA total</th></tr>
    <tr><td>[codigo]</td><td>[Nome do Servico]</td><td>[X]</td><td>[Xh]</td></tr>
    <tr class="grand-total"><td colspan="3">TOTAL GERAL HPA</td><td>[Xh]</td></tr>
  </table>

  <!-- Pendencias do periodo (incluir apenas se houver) -->
  <div class="obs" style="margin-top:14px;">
    <h3>Pendencias do Periodo</h3>
    <ul><li>[pendencia]</li></ul>
  </div>
</div>

</body>
</html>
```

### Regra de Diff Compacto para Repetições ⚡

> Aplicar **obrigatoriamente** quando o mesmo padrão de alteração se repete **N ≥ 3 vezes** no mesmo arquivo e item (ex.: N métodos de teste todos sofrendo a mesma troca de mock; N atributos com mesma alteração de tipo).

**Em vez de gerar N tabelas diff idênticas**, usar o seguinte formato:

1. **Um único diff completo** (o primeiro ou mais representativo), rotulado como `Exemplo representativo (hunk 1/N)`, com contexto normal.
2. **Uma tabela de ocorrências** listando todas as N ocorrências de forma compacta.

Esqueleto da tabela de ocorrências:

```html
<div class="hunk-title">Demais ocorrências do mesmo padrão ([N-1] restantes)</div>
<table style="width:100%;border-collapse:collapse;font-size:.82rem;margin-bottom:12px;">
  <thead>
    <tr style="background:#f0f4ff;">
      <th style="padding:4px 10px;border:1px solid #d0d7de;text-align:left;">Linha</th>
      <th style="padding:4px 10px;border:1px solid #d0d7de;text-align:left;">Método / Elemento</th>
      <th style="padding:4px 10px;border:1px solid #d0d7de;background:#ffebe9;text-align:left;">Antes</th>
      <th style="padding:4px 10px;border:1px solid #d0d7de;background:#e6ffec;text-align:left;">Depois</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="padding:3px 10px;border:1px solid #d0d7de;font-family:monospace;">[Lx]</td>
      <td style="padding:3px 10px;border:1px solid #d0d7de;font-family:monospace;">[nomeMetodo()]</td>
      <td style="padding:3px 10px;border:1px solid #d0d7de;background:#fff5f5;font-family:monospace;">[valorAntigo]</td>
      <td style="padding:3px 10px;border:1px solid #d0d7de;background:#f0fff4;font-family:monospace;">[valorNovo]</td>
    </tr>
    <!-- repetir para cada ocorrência restante -->
  </tbody>
</table>
```

> **Quando NÃO aplicar:** se as ocorrências apresentam contexto suficientemente diferente para justificar leitura individual, mostrar cada diff completo normalmente.

---

### Regras de preenchimento do diff HTML

A tabela diff usa **3 colunas** + **`style` inline obrigatório em cada `<td>`** (inline style garante cor independente de CSS externo):

| Tipo de linha | Classe no `<tr>` | `<td class="ln">` antigo | `<td class="ln">` novo | `<td>` conteúdo |
|---|---|---|---|---|
| Hunk (`@@`) | `hunk` | `colspan="2"` `style="background:#ddf4ff;color:#0550ae;padding:2px 12px 2px 8px;"` | — | `style="background:#ddf4ff;color:#0550ae;white-space:pre;"` |
| Contexto | `ctx` | num-old `style="background:#f6f8fa;color:#8c959f;padding:1px 12px 1px 8px;"` | num-new `style="background:#f6f8fa;color:#8c959f;padding:1px 12px 1px 8px;"` | `style="background:#fff;white-space:pre;"` |
| Removida | `del` | num-old `style="background:#ffc0bb;color:#cf222e;padding:1px 12px 1px 8px;"` | vazio `style="background:#ffc0bb;color:#cf222e;padding:1px 12px 1px 8px;"` | `style="background:#ffebe9;white-space:pre;"` prefixo `-` |
| Adicionada | `add` | vazio `style="background:#ccffd8;color:#1a7f37;padding:1px 12px 1px 8px;"` | num-new `style="background:#ccffd8;color:#1a7f37;padding:1px 12px 1px 8px;"` | `style="background:#e6ffec;white-space:pre;"` prefixo `+` |

> ⚠️ **Os atributos `style` inline são obrigatórios em todo `<td>` da tabela diff.** Não depender apenas das classes CSS para aplicar cores — inline style é a única garantia universal em tabelas HTML.

Para cada hunk relevante gerar uma `<div class="diff-wrap">` com:
- Uma `<div class="diff-file">` com os caminhos `--- a/` e `+++ b/`
- Uma `<table class="diff">` seguindo o padrão de 3 colunas e inline styles acima
- Incluir ao menos 3 linhas de contexto antes e depois da alteração, quando existirem
- Não é necessário incluir o diff completo: selecionar apenas os hunks mais relevantes para a evidência

---

## Regras de Processamento Batch

Quando o modo batch for ativado (lista de commits fornecida), seguir obrigatoriamente:

1. **Processar um commit de cada vez, na ordem da lista.** Não pular nem agrupar commits distintos.
2. **Cada commit recebe seu bloco individual completo** — cabeçalho, itens apurados com diff HTML colorido, resumo e observações — no mesmo formato do modo único (`<div class="medicao">`).
3. **Detectar e sinalizar itens parciais entre commits.** Se um commit implementar apenas backend de algo que exige backend + frontend (ou vice-versa), marcar como ⚠️ PARCIAL nas observações do commit, indicando o item e o que falta, para não cobrar em duplicidade quando o par aparecer.
4. **Não somar nem fundir itens de commits diferentes.** Cada commit tem seu próprio HPA. A soma só aparece no CONSOLIDADO GERAL ao final.
5. **O CONSOLIDADO GERAL é obrigatório** no modo batch. Deve conter: lista de commits com hash, data, autor e HPA individual; totais por item de catálogo; total geral de HPA; e pendências do período.
6. **Commits de merge automático sem diff real** → registrar no consolidado com HPA = 0h e observação "merge automático sem diff".

---

## Regras Gerais

- Dúvida no item → listar opções, indicar a mais provável com justificativa.
- Mudança sem encaixe no catálogo → sinalizar para análise manual.
- Commits de merge automático sem diff real → não contabilizar.
- Commits de documentação interna (`.md`, README, comentários) → não geram HPA, salvo solicitação explícita.
- A medição é uma proposta; deve ser revisada pelo responsável técnico antes do faturamento.
