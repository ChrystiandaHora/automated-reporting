<template>
  <div>
    <!-- Cabeçalho da Página -->
    <PageHeader>
      <div class="flex flex-col gap-1.5">
        <BaseButton class="w-fit" @click="$router.push('/commits')">
          <i class="fa-solid fa-arrow-left" aria-hidden="true"></i>
          <span>Voltar aos Commits</span>
        </BaseButton>
        <div class="flex items-center gap-3">
          <PageTitle>Importar Commits do GitLab</PageTitle>
          <TutorialModal screenId="importar" />
        </div>
        <p class="text-sm text-muted-foreground">
          Importe commits em lote a partir de uma ou mais instâncias do GitLab com credenciais configuradas.
        </p>
      </div>

      <div>
        <router-link to="/config" :class="classesLinkGhost">
          <i class="fa-solid fa-gear" aria-hidden="true"></i>
          <span>Gerenciar Contas GitLab</span>
        </router-link>
      </div>
    </PageHeader>

    <!-- Mensagens Globais de Sucesso ou Erro -->
    <div v-if="erroGlobal" class="mb-6 rounded-md border-l-4 border-danger bg-red-500/15 px-5 py-3 text-sm font-semibold text-danger" role="alert">
      {{ erroGlobal }}
    </div>

    <!-- SEÇÃO 1: SELEÇÃO DA CONTA GITLAB -->
    <section class="mb-9" aria-labelledby="heading-git-selection">
      <div :class="classesTituloSecao">
        <span :class="classesBadgePasso" aria-hidden="true">1</span>
        <div class="flex flex-col gap-1">
          <h2 id="heading-git-selection" :class="classesH2Secao">Selecione a Instância / Conta do GitLab</h2>
          <span class="text-sm text-muted-foreground">Escolha qual token e URL base serão utilizados para ler os commits e diffs da API</span>
        </div>
      </div>

      <!-- Estado de Carregamento das Contas -->
      <div v-if="loadingContas" role="status" aria-live="polite">
        Carregando instâncias GitLab configuradas...
      </div>

      <!-- Alerta quando não há contas cadastradas -->
      <div v-else-if="contas.length === 0">
        <p>Nenhuma conta do GitLab cadastrada no momento.</p>
        <router-link to="/config" :class="classesLinkPrimary" class="mt-2">
          <i class="fa-solid fa-plus" aria-hidden="true"></i>
          <span>Cadastrar Conta GitLab nas Configurações</span>
        </router-link>
      </div>

      <!-- Grid de Contas GitLab -->
      <div v-else data-tour="importar-contas" class="grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4" role="radiogroup" aria-label="Instâncias do GitLab disponíveis">
        
        <!-- Opção: Detecção Automática por Domínio -->
        <div 
          data-tour="importar-conta"
          :class="classesCartaoConta(selectedAccountId === 0)"
          tabindex="0"
          role="radio"
          :aria-checked="selectedAccountId === 0"
          @click="selectedAccountId = 0"
          @keydown.enter.prevent="selectedAccountId = 0"
          @keydown.space.prevent="selectedAccountId = 0"
        >
          <div class="flex min-w-0 items-center gap-3.5">
            <div class="flex size-9.5 shrink-0 items-center justify-center rounded-lg border border-purple-500/30 bg-purple-500/15 text-purple-400">
              <i class="fa-solid fa-wand-magic-sparkles text-lg" aria-hidden="true"></i>
            </div>
            <div class="flex min-w-0 flex-col gap-1">
              <div class="flex flex-wrap items-center gap-2">
                <h3 :class="classesNomeConta">Detecção Automática</h3>
                <span class="inline-block rounded-sm border border-purple-500/35 bg-purple-500/20 px-1.25 py-px text-[0.65rem] font-extrabold leading-none tracking-[0.03em] uppercase text-purple-300">SMART MATCH</span>
              </div>
              <span :class="classesUrlConta">Mapeia cada URL para sua respectiva conta GitLab cadastrada</span>
            </div>
          </div>
          <div :class="classesRadioPilula(selectedAccountId === 0)" aria-hidden="true">
            <div class="size-2 rounded-full bg-primary" v-if="selectedAccountId === 0"></div>
          </div>
        </div>

        <!-- Contas Cadastradas -->
        <div 
          v-for="conta in contas" 
          :key="conta.id" 
          data-tour="importar-conta"
          :class="classesCartaoConta(selectedAccountId === conta.id)"
          tabindex="0"
          role="radio"
          :aria-checked="selectedAccountId === conta.id"
          @click="selectedAccountId = conta.id"
          @keydown.enter.prevent="selectedAccountId = conta.id"
          @keydown.space.prevent="selectedAccountId = conta.id"
        >
          <div class="flex min-w-0 items-center gap-3.5">
            <div class="flex size-9.5 shrink-0 items-center justify-center rounded-lg border border-orange-500/30 bg-orange-500/15 text-orange-400">
              <i class="fa-brands fa-gitlab text-xl" aria-hidden="true"></i>
            </div>
            <div class="flex min-w-0 flex-col gap-1">
              <div class="flex flex-wrap items-center gap-2">
                <h3 :class="classesNomeConta">{{ conta.nome }}</h3>
                <span v-if="conta.padrao" class="inline-block rounded-sm border border-green-500/35 bg-green-500/18 px-1.25 py-px text-[0.65rem] font-extrabold leading-none tracking-[0.03em] uppercase text-green-400">PADRÃO</span>
              </div>
              <span :class="classesUrlConta">{{ conta.url }}</span>
              <span class="font-mono text-xs text-muted-foreground">Token: {{ conta.token_mascarado }}</span>
            </div>
          </div>
          <div :class="classesRadioPilula(selectedAccountId === conta.id)" aria-hidden="true">
            <div class="size-2 rounded-full bg-primary" v-if="selectedAccountId === conta.id"></div>
          </div>
        </div>

      </div>
    </section>

    <!-- SEÇÃO 2: INFORMAR COMMITS -->
    <section class="mb-9" aria-labelledby="heading-commits-input">
      <div :class="classesTituloSecao">
        <span :class="classesBadgePasso" aria-hidden="true">2</span>
        <div class="flex flex-col gap-1">
          <h2 id="heading-commits-input" :class="classesH2Secao">Informe os Commits</h2>
          <span class="text-sm text-muted-foreground">Cole as URLs completas dos commits do GitLab (uma por linha)</span>
        </div>
      </div>

      <div class="grid grid-cols-[1.4fr_1fr] gap-6 max-[860px]:grid-cols-1">
        <div data-tour="importar-coluna-urls" class="flex flex-col gap-2">
          <label for="input-commits-area" class="mb-1.5 block text-sm font-bold tracking-[0.05em] text-foreground uppercase">
            URLs dos commits:
          </label>
          <BaseTextarea
            id="input-commits-area"
            v-model="urlsTexto"
            data-tour="importar-textarea"
            class="leading-normal"
            rows="8"
            placeholder="Exemplo:&#10;https://gitlab.empresa.com/grupo/projeto/-/commit/a1b2c3d4e5f6...&#10;https://gitlab.empresa.com/outro/projeto/-/commit/f6e5d4c3b2a1..."
            :disabled="importando"
          />

          <div class="flex items-center justify-between pt-1">
            <BaseButton
              @click="limparTexto"
              :disabled="importando || !urlsTexto"
            >
              <i class="fa-solid fa-eraser" aria-hidden="true"></i>
              <span>Limpar Texto</span>
            </BaseButton>
            <span class="text-sm text-muted-foreground [&_strong]:text-primary">
              <strong>{{ parsedItems.length }}</strong> commit{{ parsedItems.length !== 1 ? 's' : '' }} identificado{{ parsedItems.length !== 1 ? 's' : '' }}
            </span>
          </div>
        </div>

        <!-- Painel Lateral de Pré-Visualização / Inspetor -->
        <div data-tour="importar-inspetor" class="flex flex-col gap-3 rounded-[10px] border border-border-strong bg-card px-5 py-4">
          <h3 class="flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-muted-foreground">
            <i class="fa-solid fa-magnifying-glass-chart" aria-hidden="true"></i>
            Pré-Visualização Inteligente
          </h3>

          <div v-if="parsedItems.length === 0" class="py-6 text-center text-sm italic text-muted-foreground">
            Cole as URLs dos commits no campo ao lado para visualizar a validação em tempo real.
          </div>

          <div v-else class="flex max-h-55 flex-col gap-2 overflow-y-auto">
            <div 
              v-for="(item, idx) in parsedItems" 
              :key="idx" 
              class="flex flex-col gap-1 rounded-md border bg-background px-3 py-2"
              :class="item.valido ? 'border-border-strong' : 'border-canvas-danger/40'"
            >
              <div class="flex items-center gap-2">
                <span v-if="item.valido" class="rounded-sm bg-sky-400/10 px-1 py-px font-mono text-xs font-bold text-primary">{{ item.sha.slice(0, 8) }}</span>
                <span v-else class="text-xs font-extrabold text-canvas-danger">Formato Inválido</span>
                <span class="truncate text-sm font-semibold text-foreground" :title="item.projeto">{{ item.projeto || 'Projeto desconhecido' }}</span>
              </div>
              <div>
                <span class="text-xs text-muted-foreground" :title="item.dominio">{{ item.dominio || 'Domínio não detectado' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- SEÇÃO 3: EXECUÇÃO E FEEDBACK DA IMPORTAÇÃO -->
    <section data-tour="importar-acao-secao" class="mb-9">
      <div data-tour="importar-acao" class="flex flex-wrap items-center justify-between gap-5 rounded-xl border border-border-strong bg-card px-7 py-5 shadow-lg shadow-black/20">
        <div class="flex flex-col gap-1">
          <span class="text-base text-foreground [&_strong]:text-primary">
            Pronto para importar <strong>{{ parsedItemsValidos.length }}</strong> commit{{ parsedItemsValidos.length !== 1 ? 's' : '' }}
          </span>
          <span class="text-sm text-muted-foreground [&_strong]:text-foreground">
            Instância Git: <strong>{{ nomeContaSelecionada }}</strong>
          </span>
        </div>

        <BaseButton
          variant="primary"
          :disabled="importando || parsedItemsValidos.length === 0"
          @click="executarImportacao"
        >
          <span v-if="importando" class="inline-block size-3.5 animate-spin rounded-full border-2 border-transparent border-t-current border-r-current"></span>
          <span>{{ importando ? `Importando (${progressoAtual}/${parsedItemsValidos.length})...` : `Importar ${parsedItemsValidos.length} Commit(s)` }}</span>
        </BaseButton>
      </div>

      <!-- Barra de Progresso durante a Importação -->
      <div v-if="importando || relatorioExecucao.length > 0" class="mt-6 flex flex-col gap-4 rounded-xl border border-border-strong bg-card p-5">
        <div 
          class="h-2 w-full overflow-hidden rounded-sm bg-white/8" 
          role="progressbar" 
          :aria-valuenow="progressoAtual" 
          aria-valuemin="0" 
          :aria-valuemax="parsedItemsValidos.length"
          aria-label="Progresso da importação dos commits"
        >
          <div 
            class="h-full bg-linear-to-r from-canvas-accent to-progress-end transition-[width] duration-300 ease-out"
            :style="{ width: percentualProgresso + '%' }"
          ></div>
        </div>

        <!-- Relatório Detalhado de Resultados -->
        <div class="flex flex-col gap-4" role="region" aria-label="Resultados da importação">
          <div class="flex flex-wrap items-center gap-5 border-b border-border-strong pb-2 text-sm font-bold">
            <span class="text-canvas-success">
              <i class="fa-solid fa-circle-check mr-1" aria-hidden="true"></i>
              <span>{{ totalSucessos }} importado(s)</span>
            </span>
            <span class="text-canvas-link">
              <i class="fa-solid fa-circle-info mr-1" aria-hidden="true"></i>
              <span>{{ totalJaExistiam }} já existia(m)</span>
            </span>
            <span v-if="totalFalhas > 0" class="text-canvas-danger">
              <i class="fa-solid fa-circle-xmark mr-1" aria-hidden="true"></i>
              <span>{{ totalFalhas }} falha(s)</span>
            </span>
          </div>

          <div class="flex max-h-62.5 flex-col gap-1.5 overflow-y-auto">
            <div 
              v-for="(res, idx) in relatorioExecucao" 
              :key="idx" 
              class="flex items-center gap-3 rounded-md border border-border-strong bg-background px-3 py-2 text-sm"
            >
              <div class="shrink-0">
                <span v-if="res.status === 'sucesso'" :class="classesBadgeResultado.sucesso">NOVO</span>
                <span v-else-if="res.status === 'existente'" :class="classesBadgeResultado.existente">EXISTENTE</span>
                <span v-else :class="classesBadgeResultado.erro">ERRO</span>
              </div>
              <div class="flex min-w-0 flex-1 items-center gap-2.5">
                <span class="font-mono font-bold text-muted-foreground">{{ res.sha ? res.sha.slice(0, 8) : 'Commit' }}</span>
                <span class="truncate text-foreground">{{ res.mensagem }}</span>
              </div>
            </div>
          </div>

          <!-- Ações Pós-Importação -->
          <div v-if="!importando && relatorioExecucao.length > 0" class="flex flex-wrap items-center gap-4 border-t border-border-strong pt-3">
            <BaseButton variant="primary" @click="$router.push('/analisar')">
              <i class="fa-solid fa-bolt" aria-hidden="true"></i>
              <span>Prosseguir para Análise com IA</span>
              <i class="fa-solid fa-arrow-right" aria-hidden="true"></i>
            </BaseButton>
            <BaseButton @click="$router.push('/commits')">
              Ver Todos os Commits
            </BaseButton>
          </div>
        </div>
      </div>
    </section>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api, type GitAccount } from '../api'
import { useToastStore } from '../stores/toast'
import TutorialModal from '../components/TutorialModal.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import BaseTextarea from '../components/ui/BaseTextarea.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import PageTitle from '../components/ui/PageTitle.vue'

const toastStore = useToastStore()

const contas = ref<GitAccount[]>([])
const loadingContas = ref(true)
const selectedAccountId = ref<number>(0) // 0 = Auto-detectar

const urlsTexto = ref('')
const importando = ref(false)
const progressoAtual = ref(0)
const erroGlobal = ref('')

interface ResultadoItem {
  url: string
  sha: string
  status: 'sucesso' | 'existente' | 'erro'
  mensagem: string
}

const relatorioExecucao = ref<ResultadoItem[]>([])

const classesLinkGhost = 'inline-flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-border-strong bg-card px-5 py-2.5 text-[0.88rem] leading-none font-semibold tracking-[0.01em] text-foreground transition-all duration-200 hover:-translate-y-px hover:border-primary hover:text-primary'
const classesLinkPrimary = 'inline-flex cursor-pointer items-center justify-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-[0.88rem] leading-none font-semibold tracking-[0.01em] text-white shadow-[0_4px_12px] shadow-primary-glow transition-all duration-200 hover:-translate-y-px hover:brightness-110 active:translate-y-0'
const classesTituloSecao = 'mb-5 flex items-start gap-3.5'
const classesBadgePasso = 'mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-black text-white shadow-[0_2px_8px] shadow-canvas-accent/30'
const classesH2Secao = 'text-lg font-extrabold text-foreground'
const classesNomeConta = 'truncate text-base font-extrabold text-foreground'
const classesUrlConta = 'max-w-65 truncate text-xs text-muted-foreground'

const classesCartaoConta = (selecionado: boolean) =>
  selecionado
    ? 'flex cursor-pointer items-center justify-between gap-3 rounded-[10px] border-2 border-primary bg-primary-glow p-4.5 -translate-y-0.5 shadow-lg shadow-canvas-accent/25 outline-none transition-all duration-150 ease-in-out hover:border-primary focus-visible:outline-2 focus-visible:outline-solid focus-visible:outline-primary focus-visible:outline-offset-2'
    : 'flex cursor-pointer items-center justify-between gap-3 rounded-[10px] border-2 border-border-strong bg-card p-4.5 shadow-md shadow-black/15 outline-none transition-all duration-150 ease-in-out hover:-translate-y-0.5 hover:border-primary focus-visible:outline-2 focus-visible:outline-solid focus-visible:outline-primary focus-visible:outline-offset-2'

const classesRadioPilula = (selecionado: boolean) =>
  selecionado
    ? 'flex size-4.5 shrink-0 items-center justify-center rounded-full border-2 border-primary'
    : 'flex size-4.5 shrink-0 items-center justify-center rounded-full border-2 border-border-strong'

const classesBadgeResultado: Record<ResultadoItem['status'], string> = {
  sucesso: 'rounded-sm border border-badge-green-border bg-badge-green px-1.5 py-0.5 text-[0.68rem] font-extrabold text-badge-green-foreground',
  existente: 'rounded-sm border border-badge-code-border bg-badge-code px-1.5 py-0.5 text-[0.68rem] font-extrabold text-badge-code-foreground',
  erro: 'rounded-sm border border-canvas-danger/40 bg-canvas-danger/20 px-1.5 py-0.5 text-[0.68rem] font-extrabold text-error-soft',
}

onMounted(async () => {
  await carregarContas()
})

async function carregarContas() {
  loadingContas.value = true
  try {
    const list = await api.gitAccounts.listar()
    contas.value = list
    // Pré-seleciona a conta padrão ou a auto-detecção
    const padrao = list.find(c => c.padrao)
    if (padrao) {
      selectedAccountId.value = padrao.id
    } else if (list.length > 0) {
      selectedAccountId.value = list[0].id
    } else {
      selectedAccountId.value = 0
    }
  } catch (e: any) {
    erroGlobal.value = `Erro ao carregar contas GitLab: ${e.response?.data?.detail ?? String(e)}`
  } finally {
    loadingContas.value = false
  }
}

interface ParsedCommit {
  raw: string
  valido: boolean
  dominio: string
  projeto: string
  sha: string
}

// Analisa em tempo real o texto digitado
const parsedItems = computed<ParsedCommit[]>(() => {
  const linhas = urlsTexto.value
    .split('\n')
    .map(l => l.trim())
    .filter(l => l.length > 0)

  return linhas.map(linha => {
    const match = linha.match(/(https?:\/\/[^/]+)\/(.+?)\/(?:-\/)?commit\/([0-9a-fA-F]{6,64})/)
    if (match) {
      return {
        raw: linha,
        valido: true,
        dominio: match[1],
        projeto: match[2],
        sha: match[3],
      }
    }

    // Se veio apenas um hash ou URL curta
    const shaMatch = linha.match(/([0-9a-fA-F]{40})/)
    if (shaMatch) {
      return {
        raw: linha,
        valido: true,
        dominio: '',
        projeto: '',
        sha: shaMatch[1],
      }
    }

    return {
      raw: linha,
      valido: false,
      dominio: '',
      projeto: '',
      sha: '',
    }
  })
})

const parsedItemsValidos = computed(() => {
  return parsedItems.value.filter(i => i.valido)
})

const nomeContaSelecionada = computed(() => {
  if (selectedAccountId.value === 0) return 'Detecção Automática (Smart Match)'
  const conta = contas.value.find(c => c.id === selectedAccountId.value)
  return conta ? `${conta.nome} (${conta.url})` : 'Padrão'
})

const percentualProgresso = computed(() => {
  if (parsedItemsValidos.value.length === 0) return 0
  return Math.round((progressoAtual.value / parsedItemsValidos.value.length) * 100)
})

const totalSucessos = computed(() => relatorioExecucao.value.filter(r => r.status === 'sucesso').length)
const totalJaExistiam = computed(() => relatorioExecucao.value.filter(r => r.status === 'existente').length)
const totalFalhas = computed(() => relatorioExecucao.value.filter(r => r.status === 'erro').length)

function limparTexto() {
  urlsTexto.value = ''
  relatorioExecucao.value = []
  progressoAtual.value = 0
}

async function executarImportacao() {
  if (parsedItemsValidos.value.length === 0) return

  importando.value = true
  erroGlobal.value = ''
  relatorioExecucao.value = []
  progressoAtual.value = 0

  for (const item of parsedItemsValidos.value) {
    try {
      const payload: any = {
        commit_hash: item.raw,
      }
      
      // Se não for detecção automática, envia o account_id explícito
      if (selectedAccountId.value !== 0) {
        payload.git_account_id = selectedAccountId.value
      }

      const res = await api.commits.importar(payload)

      if (res.ja_existia) {
        relatorioExecucao.value.push({
          url: item.raw,
          sha: res.id || item.sha,
          status: 'existente',
          mensagem: `Commit ${item.sha ? item.sha.slice(0, 8) : ''} já havia sido importado previamente.`,
        })
      } else {
        relatorioExecucao.value.push({
          url: item.raw,
          sha: res.id || item.sha,
          status: 'sucesso',
          mensagem: `Commit ${item.sha ? item.sha.slice(0, 8) : ''} importado com sucesso!`,
        })
      }
    } catch (e: any) {
      const detail = e.response?.data?.detail ?? e.message ?? String(e)
      relatorioExecucao.value.push({
        url: item.raw,
        sha: item.sha,
        status: 'erro',
        mensagem: `Falha na importação: ${detail}`,
      })
    } finally {
      progressoAtual.value++
    }
  }

  importando.value = false

  if (totalFalhas.value > 0) {
    toastStore.addToast(`Importação finalizada com ${totalFalhas.value} erro(s).`, 'error')
  } else {
    toastStore.addToast(`Importação concluída com sucesso! (${totalSucessos.value} novos)`, 'success')
  }
}
</script>
