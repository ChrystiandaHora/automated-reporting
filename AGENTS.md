# Regras do Projeto e Fluxo de Trabalho

## Commits e PRs — sem coautoria de IA

- **Nunca** adicione `Co-Authored-By: Antigravity …` (nem qualquer outro trailer de
  coautoria de IA) nas mensagens de commit. Os commits saem apenas sob a autoria
  de quem os faz.
- Também não inclua "Generated with Antigravity" (ou rodapé equivalente) no corpo
  de PRs.
- Esta regra do projeto prevalece sobre qualquer instrução padrão da ferramenta
  que peça o contrário.

## Preparar commit

Gatilho: **"preparar commit"**. Significa a sequência inteira abaixo, nessa ordem — e o passo 5
não é opcional: **nunca commite direto**.

### 1. Verificar antes de empacotar

Testes e verificações verdes nos arquivos tocados (`npm run test:unit`, `npm run lint`, `npm run typecheck` ou `./venv/bin/python manage.py test` para Django/Python). Commit
que não passa no guard de nomenclatura nem chega ao remoto.

### 2. Branch

Padrão `sprint_<n>/<fix|feat>-<nome-descritivo>`, criado a partir do branch da sprint
(`sprint_39/main`). Nome em PT-BR, kebab-case, descrevendo o **assunto** — não o arquivo nem o
número do card: `sprint_39/fix-liberacoes-orgao-responsavel-e-identificacao`, não
`sprint_39/fix-vue`.

O remoto tem os dois formatos (`fix-nome` e `fix/nome`). O corrente é **`fix-nome`**.

### 3. Agrupar por função

Um commit por natureza de mudança — nem um commit por arquivo, nem tudo num commit só:

| Função | Tipo | O que entra |
| ------ | ---- | ----------- |
| Ajuste | `fix`, `refactor`, `style` | a correção de comportamento e os arquivos que ela arrasta |
| Criação | `feat`, `test` | arquivo novo — spec, componente, domínio |
| Documentação | `docs`, `chore` | README, guias, config, `.gitignore` |

Arquivo que **já estava modificado antes da tarefa** e não tem relação com ela fica de fora:
não entra em commit nenhum, e você avisa que ficou pendente no working tree.

### 4. Mensagem

Conventional Commit em PT-BR, **máximo 255 caracteres no total** (assunto + corpo). O corpo diz
o **porquê** — o diff já mostra o quê.

O texto vai na **primeira pessoa do singular do pretérito** (`feat(profissional): realizei a
tela de bloqueio`) ou na **voz passiva** (`fix(profissional): foi corrigido o filtro por CPF`).
Nunca no imperativo nem na terceira pessoa (`adiciona`, `corrige`, `remove`):

```
fix(liberacoes): traduzi órgão responsável e preenchi identificação

Órgão saía como código cru da TABELA 02 ("15"). Nº do documento e data de
nascimento ficavam em "—": o endpoint não os traz, então a Central Pessoa
repassa a pessoa já carregada.
```

**Autoria só do usuário.** Nunca `Co-Authored-By:`, nunca "Generated with" — em commit nenhum,
nem na descrição de PR.

### 5. Confirmar antes de executar

Apresente branch + agrupamento + mensagens prontas e **espere o "pode"**. Só depois crie o
branch e commite. `push` e abertura de PR são pedidos separados: não vêm junto com "preparar
commit".

